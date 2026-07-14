"""Endpoints de inventario y operaciones explicitas sobre documentos externos."""

from __future__ import annotations

from http import HTTPStatus
from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from pliegocheck_api.auth import CurrentUser, audit_event
from pliegocheck_api.config import Settings, get_settings
from pliegocheck_api.db import get_session
from pliegocheck_api.errors import DomainError
from pliegocheck_api.external_documents.service import enqueue_download, enqueue_sync
from pliegocheck_api.models import ExternalProcessChangeEvent as ChangeEventModel
from pliegocheck_api.models import ExternalProcessDocument as DocumentModel
from pliegocheck_api.models import ExternalProcessDocumentVersion as VersionModel
from pliegocheck_api.models import ExternalProcessSyncRun as SyncRunModel
from pliegocheck_api.models import ExternalProcurementProcessLink, Process, ProcessDocument
from pliegocheck_api.routes.processes import enqueue_document_extraction
from pliegocheck_schemas import (
    ExternalDocumentAddendumStatus,
    ExternalDocumentDiscoveryStatus,
    ExternalDocumentDownloadRequest,
    ExternalDocumentDownloadResponse,
    ExternalDocumentDownloadStatus,
    ExternalDocumentErrorCode,
    ExternalDocumentExtractResponse,
    ExternalProcessChangeEvent,
    ExternalProcessChangeEventType,
    ExternalProcessDocumentDetail,
    ExternalProcessDocumentList,
    ExternalProcessDocumentSummary,
    ExternalProcessDocumentVersion,
    ExternalProcessSyncQueueResponse,
    ExternalProcessSyncReadiness,
    ExternalProcessSyncRequest,
    ExternalProcessSyncRunDetail,
    ExternalProcessSyncRunList,
    ExternalProcessSyncRunSummary,
    ExternalProcessSyncStatus,
    OperationalAuditEventType,
)

router = APIRouter(prefix="/processes", tags=["external-documents"])
SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def _actor(request: Request) -> CurrentUser | None:
    value = getattr(request.state, "current_user", None)
    return cast(CurrentUser, value) if value is not None else None


@router.get("/{process_id}/external-sync/readiness", response_model=ExternalProcessSyncReadiness)
def readiness(
    process_id: UUID, session: SessionDep, settings: SettingsDep
) -> ExternalProcessSyncReadiness:
    link = session.scalar(
        select(ExternalProcurementProcessLink).where(
            ExternalProcurementProcessLink.process_id == process_id
        )
    )
    active = session.scalar(
        select(SyncRunModel).where(
            SyncRunModel.process_id == process_id,
            SyncRunModel.status.in_(["PENDING", "PROCESSING"]),
        )
    )
    last = session.scalar(
        select(SyncRunModel)
        .where(SyncRunModel.process_id == process_id)
        .order_by(SyncRunModel.created_at.desc())
        .limit(1)
    )
    available = bool(
        link and settings.secop_document_sync_enabled and settings.secop_incremental_sync_enabled
    )
    reason = (
        None
        if available
        else (
            "El proceso no tiene enlace SECOP."
            if not link
            else "La sincronizacion documental esta deshabilitada."
        )
    )
    return ExternalProcessSyncReadiness(
        process_id=process_id,
        available=available,
        enabled=settings.secop_document_sync_enabled,
        source_system=link.source_system if link else None,
        external_process_link_id=link.id if link else None,
        active_sync_run_id=active.id if active else None,
        last_sync_at=last.finished_at if last else None,
        reason=reason,
    )


@router.post(
    "/{process_id}/external-sync",
    response_model=ExternalProcessSyncQueueResponse,
    status_code=HTTPStatus.ACCEPTED,
)
def queue_sync(
    process_id: UUID,
    payload: ExternalProcessSyncRequest,
    request: Request,
    session: SessionDep,
    settings: SettingsDep,
) -> ExternalProcessSyncQueueResponse:
    actor = _actor(request)
    run = enqueue_sync(
        session,
        settings,
        process_id,
        discover_documents=payload.discover_documents,
        created_by=actor.id if actor else None,
    )
    audit_event(
        session,
        event_type=OperationalAuditEventType.EXTERNAL_SYNC_QUEUED,
        action="external.sync",
        status=run.status,
        actor=actor,
        request=request,
        entity_type="process",
        entity_id=process_id,
        metadata={"sync_run_id": str(run.id)},
    )
    session.commit()
    return ExternalProcessSyncQueueResponse(
        process_id=process_id,
        sync_run_id=run.id,
        status=ExternalProcessSyncStatus(run.status),
        message="La sincronizacion externa quedo en cola.",
    )


@router.get("/{process_id}/external-sync-runs", response_model=ExternalProcessSyncRunList)
@router.get("/{process_id}/external-sync", response_model=ExternalProcessSyncRunList)
def list_syncs(
    process_id: UUID, session: SessionDep, limit: Annotated[int, Query(ge=1, le=100)] = 20
) -> ExternalProcessSyncRunList:
    rows = session.scalars(
        select(SyncRunModel)
        .where(SyncRunModel.process_id == process_id)
        .order_by(SyncRunModel.created_at.desc())
        .limit(limit)
    ).all()
    return ExternalProcessSyncRunList(
        process_id=process_id,
        items=[_sync_summary(row) for row in rows],
        total=session.scalar(
            select(func.count())
            .select_from(SyncRunModel)
            .where(SyncRunModel.process_id == process_id)
        )
        or 0,
    )


@router.get(
    "/{process_id}/external-sync-runs/{run_id}", response_model=ExternalProcessSyncRunDetail
)
@router.get("/{process_id}/external-sync/{run_id}", response_model=ExternalProcessSyncRunDetail)
def get_sync(process_id: UUID, run_id: UUID, session: SessionDep) -> ExternalProcessSyncRunDetail:
    run = session.get(SyncRunModel, run_id)
    if not run or run.process_id != process_id:
        raise DomainError(
            ExternalDocumentErrorCode.EXTERNAL_SYNC_NOT_FOUND,
            "La sincronizacion no existe.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    events = session.scalars(
        select(ChangeEventModel)
        .where(ChangeEventModel.sync_run_id == run.id)
        .order_by(ChangeEventModel.created_at)
    ).all()
    return ExternalProcessSyncRunDetail(
        **_sync_summary(run).model_dump(),
        input_digest=run.input_digest,
        events=[_event(item) for item in events],
    )


@router.get("/{process_id}/external-documents", response_model=ExternalProcessDocumentList)
def list_documents(process_id: UUID, session: SessionDep) -> ExternalProcessDocumentList:
    rows = session.scalars(
        select(DocumentModel)
        .where(DocumentModel.process_id == process_id)
        .order_by(DocumentModel.last_seen_at.desc())
    ).all()
    return ExternalProcessDocumentList(
        process_id=process_id, items=[_document(row) for row in rows], total=len(rows)
    )


@router.get(
    "/{process_id}/external-documents/{document_id}", response_model=ExternalProcessDocumentDetail
)
def get_document(
    process_id: UUID, document_id: UUID, session: SessionDep
) -> ExternalProcessDocumentDetail:
    document = _get_document(session, process_id, document_id)
    versions = session.scalars(
        select(VersionModel)
        .where(VersionModel.external_document_id == document.id)
        .order_by(VersionModel.version_number.desc())
    ).all()
    return ExternalProcessDocumentDetail(
        **_document(document).model_dump(), versions=[_version(item) for item in versions]
    )


@router.get(
    "/{process_id}/external-documents/{document_id}/versions",
    response_model=list[ExternalProcessDocumentVersion],
)
def list_document_versions(
    process_id: UUID, document_id: UUID, session: SessionDep
) -> list[ExternalProcessDocumentVersion]:
    document = _get_document(session, process_id, document_id)
    rows = session.scalars(
        select(VersionModel)
        .where(VersionModel.external_document_id == document.id)
        .order_by(VersionModel.version_number.desc())
    ).all()
    return [_version(row) for row in rows]


@router.post(
    "/{process_id}/external-documents/{document_id}/download",
    response_model=ExternalDocumentDownloadResponse,
    status_code=HTTPStatus.ACCEPTED,
)
def queue_download(
    process_id: UUID,
    document_id: UUID,
    payload: ExternalDocumentDownloadRequest,
    request: Request,
    session: SessionDep,
    settings: SettingsDep,
) -> ExternalDocumentDownloadResponse:
    if not payload.confirm_public_download:
        raise DomainError(
            ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_DOWNLOAD_UNSUPPORTED,
            "Debe confirmar expresamente la descarga publica.",
        )
    actor = _actor(request)
    job = enqueue_download(
        session, settings, process_id, document_id, created_by=actor.id if actor else None
    )
    audit_event(
        session,
        event_type=OperationalAuditEventType.EXTERNAL_DOCUMENT_DOWNLOAD_QUEUED,
        action="external.document.download",
        status=job.status,
        actor=actor,
        request=request,
        entity_type="external_document",
        entity_id=document_id,
        metadata={"download_job_id": str(job.id)},
    )
    session.commit()
    return ExternalDocumentDownloadResponse(
        process_id=process_id,
        external_document_id=document_id,
        status=ExternalDocumentDownloadStatus(job.status),
        version_id=None,
        process_document_id=None,
        sha256=None,
        message=(
            "La descarga publica controlada quedo en cola; "
            "la extraccion no se inicia automaticamente."
        ),
    )


@router.post(
    "/{process_id}/external-documents/{document_id}/extract",
    response_model=ExternalDocumentExtractResponse,
    status_code=HTTPStatus.ACCEPTED,
)
def extract_document(
    process_id: UUID,
    document_id: UUID,
    request: Request,
    session: SessionDep,
    settings: SettingsDep,
) -> ExternalDocumentExtractResponse:
    external = _get_document(session, process_id, document_id)
    version = (
        session.get(VersionModel, external.current_version_id)
        if external.current_version_id
        else None
    )
    process = session.get(Process, process_id)
    stored = session.get(ProcessDocument, version.process_document_id) if version else None
    if not process or not stored:
        raise DomainError(
            ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_EXTRACTION_NOT_READY,
            "El documento debe descargarse y validarse antes de extraerlo.",
            status_code=HTTPStatus.CONFLICT,
        )
    result = enqueue_document_extraction(
        session=session,
        process=process,
        document=stored,
        force=False,
        max_attempts=settings.worker_max_attempts,
    )
    audit_event(
        session,
        event_type=OperationalAuditEventType.EXTERNAL_DOCUMENT_EXTRACTION_QUEUED,
        action="external.document.extract",
        status="QUEUED" if result.job_id else "UNCHANGED",
        actor=_actor(request),
        request=request,
        entity_type="external_document",
        entity_id=document_id,
        metadata={"process_document_id": str(stored.id)},
    )
    session.commit()
    return ExternalDocumentExtractResponse(
        process_id=process_id,
        external_document_id=document_id,
        process_document_id=stored.id,
        extraction_job_id=result.job_id,
        message="La extraccion explicita quedo en cola; no se tomo ninguna decision automatica.",
    )


def _get_document(session: Session, process_id: UUID, document_id: UUID) -> DocumentModel:
    document = session.get(DocumentModel, document_id)
    if not document or document.process_id != process_id:
        raise DomainError(
            ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_NOT_FOUND,
            "El documento externo no existe.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return document


def _sync_summary(row: SyncRunModel) -> ExternalProcessSyncRunSummary:
    return ExternalProcessSyncRunSummary(
        id=row.id,
        process_id=row.process_id,
        external_process_link_id=row.external_process_link_id,
        source_system=row.source_system,
        status=ExternalProcessSyncStatus(row.status),
        started_at=row.started_at,
        finished_at=row.finished_at,
        source_updated_at=row.source_updated_at,
        metadata_changed=row.metadata_changed,
        documents_discovered=row.documents_discovered,
        documents_added=row.documents_added,
        documents_updated=row.documents_updated,
        documents_unchanged=row.documents_unchanged,
        documents_failed=row.documents_failed,
        warnings=row.warnings,
        error_code=ExternalDocumentErrorCode(row.error_code) if row.error_code else None,
        error_message=row.error_message,
        created_at=row.created_at,
    )


def _event(row: ChangeEventModel) -> ExternalProcessChangeEvent:
    return ExternalProcessChangeEvent(
        id=row.id,
        process_id=row.process_id,
        sync_run_id=row.sync_run_id,
        event_type=ExternalProcessChangeEventType(row.event_type),
        external_document_id=row.external_document_id,
        old_value=row.old_value,
        new_value=row.new_value,
        metadata=row.event_metadata,
        created_at=row.created_at,
    )


def _document(row: DocumentModel) -> ExternalProcessDocumentSummary:
    return ExternalProcessDocumentSummary(
        id=row.id,
        process_id=row.process_id,
        source_system=row.source_system,
        source_document_id=row.source_document_id,
        source_document_reference=row.source_document_reference,
        title=row.title,
        document_type=row.document_type,
        document_category=row.document_category,
        source_url=row.source_url,
        source_public_url=row.source_public_url,
        published_at=row.published_at,
        updated_at_source=row.updated_at_source,
        reported_size_bytes=row.reported_size_bytes,
        reported_content_type=row.reported_content_type,
        discovery_status=ExternalDocumentDiscoveryStatus(row.discovery_status),
        download_status=ExternalDocumentDownloadStatus(row.download_status),
        addendum_status=ExternalDocumentAddendumStatus(row.addendum_status),
        requires_human_review=row.requires_human_review,
        current_version_id=row.current_version_id,
        version_count=row.version_count,
        first_seen_at=row.first_seen_at,
        last_seen_at=row.last_seen_at,
    )


def _version(row: VersionModel) -> ExternalProcessDocumentVersion:
    return ExternalProcessDocumentVersion(
        id=row.id,
        external_document_id=row.external_document_id,
        version_number=row.version_number,
        source_url=row.source_url,
        source_updated_at=row.source_updated_at,
        reported_size_bytes=row.reported_size_bytes,
        reported_content_type=row.reported_content_type,
        sha256=row.sha256,
        size_bytes=row.size_bytes,
        detected_content_type=row.detected_content_type,
        downloaded_at=row.downloaded_at,
        process_document_id=row.process_document_id,
        previous_version_id=row.previous_version_id,
        created_at=row.created_at,
    )
