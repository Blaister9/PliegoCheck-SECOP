"""Endpoints de normalizacion de requisitos y evidencia."""

from __future__ import annotations

from datetime import UTC, datetime
from http import HTTPStatus
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from pliegocheck_api.config import Settings, get_settings
from pliegocheck_api.db import get_session
from pliegocheck_api.errors import DomainError
from pliegocheck_api.models import (
    ImportEvent,
    Process,
    PromptVersion,
    Requirement,
    RequirementEvidence,
    RequirementNormalizationBatch,
    RequirementNormalizationJob,
    RequirementNormalizationRun,
    RequirementRelation,
)
from pliegocheck_api.normalization import build_batches, build_input_snapshot
from pliegocheck_api.prompt_registry import (
    CONSOLIDATION_PROMPT,
    NORMALIZATION_PROMPT,
    PromptRegistryError,
    ensure_prompt_version,
)
from pliegocheck_schemas import (
    ExpectedValue,
    NormalizationBatchSummary,
    NormalizationCreateRequest,
    NormalizationCreateResponse,
    NormalizationErrorCode,
    NormalizationJobSummary,
    NormalizationProvider,
    NormalizationRetryResponse,
    NormalizationRunDetail,
    NormalizationRunList,
    NormalizationRunSummary,
    PromptVersionSummary,
    RequirementBasis,
    RequirementCategory,
    RequirementCriticality,
    RequirementDetail,
    RequirementEvidenceRole,
    RequirementEvidenceStatus,
    RequirementEvidenceValidationStatus,
    RequirementList,
    RequirementModality,
    RequirementNormalizationStatus,
    RequirementRelationType,
    RequirementReviewStatus,
    RequirementScope,
    RequirementSubsanability,
    SourceLocation,
)
from pliegocheck_schemas import NormalizedRequirement as NormalizedRequirementContract
from pliegocheck_schemas import (
    RequirementEvidence as RequirementEvidenceContract,
)
from pliegocheck_schemas import (
    RequirementRelation as RequirementRelationContract,
)

router = APIRouter(prefix="/processes", tags=["requirements"])
SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
LimitParam = Annotated[int, Query(ge=1, le=100)]
OffsetParam = Annotated[int, Query(ge=0)]


@router.post(
    "/{process_id}/requirements/normalizations",
    response_model=NormalizationCreateResponse,
    status_code=HTTPStatus.ACCEPTED,
)
def create_normalization(
    process_id: UUID,
    payload: NormalizationCreateRequest,
    response: Response,
    session: SessionDep,
    settings: SettingsDep,
) -> NormalizationCreateResponse:
    _get_process_or_404(session, process_id)
    _ensure_normalization_configured(settings)
    try:
        normalization_prompt = ensure_prompt_version(session, NORMALIZATION_PROMPT)
        consolidation_prompt = ensure_prompt_version(session, CONSOLIDATION_PROMPT)
        snapshot = build_input_snapshot(
            session,
            process_id=process_id,
            document_ids=payload.document_ids,
            settings=settings,
        )
    except PromptRegistryError as exc:
        session.rollback()
        raise DomainError(
            exc.code, exc.message, status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        ) from exc
    if snapshot.segment_count == 0:
        session.rollback()
        raise DomainError(
            NormalizationErrorCode.NO_ELIGIBLE_SEGMENTS,
            "El proceso no tiene segmentos extraidos elegibles para normalizacion.",
            status_code=HTTPStatus.CONFLICT,
        )

    active = _active_job(session, process_id)
    if active is not None and not payload.force:
        run = _run_for_job(session, active.id)
        if run is not None:
            response.status_code = HTTPStatus.ACCEPTED
            return NormalizationCreateResponse(job=job_to_summary(active), run=run_to_summary(run))

    if not payload.force:
        existing = session.scalar(
            select(RequirementNormalizationRun)
            .where(
                RequirementNormalizationRun.process_id == process_id,
                RequirementNormalizationRun.input_digest == snapshot.input_digest,
                RequirementNormalizationRun.status.in_(
                    [
                        RequirementNormalizationStatus.PENDING.value,
                        RequirementNormalizationStatus.PROCESSING.value,
                        RequirementNormalizationStatus.COMPLETED.value,
                        RequirementNormalizationStatus.COMPLETED_WITH_WARNINGS.value,
                    ]
                ),
            )
            .order_by(RequirementNormalizationRun.created_at.desc())
            .limit(1)
        )
        if existing is not None:
            job = session.get(RequirementNormalizationJob, existing.job_id)
            if job is not None:
                return NormalizationCreateResponse(
                    job=job_to_summary(job), run=run_to_summary(existing)
                )

    batches = build_batches(
        snapshot.manifest,
        max_segments_per_batch=settings.openai_normalization_max_segments_per_batch,
        max_characters_per_batch=settings.openai_normalization_max_characters_per_batch,
    )
    if not batches:
        session.rollback()
        raise DomainError(
            NormalizationErrorCode.NO_ELIGIBLE_SEGMENTS,
            "No fue posible construir lotes de normalizacion.",
            status_code=HTTPStatus.CONFLICT,
        )
    provider = (
        NormalizationProvider.FAKE
        if settings.allow_fake_normalization_provider and not settings.ai_enabled
        else NormalizationProvider.OPENAI
    )
    job = RequirementNormalizationJob(
        id=uuid4(),
        process_id=process_id,
        status=RequirementNormalizationStatus.PENDING.value,
        max_attempts=max(1, settings.openai_normalization_max_retries + 1),
        available_at=datetime.now(UTC),
        force=payload.force,
    )
    session.add(job)
    session.flush()
    run = RequirementNormalizationRun(
        id=uuid4(),
        job_id=job.id,
        process_id=process_id,
        status=RequirementNormalizationStatus.PENDING.value,
        provider=provider.value,
        model=settings.openai_normalization_model,
        reasoning_effort=settings.openai_normalization_reasoning_effort,
        prompt_version_id=normalization_prompt.id,
        consolidation_prompt_version_id=consolidation_prompt.id,
        input_manifest=snapshot.manifest,
        input_digest=snapshot.input_digest,
        source_extraction_ids=[
            str(extraction_id) for extraction_id in snapshot.source_extraction_ids
        ],
        segment_count=snapshot.segment_count,
        batch_count=len(batches),
        candidate_count=0,
        accepted_requirement_count=0,
        rejected_candidate_count=0,
        warning_count=len(snapshot.warnings),
        input_tokens=0,
        output_tokens=0,
        reasoning_tokens=0,
        provider_response_ids=[],
    )
    session.add(run)
    session.flush()
    job.run_id = run.id
    for batch in batches:
        session.add(
            RequirementNormalizationBatch(
                id=uuid4(),
                run_id=run.id,
                batch_index=batch.index,
                status=RequirementNormalizationStatus.PENDING.value,
                segment_ids=[str(segment_id) for segment_id in batch.segment_ids],
                input_digest=batch.input_digest,
            )
        )
    _add_event(
        session,
        process_id=process_id,
        event_type="NORMALIZATION_QUEUED",
        details={
            "job_id": str(job.id),
            "run_id": str(run.id),
            "input_digest": snapshot.input_digest,
            "segment_count": str(snapshot.segment_count),
            "batch_count": str(len(batches)),
            "provider": provider.value,
            "model": settings.openai_normalization_model,
        },
    )
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        active_after_error = _active_job(session, process_id)
        if active_after_error is not None:
            run_after_error = _run_for_job(session, active_after_error.id)
            if run_after_error is not None:
                return NormalizationCreateResponse(
                    job=job_to_summary(active_after_error),
                    run=run_to_summary(run_after_error),
                )
        raise DomainError(
            NormalizationErrorCode.NORMALIZATION_ALREADY_ACTIVE,
            "El proceso ya tiene una normalizacion activa.",
            status_code=HTTPStatus.CONFLICT,
        ) from exc
    except SQLAlchemyError as exc:
        session.rollback()
        raise DomainError(
            NormalizationErrorCode.DATABASE_ERROR,
            "No fue posible crear la normalizacion.",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        ) from exc
    session.refresh(job)
    session.refresh(run)
    return NormalizationCreateResponse(job=job_to_summary(job), run=run_to_summary(run))


@router.get(
    "/{process_id}/requirements/normalizations",
    response_model=NormalizationRunList,
)
def list_normalizations(
    process_id: UUID,
    session: SessionDep,
    limit: LimitParam = 20,
    offset: OffsetParam = 0,
) -> NormalizationRunList:
    _get_process_or_404(session, process_id)
    total = (
        session.scalar(
            select(func.count())
            .select_from(RequirementNormalizationRun)
            .where(RequirementNormalizationRun.process_id == process_id)
        )
        or 0
    )
    runs = session.scalars(
        select(RequirementNormalizationRun)
        .where(RequirementNormalizationRun.process_id == process_id)
        .order_by(RequirementNormalizationRun.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return NormalizationRunList(
        process_id=process_id,
        total=total,
        limit=limit,
        offset=offset,
        items=[run_to_summary(run) for run in runs],
    )


@router.get(
    "/{process_id}/requirements/normalizations/{run_id}",
    response_model=NormalizationRunDetail,
)
def get_normalization(
    process_id: UUID,
    run_id: UUID,
    session: SessionDep,
) -> NormalizationRunDetail:
    run = _get_run_or_404(session, process_id, run_id)
    return run_to_detail(run)


@router.post(
    "/{process_id}/requirements/normalizations/{run_id}/retry",
    response_model=NormalizationRetryResponse,
)
def retry_normalization(
    process_id: UUID,
    run_id: UUID,
    session: SessionDep,
    settings: SettingsDep,
) -> NormalizationRetryResponse:
    _ensure_normalization_configured(settings)
    run = _get_run_or_404(session, process_id, run_id)
    if run.status not in {RequirementNormalizationStatus.FAILED.value}:
        raise DomainError(
            NormalizationErrorCode.NORMALIZATION_NOT_RETRYABLE,
            "Solo las normalizaciones fallidas pueden reintentarse.",
            status_code=HTTPStatus.CONFLICT,
        )
    active = _active_job(session, process_id)
    if active is not None:
        return NormalizationRetryResponse(
            job=job_to_summary(active),
            run=run_to_summary(run),
            message="El proceso ya tiene un trabajo activo.",
        )
    job = RequirementNormalizationJob(
        id=uuid4(),
        process_id=process_id,
        run_id=run.id,
        status=RequirementNormalizationStatus.PENDING.value,
        max_attempts=max(1, settings.openai_normalization_max_retries + 1),
        available_at=datetime.now(UTC),
        force=True,
    )
    session.add(job)
    run.job_id = job.id
    run.status = RequirementNormalizationStatus.PENDING.value
    run.error_code = None
    run.error_message = None
    for batch in run.batches:
        if batch.status == RequirementNormalizationStatus.FAILED.value:
            batch.status = RequirementNormalizationStatus.PENDING.value
            batch.error_code = None
            batch.error_message = None
    _add_event(
        session,
        process_id=process_id,
        event_type="NORMALIZATION_RETRIED",
        details={"job_id": str(job.id), "run_id": str(run.id)},
    )
    session.commit()
    return NormalizationRetryResponse(
        job=job_to_summary(job),
        run=run_to_summary(run),
        message="Normalizacion reenviada a la cola.",
    )


@router.get("/{process_id}/requirements", response_model=RequirementList)
def list_requirements(
    process_id: UUID,
    session: SessionDep,
    limit: LimitParam = 20,
    offset: OffsetParam = 0,
    category: Annotated[RequirementCategory | None, Query()] = None,
    scope: Annotated[RequirementScope | None, Query()] = None,
    criticality: Annotated[RequirementCriticality | None, Query()] = None,
    subsanability: Annotated[RequirementSubsanability | None, Query()] = None,
    review_status: Annotated[RequirementReviewStatus | None, Query()] = None,
    requires_human_review: Annotated[bool | None, Query()] = None,
    search: Annotated[str | None, Query(min_length=1, max_length=200)] = None,
    normalization_run_id: Annotated[UUID | None, Query()] = None,
) -> RequirementList:
    _get_process_or_404(session, process_id)
    filters = [Requirement.process_id == process_id, Requirement.is_active.is_(True)]
    if category is not None:
        filters.append(Requirement.category == category.value)
    if scope is not None:
        filters.append(Requirement.scope == scope.value)
    if criticality is not None:
        filters.append(Requirement.criticality == criticality.value)
    if subsanability is not None:
        filters.append(Requirement.subsanability == subsanability.value)
    if review_status is not None:
        filters.append(Requirement.review_status == review_status.value)
    if requires_human_review is not None:
        filters.append(Requirement.requires_human_review.is_(requires_human_review))
    if normalization_run_id is not None:
        filters.append(Requirement.normalization_run_id == normalization_run_id)
    if search is not None:
        pattern = f"%{search.strip()}%"
        filters.append(
            or_(Requirement.description.ilike(pattern), Requirement.condition_text.ilike(pattern))
        )
    total = session.scalar(select(func.count()).select_from(Requirement).where(*filters)) or 0
    requirements = session.scalars(
        select(Requirement)
        .where(*filters)
        .order_by(Requirement.created_at.asc(), Requirement.id.asc())
        .limit(limit)
        .offset(offset)
    ).all()
    return RequirementList(
        process_id=process_id,
        total=total,
        limit=limit,
        offset=offset,
        items=[requirement_to_contract(requirement) for requirement in requirements],
    )


@router.get("/{process_id}/requirements/{requirement_id}", response_model=RequirementDetail)
def get_requirement(
    process_id: UUID,
    requirement_id: UUID,
    session: SessionDep,
) -> RequirementDetail:
    _get_process_or_404(session, process_id)
    requirement = session.scalar(
        select(Requirement)
        .where(Requirement.id == requirement_id, Requirement.process_id == process_id)
        .options(selectinload(Requirement.evidence), selectinload(Requirement.run))
    )
    if requirement is None:
        raise DomainError(
            NormalizationErrorCode.REQUIREMENT_NOT_FOUND,
            "El requisito no existe para este proceso.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    relations = session.scalars(
        select(RequirementRelation)
        .where(
            RequirementRelation.process_id == process_id,
            or_(
                RequirementRelation.source_requirement_id == requirement_id,
                RequirementRelation.target_requirement_id == requirement_id,
            ),
        )
        .order_by(RequirementRelation.created_at.asc())
    ).all()
    run = requirement.run
    prompt = session.get(PromptVersion, run.prompt_version_id)
    if prompt is None:
        raise DomainError(
            NormalizationErrorCode.PROMPT_VERSION_NOT_FOUND,
            "La version de prompt asociada no existe.",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )
    base = requirement_to_contract(requirement).model_dump()
    return RequirementDetail(
        **base,
        evidence=[evidence_to_contract(evidence) for evidence in requirement.evidence],
        relations=[relation_to_contract(relation) for relation in relations],
        run=run_to_summary(run),
        prompt_version=prompt_to_summary(prompt),
        documents=list(_manifest_list(run.input_manifest, "documents")),
    )


def _get_process_or_404(session: Session, process_id: UUID) -> Process:
    process = session.get(Process, process_id)
    if process is None:
        raise DomainError(
            NormalizationErrorCode.PROCESS_NOT_FOUND,
            "El proceso no existe.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return process


def _get_run_or_404(
    session: Session, process_id: UUID, run_id: UUID
) -> RequirementNormalizationRun:
    run = session.scalar(
        select(RequirementNormalizationRun)
        .where(
            RequirementNormalizationRun.id == run_id,
            RequirementNormalizationRun.process_id == process_id,
        )
        .options(
            selectinload(RequirementNormalizationRun.batches),
            selectinload(RequirementNormalizationRun.prompt_version),
            selectinload(RequirementNormalizationRun.consolidation_prompt_version),
        )
    )
    if run is None:
        raise DomainError(
            NormalizationErrorCode.NORMALIZATION_RUN_NOT_FOUND,
            "La normalizacion no existe para este proceso.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return run


def _ensure_normalization_configured(settings: Settings) -> None:
    if not settings.ai_enabled and not settings.allow_fake_normalization_provider:
        raise DomainError(
            NormalizationErrorCode.NORMALIZATION_DISABLED,
            "La normalizacion con IA no esta habilitada.",
            status_code=HTTPStatus.CONFLICT,
        )
    if settings.ai_enabled and not settings.openai_api_key:
        raise DomainError(
            NormalizationErrorCode.OPENAI_API_KEY_MISSING,
            "OPENAI_API_KEY no esta configurada para normalizacion real.",
            status_code=HTTPStatus.CONFLICT,
        )


def _active_job(session: Session, process_id: UUID) -> RequirementNormalizationJob | None:
    return session.scalar(
        select(RequirementNormalizationJob)
        .where(
            RequirementNormalizationJob.process_id == process_id,
            RequirementNormalizationJob.status.in_(
                [
                    RequirementNormalizationStatus.PENDING.value,
                    RequirementNormalizationStatus.PROCESSING.value,
                ]
            ),
        )
        .order_by(RequirementNormalizationJob.created_at.asc())
        .limit(1)
    )


def _run_for_job(session: Session, job_id: UUID) -> RequirementNormalizationRun | None:
    return session.scalar(
        select(RequirementNormalizationRun)
        .where(RequirementNormalizationRun.job_id == job_id)
        .order_by(RequirementNormalizationRun.created_at.desc())
        .limit(1)
    )


def _add_event(
    session: Session,
    *,
    process_id: UUID,
    event_type: str,
    details: dict[str, str],
) -> None:
    session.add(
        ImportEvent(
            id=uuid4(),
            process_id=process_id,
            document_id=None,
            event_type=event_type,
            details=details,
        )
    )


def prompt_to_summary(prompt: PromptVersion) -> PromptVersionSummary:
    return PromptVersionSummary(
        id=prompt.id,
        prompt_name=prompt.prompt_name,
        semantic_version=prompt.semantic_version,
        content_sha256=prompt.content_sha256,
        provider=prompt.provider,
        is_active=prompt.is_active,
        created_at=prompt.created_at,
    )


def job_to_summary(job: RequirementNormalizationJob) -> NormalizationJobSummary:
    return NormalizationJobSummary(
        id=job.id,
        process_id=job.process_id,
        run_id=job.run_id,
        status=RequirementNormalizationStatus(job.status),
        priority=job.priority,
        attempt_count=job.attempt_count,
        max_attempts=job.max_attempts,
        force=job.force,
        available_at=job.available_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        last_error_code=job.last_error_code,
        last_error_message=job.last_error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def batch_to_summary(batch: RequirementNormalizationBatch) -> NormalizationBatchSummary:
    return NormalizationBatchSummary(
        id=batch.id,
        run_id=batch.run_id,
        batch_index=batch.batch_index,
        status=RequirementNormalizationStatus(batch.status),
        segment_ids=[UUID(str(segment_id)) for segment_id in batch.segment_ids],
        input_digest=batch.input_digest,
        provider_response_id=batch.provider_response_id,
        candidate_count=batch.candidate_count,
        input_tokens=batch.input_tokens,
        output_tokens=batch.output_tokens,
        reasoning_tokens=batch.reasoning_tokens,
        started_at=batch.started_at,
        finished_at=batch.finished_at,
        error_code=batch.error_code,
        error_message=batch.error_message,
        created_at=batch.created_at,
    )


def run_to_summary(run: RequirementNormalizationRun) -> NormalizationRunSummary:
    return NormalizationRunSummary(
        id=run.id,
        job_id=run.job_id,
        process_id=run.process_id,
        status=RequirementNormalizationStatus(run.status),
        provider=NormalizationProvider(run.provider),
        model=run.model,
        reasoning_effort=run.reasoning_effort,
        prompt_version_id=run.prompt_version_id,
        consolidation_prompt_version_id=run.consolidation_prompt_version_id,
        input_digest=run.input_digest,
        source_extraction_ids=[
            UUID(str(extraction_id)) for extraction_id in run.source_extraction_ids
        ],
        segment_count=run.segment_count,
        batch_count=run.batch_count,
        candidate_count=run.candidate_count,
        accepted_requirement_count=run.accepted_requirement_count,
        rejected_candidate_count=run.rejected_candidate_count,
        warning_count=run.warning_count,
        input_tokens=run.input_tokens,
        output_tokens=run.output_tokens,
        reasoning_tokens=run.reasoning_tokens,
        provider_response_ids=list(run.provider_response_ids),
        started_at=run.started_at,
        finished_at=run.finished_at,
        error_code=run.error_code,
        error_message=run.error_message,
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


def run_to_detail(run: RequirementNormalizationRun) -> NormalizationRunDetail:
    return NormalizationRunDetail(
        **run_to_summary(run).model_dump(),
        prompt_version=prompt_to_summary(run.prompt_version),
        consolidation_prompt_version=prompt_to_summary(run.consolidation_prompt_version),
        batches=[batch_to_summary(batch) for batch in run.batches],
        warnings=[str(warning) for warning in run.input_manifest.get("warnings", [])],
        documents_used=list(_manifest_list(run.input_manifest, "documents")),
        omitted_documents=list(_manifest_list(run.input_manifest, "omitted_documents")),
    )


def requirement_to_contract(requirement: Requirement) -> NormalizedRequirementContract:
    return NormalizedRequirementContract(
        id=requirement.id,
        process_id=requirement.process_id,
        normalization_run_id=requirement.normalization_run_id,
        stable_key=requirement.stable_key,
        category=RequirementCategory(requirement.category),
        scope=RequirementScope(requirement.scope),
        modality=RequirementModality(requirement.modality),
        description=requirement.description,
        condition_text=requirement.condition_text,
        expected_value=(
            ExpectedValue.model_validate(requirement.expected_value)
            if requirement.expected_value is not None
            else None
        ),
        criticality=RequirementCriticality(requirement.criticality),
        criticality_basis=RequirementBasis(requirement.criticality_basis),
        subsanability=RequirementSubsanability(requirement.subsanability),
        subsanability_basis=RequirementBasis(requirement.subsanability_basis),
        confidence=float(requirement.confidence),
        evidence_status=RequirementEvidenceStatus(requirement.evidence_status),
        review_status=RequirementReviewStatus(requirement.review_status),
        requires_human_review=requirement.requires_human_review,
        is_active=requirement.is_active,
        created_at=requirement.created_at,
        updated_at=requirement.updated_at,
    )


def evidence_to_contract(evidence: RequirementEvidence) -> RequirementEvidenceContract:
    return RequirementEvidenceContract(
        id=evidence.id,
        requirement_id=evidence.requirement_id,
        extraction_id=evidence.extraction_id,
        segment_id=evidence.segment_id,
        evidence_role=RequirementEvidenceRole(evidence.evidence_role),
        quoted_text=evidence.quoted_text,
        quote_start=evidence.quote_start,
        quote_end=evidence.quote_end,
        source_location=SourceLocation.model_validate(evidence.source_location),
        validation_status=RequirementEvidenceValidationStatus(evidence.validation_status),
        created_at=evidence.created_at,
    )


def relation_to_contract(relation: RequirementRelation) -> RequirementRelationContract:
    return RequirementRelationContract(
        id=relation.id,
        process_id=relation.process_id,
        normalization_run_id=relation.normalization_run_id,
        source_requirement_id=relation.source_requirement_id,
        target_requirement_id=relation.target_requirement_id,
        relation_type=RequirementRelationType(relation.relation_type),
        explanation=relation.explanation,
        confidence=float(relation.confidence),
        requires_human_review=relation.requires_human_review,
        created_at=relation.created_at,
    )


def _manifest_list(manifest: dict[str, Any], key: str) -> list[dict[str, object]]:
    value = manifest.get(key, [])
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]
