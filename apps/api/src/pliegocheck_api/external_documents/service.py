"""Casos de uso transaccionales de sincronizacion, versionado y descarga."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from http import HTTPStatus
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from pliegocheck_api.config import Settings
from pliegocheck_api.errors import DomainError
from pliegocheck_api.external_documents.download import (
    DocumentDownloader,
    ExternalDownloadError,
    SafeDocumentDownloader,
)
from pliegocheck_api.external_documents.providers import (
    ExternalProcessDocumentProvider,
    ProcessRefresh,
    provider_for_link,
)
from pliegocheck_api.external_documents.security import ExternalDocumentSecurityError
from pliegocheck_api.models import (
    ExternalDocumentDownloadJob,
    ExternalProcessChangeEvent,
    ExternalProcessDocument,
    ExternalProcessDocumentVersion,
    ExternalProcessSnapshot,
    ExternalProcessSyncRun,
    ExternalProcurementProcessLink,
    Process,
    ProcessDocument,
)
from pliegocheck_api.storage import LocalDocumentStorage, StorageError
from pliegocheck_schemas import (
    DocumentProcessingStatus,
    DocumentType,
    DocumentUploadStatus,
    ExternalDocumentAddendumStatus,
    ExternalDocumentDiscoveryStatus,
    ExternalDocumentDownloadStatus,
    ExternalDocumentErrorCode,
    ExternalProcessChangeEventType,
    ExternalProcessSyncStatus,
)


def enqueue_sync(
    session: Session,
    settings: Settings,
    process_id: UUID,
    *,
    discover_documents: bool,
    created_by: UUID | None = None,
) -> ExternalProcessSyncRun:
    if not settings.secop_document_sync_enabled or not settings.secop_incremental_sync_enabled:
        raise DomainError(
            ExternalDocumentErrorCode.EXTERNAL_SYNC_NOT_AVAILABLE,
            "La sincronizacion documental externa no esta habilitada.",
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
        )
    link = session.scalar(
        select(ExternalProcurementProcessLink).where(
            ExternalProcurementProcessLink.process_id == process_id
        )
    )
    if link is None:
        raise DomainError(
            ExternalDocumentErrorCode.EXTERNAL_PROCESS_LINK_NOT_FOUND,
            "El proceso no tiene un enlace SECOP verificable.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    active = session.scalar(
        select(ExternalProcessSyncRun).where(
            ExternalProcessSyncRun.process_id == process_id,
            ExternalProcessSyncRun.status.in_(
                [
                    ExternalProcessSyncStatus.PENDING.value,
                    ExternalProcessSyncStatus.PROCESSING.value,
                ]
            ),
        )
    )
    if active:
        return active
    digest = hashlib.sha256(f"{process_id}:{link.id}:{discover_documents}".encode()).hexdigest()
    run = ExternalProcessSyncRun(
        id=uuid4(),
        process_id=process_id,
        external_process_link_id=link.id,
        source_system=link.source_system,
        status=ExternalProcessSyncStatus.PENDING.value,
        input_digest=digest,
        discover_documents=discover_documents,
        max_attempts=settings.worker_max_attempts,
        created_by=created_by,
    )
    session.add(run)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        existing = session.scalar(
            select(ExternalProcessSyncRun).where(
                ExternalProcessSyncRun.process_id == process_id,
                ExternalProcessSyncRun.status.in_(
                    [
                        ExternalProcessSyncStatus.PENDING.value,
                        ExternalProcessSyncStatus.PROCESSING.value,
                    ]
                ),
            )
        )
        if existing:
            return existing
        raise
    session.refresh(run)
    return run


def claim_sync(session: Session, worker_id: str) -> ExternalProcessSyncRun | None:
    now = datetime.now(UTC)
    run = session.scalar(
        select(ExternalProcessSyncRun)
        .where(
            ExternalProcessSyncRun.status == ExternalProcessSyncStatus.PENDING.value,
            ExternalProcessSyncRun.available_at <= now,
        )
        .order_by(ExternalProcessSyncRun.created_at)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if run:
        run.status = ExternalProcessSyncStatus.PROCESSING.value
        run.started_at = now
        run.locked_at = now
        run.locked_by = worker_id
        run.attempt_count += 1
        session.commit()
        session.refresh(run)
    return run


def execute_sync(
    session: Session,
    settings: Settings,
    run_id: UUID,
    *,
    provider: ExternalProcessDocumentProvider | None = None,
) -> ExternalProcessSyncRun:
    run = session.get(ExternalProcessSyncRun, run_id)
    if run is None:
        raise DomainError(
            ExternalDocumentErrorCode.EXTERNAL_SYNC_NOT_FOUND,
            "La sincronizacion no existe.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    link = session.get(ExternalProcurementProcessLink, run.external_process_link_id)
    if link is None:
        return _fail_sync(
            session,
            run,
            ExternalDocumentErrorCode.EXTERNAL_PROCESS_LINK_NOT_FOUND,
            "El enlace SECOP ya no existe.",
        )
    own_provider = provider is None
    provider = provider or provider_for_link(settings, link)
    try:
        refresh = provider.refresh(
            link,
            settings.secop_document_max_files_per_sync if run.discover_documents else 0,
        )
        _persist_refresh(session, run, link, refresh)
    except Exception:
        session.rollback()
        run = session.get(ExternalProcessSyncRun, run_id)
        assert run is not None
        _fail_sync(
            session,
            run,
            ExternalDocumentErrorCode.EXTERNAL_SOURCE_UNAVAILABLE,
            "La fuente publica no pudo sincronizarse.",
        )
    finally:
        if own_provider:
            provider.close()
    session.refresh(run)
    return run


def _persist_refresh(
    session: Session,
    run: ExternalProcessSyncRun,
    link: ExternalProcurementProcessLink,
    refresh: ProcessRefresh,
) -> None:
    now = datetime.now(UTC)
    normalized = dict(refresh.metadata)
    encoded = json.dumps(normalized, sort_keys=True, ensure_ascii=False, default=str).encode()
    metadata_hash = str(normalized.get("raw_payload_hash") or hashlib.sha256(encoded).hexdigest())
    previous = session.scalar(
        select(ExternalProcessSnapshot)
        .where(ExternalProcessSnapshot.process_id == run.process_id)
        .order_by(ExternalProcessSnapshot.captured_at.desc())
        .limit(1)
    )
    session.add(
        ExternalProcessSnapshot(
            id=uuid4(),
            process_id=run.process_id,
            sync_run_id=run.id,
            source_system=run.source_system,
            source_process_id=link.source_process_id,
            source_reference=_text(normalized.get("reference")),
            source_status=_text(normalized.get("status")),
            source_publication_date=_datetime_value(normalized.get("publication_date")),
            source_closing_date=_datetime_value(normalized.get("closing_date")),
            source_estimated_value=_decimal_value(normalized.get("estimated_value")),
            source_currency=_text(normalized.get("currency")),
            normalized_payload=normalized,
            raw_payload_hash=metadata_hash,
            source_updated_at=refresh.source_updated_at,
        )
    )
    run.metadata_changed = previous is None or previous.raw_payload_hash != metadata_hash
    warnings = list(refresh.warnings)
    if previous:
        for event_type, old, new in detect_process_changes(previous.normalized_payload, normalized):
            _event(session, run, event_type, old, new)
        for field in (
            "status",
            "publication_date",
            "closing_date",
            "estimated_value",
            "currency",
            "entity_name",
            "title",
            "description",
        ):
            if previous.normalized_payload.get(field) is not None and normalized.get(field) is None:
                warnings.append(
                    {
                        "code": "SOURCE_FIELD_NOW_MISSING",
                        "message": f"La fuente dejo de informar {field}; se conserva el historico.",
                        "field": field,
                    }
                )
    _update_current_process(session, run.process_id, link, normalized, metadata_hash, now)
    seen: set[UUID] = set()
    for item in refresh.documents if run.discover_documents else ():
        document = session.scalar(
            select(ExternalProcessDocument).where(
                ExternalProcessDocument.process_id == run.process_id,
                ExternalProcessDocument.source_system == run.source_system,
                ExternalProcessDocument.source_document_id == item.source_document_id,
            )
        )
        if document is None:
            document = ExternalProcessDocument(
                id=uuid4(),
                process_id=run.process_id,
                external_process_link_id=link.id,
                source_system=run.source_system,
                source_document_id=item.source_document_id,
                source_document_reference=item.source_document_reference,
                title=item.title,
                document_type=item.document_type,
                document_category=item.document_category,
                source_url=item.source_url,
                source_public_url=item.source_public_url,
                published_at=item.published_at,
                updated_at_source=item.updated_at_source,
                reported_size_bytes=item.reported_size_bytes,
                reported_content_type=item.reported_content_type,
                discovery_status=item.discovery_status.value,
                download_status=item.download_status.value,
                addendum_status=item.addendum_status.value,
                requires_human_review=item.requires_human_review,
                first_seen_at=now,
                last_seen_at=now,
            )
            session.add(document)
            session.flush()
            run.documents_added += 1
            _event(
                session,
                run,
                ExternalProcessChangeEventType.DOCUMENT_DISCOVERED,
                None,
                item.title,
                document.id,
            )
            if item.addendum_status == ExternalDocumentAddendumStatus.POTENTIAL_ADDENDUM:
                _event(
                    session,
                    run,
                    ExternalProcessChangeEventType.POTENTIAL_ADDENDUM_DISCOVERED,
                    None,
                    item.title,
                    document.id,
                )
                warnings.append(
                    {
                        "code": "POTENTIAL_ADDENDUM_REQUIRES_REVIEW",
                        "message": (
                            "Una posible adenda requiere revision humana "
                            "y nueva normalizacion explicita."
                        ),
                    }
                )
            elif item.addendum_status == ExternalDocumentAddendumStatus.CONFIRMED_ADDENDUM:
                _event(
                    session,
                    run,
                    ExternalProcessChangeEventType.CONFIRMED_ADDENDUM_DISCOVERED,
                    None,
                    item.title,
                    document.id,
                )
        else:
            old_addendum_status = document.addendum_status
            old_signature = (
                document.source_document_reference,
                document.title,
                document.document_type,
                document.document_category,
                document.source_url,
                document.source_public_url,
                document.published_at,
                document.updated_at_source,
                document.reported_size_bytes,
                document.reported_content_type,
            )
            new_signature = (
                item.source_document_reference,
                item.title,
                item.document_type,
                item.document_category,
                item.source_url,
                item.source_public_url,
                item.published_at,
                item.updated_at_source,
                item.reported_size_bytes,
                item.reported_content_type,
            )
            (
                document.source_document_reference,
                document.title,
                document.document_type,
                document.document_category,
                document.source_url,
                document.source_public_url,
                document.published_at,
                document.updated_at_source,
                document.reported_size_bytes,
                document.reported_content_type,
            ) = new_signature
            document.discovery_status = item.discovery_status.value
            document.addendum_status = item.addendum_status.value
            document.requires_human_review = item.requires_human_review
            if document.download_status in {
                ExternalDocumentDownloadStatus.NOT_REQUESTED.value,
                ExternalDocumentDownloadStatus.UNSUPPORTED.value,
            }:
                document.download_status = item.download_status.value
            document.last_seen_at = now
            if old_signature != new_signature:
                run.documents_updated += 1
                _event(
                    session,
                    run,
                    ExternalProcessChangeEventType.DOCUMENT_UPDATED,
                    str(old_signature),
                    str(new_signature),
                    document.id,
                )
            else:
                run.documents_unchanged += 1
            if old_addendum_status != item.addendum_status.value and item.addendum_status in {
                ExternalDocumentAddendumStatus.POTENTIAL_ADDENDUM,
                ExternalDocumentAddendumStatus.CONFIRMED_ADDENDUM,
            }:
                event_type = (
                    ExternalProcessChangeEventType.CONFIRMED_ADDENDUM_DISCOVERED
                    if item.addendum_status == ExternalDocumentAddendumStatus.CONFIRMED_ADDENDUM
                    else ExternalProcessChangeEventType.POTENTIAL_ADDENDUM_DISCOVERED
                )
                _event(session, run, event_type, old_addendum_status, item.title, document.id)
                warnings.append(
                    {
                        "code": "ADDENDUM_REQUIRES_REVIEW",
                        "message": "La adenda detectada requiere revision humana explicita.",
                    }
                )
        seen.add(document.id)
    if run.discover_documents:
        missing_query = select(ExternalProcessDocument).where(
            ExternalProcessDocument.process_id == run.process_id
        )
        if seen:
            missing_query = missing_query.where(ExternalProcessDocument.id.not_in(seen))
        for missing in session.scalars(missing_query).all():
            if missing.discovery_status != ExternalDocumentDiscoveryStatus.MISSING.value:
                missing.discovery_status = ExternalDocumentDiscoveryStatus.MISSING.value
                _event(
                    session,
                    run,
                    ExternalProcessChangeEventType.DOCUMENT_REMOVED_FROM_SOURCE,
                    missing.title,
                    None,
                    missing.id,
                )
    run.documents_discovered = len(refresh.documents) if run.discover_documents else 0
    run.warnings = warnings
    run.source_updated_at = refresh.source_updated_at
    run.status = (
        ExternalProcessSyncStatus.COMPLETED_WITH_WARNINGS.value
        if warnings
        else ExternalProcessSyncStatus.COMPLETED.value
    )
    run.finished_at = now
    run.locked_at = None
    run.locked_by = None
    session.commit()


def _event(
    session: Session,
    run: ExternalProcessSyncRun,
    event_type: ExternalProcessChangeEventType,
    old: object,
    new: object,
    document_id: UUID | None = None,
) -> None:
    session.add(
        ExternalProcessChangeEvent(
            id=uuid4(),
            process_id=run.process_id,
            sync_run_id=run.id,
            event_type=event_type.value,
            external_document_id=document_id,
            old_value=None if old is None else str(old),
            new_value=None if new is None else str(new),
            event_metadata={},
        )
    )


def detect_process_changes(
    previous: dict[str, object], current: dict[str, object]
) -> list[tuple[ExternalProcessChangeEventType, object, object]]:
    """Compara solo campos verificables; no convierte ausencias en datos inventados."""

    fields = (
        ("status", ExternalProcessChangeEventType.PROCESS_STATUS_CHANGED),
        ("closing_date", ExternalProcessChangeEventType.CLOSING_DATE_CHANGED),
        ("estimated_value", ExternalProcessChangeEventType.ESTIMATED_VALUE_CHANGED),
    )
    return [
        (event_type, previous.get(field), current.get(field))
        for field, event_type in fields
        if previous.get(field) != current.get(field)
    ]


def _update_current_process(
    session: Session,
    process_id: UUID,
    link: ExternalProcurementProcessLink,
    metadata: dict[str, object],
    raw_hash: str,
    captured_at: datetime,
) -> None:
    process = session.get(Process, process_id)
    if process is None:
        return
    for source_field, target_field in {
        "title": "title",
        "entity_name": "contracting_entity",
        "description": "description",
        "modality": "selection_method",
        "currency": "currency",
        "source_url": "source_url",
        "reference": "secop_reference",
    }.items():
        value = _text(metadata.get(source_field))
        if value is not None:
            setattr(process, target_field, value)
    for source_field, target_field in (
        ("publication_date", "published_at"),
        ("closing_date", "closing_at"),
    ):
        date_value = _datetime_value(metadata.get(source_field))
        if date_value is not None:
            setattr(process, target_field, date_value)
    estimated_value = _decimal_value(metadata.get("estimated_value"))
    if estimated_value is not None:
        process.estimated_value = estimated_value
    link.external_metadata = {
        **link.external_metadata,
        "last_sync_at": captured_at.isoformat(),
        "raw_payload_hash": raw_hash,
    }


def _text(value: object) -> str | None:
    if value is None:
        return None
    result = str(value).strip()
    return result or None


def _datetime_value(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed
    except ValueError:
        return None


def _decimal_value(value: object) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _fail_sync(
    session: Session, run: ExternalProcessSyncRun, code: ExternalDocumentErrorCode, message: str
) -> ExternalProcessSyncRun:
    run.status = ExternalProcessSyncStatus.FAILED.value
    run.error_code = code.value
    run.error_message = message
    run.finished_at = datetime.now(UTC)
    run.locked_at = None
    run.locked_by = None
    session.commit()
    return run


def enqueue_download(
    session: Session,
    settings: Settings,
    process_id: UUID,
    external_document_id: UUID,
    *,
    created_by: UUID | None = None,
) -> ExternalDocumentDownloadJob:
    if not settings.secop_document_download_enabled:
        raise DomainError(
            ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_DOWNLOAD_UNSUPPORTED,
            "La descarga documental externa no esta habilitada.",
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
        )
    document = session.get(ExternalProcessDocument, external_document_id)
    if document is None or document.process_id != process_id:
        raise DomainError(
            ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_NOT_FOUND,
            "El documento externo no existe.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    if (
        not document.source_url
        or document.download_status == ExternalDocumentDownloadStatus.UNSUPPORTED.value
    ):
        raise DomainError(
            ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_DOWNLOAD_UNSUPPORTED,
            "La fuente no ofrece una descarga HTTPS compatible.",
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    existing = session.scalar(
        select(ExternalDocumentDownloadJob).where(
            ExternalDocumentDownloadJob.external_document_id == document.id,
            ExternalDocumentDownloadJob.status.in_(
                [
                    ExternalDocumentDownloadStatus.PENDING.value,
                    ExternalDocumentDownloadStatus.DOWNLOADING.value,
                ]
            ),
        )
    )
    if existing:
        return existing
    job = ExternalDocumentDownloadJob(
        id=uuid4(),
        external_document_id=document.id,
        status=ExternalDocumentDownloadStatus.PENDING.value,
        max_attempts=settings.worker_max_attempts,
        created_by=created_by,
    )
    document.download_status = ExternalDocumentDownloadStatus.PENDING.value
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def claim_download(session: Session, worker_id: str) -> ExternalDocumentDownloadJob | None:
    now = datetime.now(UTC)
    job = session.scalar(
        select(ExternalDocumentDownloadJob)
        .where(
            ExternalDocumentDownloadJob.status == ExternalDocumentDownloadStatus.PENDING.value,
            ExternalDocumentDownloadJob.available_at <= now,
        )
        .order_by(ExternalDocumentDownloadJob.created_at)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if job:
        job.status = ExternalDocumentDownloadStatus.DOWNLOADING.value
        job.locked_at = now
        job.locked_by = worker_id
        job.attempt_count += 1
        document = session.get(ExternalProcessDocument, job.external_document_id)
        if document:
            document.download_status = ExternalDocumentDownloadStatus.DOWNLOADING.value
        session.commit()
        session.refresh(job)
    return job


def execute_download(
    session: Session,
    settings: Settings,
    job_id: UUID,
    *,
    downloader: DocumentDownloader | None = None,
) -> ExternalDocumentDownloadJob:
    job = session.get(ExternalDocumentDownloadJob, job_id)
    if job is None:
        raise DomainError(
            ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_NOT_FOUND,
            "El trabajo de descarga no existe.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    document = session.get(ExternalProcessDocument, job.external_document_id)
    if document is None or not document.source_url:
        return _fail_download(
            session,
            job,
            document,
            ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_NOT_FOUND,
            "El documento externo ya no esta disponible.",
        )
    own = downloader is None
    downloader = downloader or SafeDocumentDownloader(settings)
    storage = LocalDocumentStorage(settings.storage_path)
    storage_key: str | None = None
    try:
        artifact = downloader.download(document.source_url, document.title)
        current = (
            session.get(ExternalProcessDocumentVersion, document.current_version_id)
            if document.current_version_id
            else None
        )
        if current and current.sha256 == artifact.sha256:
            artifact.path.unlink(missing_ok=True)
            job.status = ExternalDocumentDownloadStatus.UNCHANGED.value
            document.download_status = ExternalDocumentDownloadStatus.UNCHANGED.value
            job.finished_at = datetime.now(UTC)
            session.commit()
            return job
        process_document = session.scalar(
            select(ProcessDocument).where(
                ProcessDocument.process_id == document.process_id,
                ProcessDocument.sha256 == artifact.sha256,
            )
        )
        if process_document is None:
            process_document = ProcessDocument(
                id=uuid4(),
                process_id=document.process_id,
                original_filename=artifact.filename,
                stored_filename=f"{uuid4().hex}{artifact.extension}",
                storage_key="pending",
                declared_content_type=artifact.declared_content_type,
                detected_content_type=artifact.detected_content_type,
                extension=artifact.extension,
                size_bytes=artifact.size_bytes,
                sha256=artifact.sha256,
                document_type=DocumentType.UNKNOWN.value,
                upload_status=DocumentUploadStatus.STORED.value,
                processing_status=DocumentProcessingStatus.NOT_QUEUED.value,
            )
            storage_key = (
                f"processes/{document.process_id}/{process_document.id}{artifact.extension}"
            )
            process_document.storage_key = storage_key
            storage.save(artifact.path, storage_key)
            session.add(process_document)
            session.flush()
        else:
            artifact.path.unlink(missing_ok=True)
        version = ExternalProcessDocumentVersion(
            id=uuid4(),
            external_document_id=document.id,
            version_number=document.version_count + 1,
            source_url=artifact.final_url,
            source_updated_at=document.updated_at_source,
            reported_size_bytes=document.reported_size_bytes,
            reported_content_type=document.reported_content_type,
            sha256=artifact.sha256,
            size_bytes=artifact.size_bytes,
            detected_content_type=artifact.detected_content_type,
            storage_key=process_document.storage_key,
            downloaded_at=datetime.now(UTC),
            process_document_id=process_document.id,
            previous_version_id=document.current_version_id,
        )
        session.add(version)
        session.flush()
        document.current_version_id = version.id
        document.version_count += 1
        document.download_status = (
            ExternalDocumentDownloadStatus.UPDATED.value
            if current
            else ExternalDocumentDownloadStatus.DOWNLOADED.value
        )
        job.status = document.download_status
        job.finished_at = datetime.now(UTC)
        job.locked_at = None
        job.locked_by = None
        session.commit()
        return job
    except (ExternalDownloadError, ExternalDocumentSecurityError) as exc:
        session.rollback()
        job = session.get(ExternalDocumentDownloadJob, job_id)
        document = session.get(ExternalProcessDocument, job.external_document_id) if job else None
        assert job is not None
        return _fail_download(session, job, document, exc.code, exc.message)
    except (StorageError, SQLAlchemyError):
        session.rollback()
        if storage_key:
            storage.delete(storage_key)
        job = session.get(ExternalDocumentDownloadJob, job_id)
        assert job is not None
        return _fail_download(
            session,
            job,
            session.get(ExternalProcessDocument, job.external_document_id),
            ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_DOWNLOAD_FAILED,
            "No fue posible persistir el documento descargado.",
        )
    finally:
        if own:
            downloader.close()


def _fail_download(
    session: Session,
    job: ExternalDocumentDownloadJob,
    document: ExternalProcessDocument | None,
    code: ExternalDocumentErrorCode,
    message: str,
) -> ExternalDocumentDownloadJob:
    job.status = (
        ExternalDocumentDownloadStatus.REJECTED.value
        if code
        in {
            ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_URL_REJECTED,
            ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_HOST_REJECTED,
            ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_CONTENT_TYPE_REJECTED,
            ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_HTML_RESPONSE,
            ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_TOO_LARGE,
        }
        else ExternalDocumentDownloadStatus.FAILED.value
    )
    job.error_code = code.value
    job.error_message = message
    job.finished_at = datetime.now(UTC)
    job.locked_at = None
    job.locked_by = None
    if document:
        document.download_status = job.status
        sync_run = session.scalar(
            select(ExternalProcessSyncRun)
            .where(ExternalProcessSyncRun.process_id == document.process_id)
            .order_by(ExternalProcessSyncRun.created_at.desc())
            .limit(1)
        )
        if sync_run is not None:
            _event(
                session,
                sync_run,
                ExternalProcessChangeEventType.DOWNLOAD_FAILED,
                None,
                code.value,
                document.id,
            )
    session.commit()
    return job
