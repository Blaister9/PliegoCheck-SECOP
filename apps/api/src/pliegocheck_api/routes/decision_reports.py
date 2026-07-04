# mypy: ignore-errors
"""Endpoints de reporte ejecutivo y paquete de decision."""

from __future__ import annotations

from datetime import UTC, datetime
from http import HTTPStatus
from io import BytesIO
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from pliegocheck_api.db import get_session
from pliegocheck_api.errors import DomainError
from pliegocheck_api.models import (
    DecisionReportArtifact,
    DecisionReportJob,
    DecisionReportPackage,
    DecisionReportSection,
    DecisionRun,
    Process,
)
from pliegocheck_api.reports.manifest import stable_digest
from pliegocheck_api.reports.package import ReportArtifactStorage
from pliegocheck_api.reports.service import PACKAGE_VERSION, build_input_manifest
from pliegocheck_api.reports.templates import ReportTemplateError, load_report_templates
from pliegocheck_schemas import (
    DecisionReportArtifactMetadata,
    DecisionReportArtifactType,
    DecisionReportErrorCode,
    DecisionReportJobStatus,
    DecisionReportJobSummary,
    DecisionReportPackageDetail,
    DecisionReportPackageList,
    DecisionReportPackageStatus,
    DecisionReportPackageSummary,
    DecisionReportPreview,
    DecisionReportQueueResponse,
    DecisionReportRequest,
    DecisionReportSectionSummary,
    DecisionRunStatus,
)

router = APIRouter(prefix="/processes", tags=["decision-reports"])
SessionDep = Annotated[Session, Depends(get_session)]
LimitParam = Annotated[int, Query(ge=1, le=100)]
OffsetParam = Annotated[int, Query(ge=0)]


@router.post(
    "/{process_id}/decision-reports",
    response_model=DecisionReportQueueResponse,
    status_code=HTTPStatus.ACCEPTED,
)
def create_decision_report(
    process_id: UUID, payload: DecisionReportRequest, session: SessionDep
) -> DecisionReportQueueResponse:
    _process_or_404(session, process_id)
    run = _completed_decision_or_error(session, process_id, payload.decision_run_id)
    try:
        templates = load_report_templates()
    except ReportTemplateError as exc:
        raise DomainError(
            DecisionReportErrorCode.DECISION_REPORT_TEMPLATE_NOT_FOUND,
            "No se encontro el template de reporte.",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        ) from exc
    input_manifest = build_input_manifest(session, run, templates)
    input_digest = stable_digest(input_manifest)
    if not payload.force:
        existing = session.scalar(
            select(DecisionReportPackage)
            .where(
                DecisionReportPackage.decision_run_id == run.id,
                DecisionReportPackage.input_digest == input_digest,
                DecisionReportPackage.status.in_(
                    [
                        DecisionReportPackageStatus.COMPLETED.value,
                        DecisionReportPackageStatus.COMPLETED_WITH_WARNINGS.value,
                    ]
                ),
            )
            .order_by(DecisionReportPackage.created_at.desc())
            .limit(1)
        )
        if existing is not None:
            return DecisionReportQueueResponse(
                job=None, package=_package_summary(existing), reused_existing_package=True
            )
    now = datetime.now(UTC)
    job = DecisionReportJob(
        id=uuid4(),
        process_id=process_id,
        decision_run_id=run.id,
        status=DecisionReportJobStatus.PENDING.value,
        priority=100,
        max_attempts=3,
        available_at=now,
        force=payload.force,
    )
    session.add(job)
    session.flush()
    package = DecisionReportPackage(
        id=uuid4(),
        process_id=process_id,
        decision_run_id=run.id,
        job_id=job.id,
        status=DecisionReportPackageStatus.DRAFT.value,
        package_version=PACKAGE_VERSION,
        template_version=templates.version,
        input_manifest=input_manifest,
        input_digest=input_digest,
        artifact_count=0,
        warning_count=0,
        created_by="local-api",
    )
    session.add(package)
    session.flush()
    job.package_id = package.id
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise DomainError(
            DecisionReportErrorCode.DECISION_REPORT_ALREADY_QUEUED,
            "Ya existe un paquete de reporte activo para esa decision.",
            status_code=HTTPStatus.CONFLICT,
        ) from exc
    session.refresh(job)
    session.refresh(package)
    return DecisionReportQueueResponse(job=_job_summary(job), package=_package_summary(package))


@router.get("/{process_id}/decision-reports", response_model=DecisionReportPackageList)
def list_decision_reports(
    process_id: UUID,
    session: SessionDep,
    decision_run_id: UUID | None = None,
    status: DecisionReportPackageStatus | None = None,
    limit: LimitParam = 20,
    offset: OffsetParam = 0,
) -> DecisionReportPackageList:
    _process_or_404(session, process_id)
    conditions = [DecisionReportPackage.process_id == process_id]
    if decision_run_id is not None:
        conditions.append(DecisionReportPackage.decision_run_id == decision_run_id)
    if status is not None:
        conditions.append(DecisionReportPackage.status == status.value)
    total = (
        session.scalar(select(func.count()).select_from(DecisionReportPackage).where(*conditions))
        or 0
    )
    packages = session.scalars(
        select(DecisionReportPackage)
        .where(*conditions)
        .order_by(DecisionReportPackage.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return DecisionReportPackageList(
        items=[_package_summary(package) for package in packages],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{process_id}/decision-reports/{package_id}",
    response_model=DecisionReportPackageDetail,
)
def get_decision_report(
    process_id: UUID, package_id: UUID, session: SessionDep
) -> DecisionReportPackageDetail:
    package = _package_or_404(session, process_id, package_id)
    artifacts = _artifacts(session, package.id)
    sections = session.scalars(
        select(DecisionReportSection)
        .where(DecisionReportSection.package_id == package.id)
        .order_by(DecisionReportSection.sequence)
    ).all()
    return DecisionReportPackageDetail(
        **_package_summary(package).model_dump(),
        input_manifest=package.input_manifest or {},
        artifacts=[_artifact_metadata(item) for item in artifacts],
        sections=[_section_summary(item) for item in sections],
        manifest_summary={
            "package_digest": package.package_digest,
            "artifact_count": package.artifact_count,
            "template_version": package.template_version,
        },
    )


@router.get(
    "/{process_id}/decision-reports/{package_id}/preview",
    response_model=DecisionReportPreview,
)
def preview_decision_report(
    process_id: UUID, package_id: UUID, session: SessionDep
) -> DecisionReportPreview:
    package = _package_or_404(session, process_id, package_id)
    artifact = _artifact_by_type(session, package.id, DecisionReportArtifactType.EXECUTIVE_MARKDOWN)
    storage = ReportArtifactStorage()
    with storage.open(artifact.storage_key) as fh:
        data = fh.read()
    return DecisionReportPreview(
        package_id=package.id,
        content_type="text/markdown",
        text=data.decode("utf-8"),
        sha256=artifact.sha256,
    )


@router.get("/{process_id}/decision-reports/{package_id}/artifacts/{artifact_id}/download")
def download_report_artifact(
    process_id: UUID, package_id: UUID, artifact_id: UUID, session: SessionDep
) -> StreamingResponse:
    package = _package_or_404(session, process_id, package_id)
    artifact = session.get(DecisionReportArtifact, artifact_id)
    if artifact is None or artifact.package_id != package.id:
        raise DomainError(
            DecisionReportErrorCode.DECISION_REPORT_ARTIFACT_NOT_FOUND,
            "El artefacto no existe para ese paquete.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return _stream_artifact(artifact)


@router.get("/{process_id}/decision-reports/{package_id}/download")
def download_report_zip(
    process_id: UUID, package_id: UUID, session: SessionDep
) -> StreamingResponse:
    package = _package_or_404(session, process_id, package_id)
    artifact = _artifact_by_type(session, package.id, DecisionReportArtifactType.PACKAGE_ZIP)
    return _stream_artifact(artifact)


@router.post(
    "/{process_id}/decision-reports/{package_id}/retry",
    response_model=DecisionReportQueueResponse,
    status_code=HTTPStatus.ACCEPTED,
)
def retry_decision_report(
    process_id: UUID, package_id: UUID, session: SessionDep
) -> DecisionReportQueueResponse:
    package = _package_or_404(session, process_id, package_id)
    if package.status != DecisionReportPackageStatus.FAILED.value:
        raise DomainError(
            DecisionReportErrorCode.DECISION_REPORT_ALREADY_COMPLETED,
            "Solo los paquetes fallidos pueden reintentarse.",
            status_code=HTTPStatus.CONFLICT,
        )
    job = DecisionReportJob(
        id=uuid4(),
        process_id=process_id,
        decision_run_id=package.decision_run_id,
        package_id=package.id,
        status=DecisionReportJobStatus.PENDING.value,
        priority=100,
        max_attempts=3,
        available_at=datetime.now(UTC),
        force=True,
    )
    session.add(job)
    package.job_id = job.id
    package.status = DecisionReportPackageStatus.DRAFT.value
    package.error_code = None
    package.error_message = None
    session.commit()
    session.refresh(job)
    session.refresh(package)
    return DecisionReportQueueResponse(job=_job_summary(job), package=_package_summary(package))


def _process_or_404(session: Session, process_id: UUID) -> Process:
    process = session.get(Process, process_id)
    if process is None:
        raise DomainError(
            DecisionReportErrorCode.DECISION_REPORT_NOT_FOUND,
            "El proceso no existe.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return process


def _completed_decision_or_error(session: Session, process_id: UUID, run_id: UUID) -> DecisionRun:
    run = session.get(DecisionRun, run_id)
    if run is None or run.process_id != process_id:
        raise DomainError(
            DecisionReportErrorCode.DECISION_REPORT_NOT_FOUND,
            "La decision no existe para ese proceso.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    if (
        run.status
        not in {
            DecisionRunStatus.COMPLETED.value,
            DecisionRunStatus.COMPLETED_WITH_WARNINGS.value,
        }
        or run.effective_outcome is None
    ):
        raise DomainError(
            DecisionReportErrorCode.DECISION_REPORT_DECISION_NOT_COMPLETED,
            "La decision preliminar aun no esta completada.",
            status_code=HTTPStatus.CONFLICT,
        )
    return run


def _package_or_404(session: Session, process_id: UUID, package_id: UUID) -> DecisionReportPackage:
    package = session.get(DecisionReportPackage, package_id)
    if package is None or package.process_id != process_id:
        raise DomainError(
            DecisionReportErrorCode.DECISION_REPORT_PACKAGE_NOT_FOUND,
            "El paquete de reporte no existe para ese proceso.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return package


def _artifacts(session: Session, package_id: UUID) -> list[DecisionReportArtifact]:
    return list(
        session.scalars(
            select(DecisionReportArtifact)
            .where(DecisionReportArtifact.package_id == package_id)
            .order_by(DecisionReportArtifact.filename)
        ).all()
    )


def _artifact_by_type(
    session: Session, package_id: UUID, artifact_type: DecisionReportArtifactType
) -> DecisionReportArtifact:
    artifact = session.scalar(
        select(DecisionReportArtifact).where(
            DecisionReportArtifact.package_id == package_id,
            DecisionReportArtifact.artifact_type == artifact_type.value,
        )
    )
    if artifact is None:
        raise DomainError(
            DecisionReportErrorCode.DECISION_REPORT_ARTIFACT_NOT_FOUND,
            "El artefacto solicitado no existe.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return artifact


def _stream_artifact(artifact: DecisionReportArtifact) -> StreamingResponse:
    storage = ReportArtifactStorage()
    with storage.open(artifact.storage_key) as fh:
        data = fh.read()
    headers = {"Content-Disposition": f'attachment; filename="{artifact.filename}"'}
    return StreamingResponse(BytesIO(data), media_type=artifact.content_type, headers=headers)


def _job_summary(job: DecisionReportJob) -> DecisionReportJobSummary:
    return DecisionReportJobSummary(
        id=job.id,
        process_id=job.process_id,
        decision_run_id=job.decision_run_id,
        status=DecisionReportJobStatus(job.status),
        attempt_count=job.attempt_count,
        max_attempts=job.max_attempts,
        force=job.force,
        last_error_code=job.last_error_code,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def _package_summary(package: DecisionReportPackage) -> DecisionReportPackageSummary:
    return DecisionReportPackageSummary(
        id=package.id,
        process_id=package.process_id,
        decision_run_id=package.decision_run_id,
        status=DecisionReportPackageStatus(package.status),
        package_version=package.package_version,
        template_version=package.template_version,
        input_digest=package.input_digest,
        package_digest=package.package_digest,
        artifact_count=package.artifact_count,
        warning_count=package.warning_count,
        created_by=package.created_by,
        published_at=package.published_at,
        error_code=package.error_code,
        error_message=package.error_message,
        created_at=package.created_at,
        updated_at=package.updated_at,
    )


def _artifact_metadata(artifact: DecisionReportArtifact) -> DecisionReportArtifactMetadata:
    return DecisionReportArtifactMetadata(
        id=artifact.id,
        package_id=artifact.package_id,
        artifact_type=DecisionReportArtifactType(artifact.artifact_type),
        filename=artifact.filename,
        content_type=artifact.content_type,
        size_bytes=artifact.size_bytes,
        sha256=artifact.sha256,
        template_version=artifact.template_version,
        source_digest=artifact.source_digest,
        created_at=artifact.created_at,
    )


def _section_summary(section: DecisionReportSection) -> DecisionReportSectionSummary:
    return DecisionReportSectionSummary(
        id=section.id,
        package_id=section.package_id,
        section_code=section.section_code,
        title=section.title,
        sequence=section.sequence,
        summary_payload=section.summary_payload or {},
        warning_codes=list(section.warning_codes or []),
        created_at=section.created_at,
    )
