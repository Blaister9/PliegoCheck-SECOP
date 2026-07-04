# mypy: ignore-errors
"""Endpoints de evaluaciones especializadas deterministicas."""

from __future__ import annotations

from datetime import UTC, datetime
from http import HTTPStatus
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from pliegocheck_api.db import get_session
from pliegocheck_api.errors import DomainError
from pliegocheck_api.models import (
    CompanyProfile,
    CompanyProfileSnapshot,
    Process,
    Requirement,
    RequirementNormalizationRun,
    SpecializedEvaluationEvent,
    SpecializedEvaluationEvidence,
    SpecializedEvaluationJob,
    SpecializedEvaluationResult,
    SpecializedEvaluationReview,
    SpecializedEvaluationRun,
    SpecializedRequirementRule,
)
from pliegocheck_api.specialized_evaluation import (
    RULE_MAPPING_VERSION,
    build_input_manifest,
    categories_for_domain,
    map_specialized_requirement,
    stable_digest,
    supported_domains,
)
from pliegocheck_schemas import (
    CompanySnapshotStatus,
    NormalizationProvider,
    RequirementNormalizationStatus,
    SpecializedErrorCode,
    SpecializedEvaluationDomain,
    SpecializedEvaluationJobStatus,
    SpecializedEvaluationJobSummary,
    SpecializedEvaluationList,
    SpecializedEvaluationQueueResponse,
    SpecializedEvaluationReadiness,
    SpecializedEvaluationRequest,
    SpecializedEvaluationResultDetail,
    SpecializedEvaluationResultList,
    SpecializedEvaluationResultReviewRequest,
    SpecializedEvaluationResultStatus,
    SpecializedEvaluationReviewStatus,
    SpecializedEvaluationRunDetail,
    SpecializedEvaluationRunStatus,
    SpecializedRequirementRuleUpdate,
    SpecializedRuleMappingStatus,
    SpecializedRuleSourceBasis,
)
from pliegocheck_schemas import (
    SpecializedRequirementRule as SpecializedRequirementRuleContract,
)

router = APIRouter(prefix="/processes", tags=["specialized-evaluations"])
SessionDep = Annotated[Session, Depends(get_session)]
LimitParam = Annotated[int, Query(ge=1, le=100)]
OffsetParam = Annotated[int, Query(ge=0)]


@router.get(
    "/{process_id}/specialized-evaluations/readiness",
    response_model=SpecializedEvaluationReadiness,
)
def get_specialized_readiness(
    process_id: UUID,
    normalization_run_id: UUID,
    company_profile_snapshot_id: UUID,
    domain: SpecializedEvaluationDomain,
    session: SessionDep,
) -> SpecializedEvaluationReadiness:
    _process_or_404(session, process_id)
    normalization = _normalization_or_404(session, process_id, normalization_run_id)
    _ensure_normalization_completed(normalization)
    snapshot = session.get(CompanyProfileSnapshot, company_profile_snapshot_id)
    if snapshot is None:
        raise _domain_error(
            SpecializedErrorCode.SPECIALIZED_INPUT_MISMATCH,
            "El snapshot de empresa no existe.",
            HTTPStatus.NOT_FOUND,
        )
    requirements = _requirements(session, process_id, normalization_run_id, domain.value)
    rules = _ensure_rules(session, requirements, domain.value)
    snapshot_published = snapshot.status == CompanySnapshotStatus.PUBLISHED.value
    warnings: list[str] = []
    if not snapshot_published:
        warnings.append("SPECIALIZED_SNAPSHOT_NOT_PUBLISHED")
    return SpecializedEvaluationReadiness(
        process_id=process_id,
        normalization_run_id=normalization_run_id,
        company_profile_snapshot_id=company_profile_snapshot_id,
        domain=domain,
        available_domains=[SpecializedEvaluationDomain(item) for item in supported_domains()],
        requirement_count=len(requirements),
        evaluable_count=sum(1 for rule in rules if rule.mapping_status == "MAPPED"),
        ambiguous_count=sum(1 for rule in rules if rule.mapping_status == "AMBIGUOUS"),
        unsupported_count=sum(1 for rule in rules if rule.mapping_status == "UNSUPPORTED"),
        snapshot_published=snapshot_published,
        warnings=warnings,
        rules=[rule_to_contract(rule) for rule in rules],
    )


@router.post(
    "/{process_id}/specialized-evaluations",
    response_model=SpecializedEvaluationQueueResponse,
    status_code=HTTPStatus.ACCEPTED,
)
def create_specialized_evaluation(
    process_id: UUID,
    payload: SpecializedEvaluationRequest,
    response: Response,
    session: SessionDep,
) -> SpecializedEvaluationQueueResponse:
    process = _process_or_404(session, process_id)
    normalization = _normalization_or_404(session, process_id, payload.normalization_run_id)
    _ensure_normalization_completed(normalization)
    company = _company_or_404(session, payload.company_id)
    snapshot = _snapshot_or_404(session, company.id, payload.company_profile_snapshot_id)
    _ensure_snapshot_published(snapshot)
    requirements = _requirements(session, process_id, normalization.id, payload.domain.value)
    if not requirements:
        raise _domain_error(
            SpecializedErrorCode.SPECIALIZED_REQUIREMENTS_NOT_FOUND,
            "La normalizacion no contiene requisitos para el dominio solicitado.",
            HTTPStatus.CONFLICT,
        )
    rules = _ensure_rules(session, requirements, payload.domain.value)
    manifest = build_input_manifest(
        process=process,
        normalization_run=normalization,
        snapshot=snapshot,
        requirements=requirements,
        domain=payload.domain.value,
    )
    manifest["specialized_rule_versions"] = [
        {
            "requirement_id": str(rule.requirement_id),
            "rule_id": str(rule.id),
            "version": rule.version,
        }
        for rule in rules
    ]
    input_digest = stable_digest(manifest)
    existing = _existing_run(session, process_id, input_digest, payload.force)
    if existing is not None:
        job = session.get(SpecializedEvaluationJob, existing.job_id)
        if job is not None:
            response.status_code = HTTPStatus.ACCEPTED
            return SpecializedEvaluationQueueResponse(
                job=job_summary(job), run=run_summary(existing)
            )
    job = SpecializedEvaluationJob(
        id=uuid4(),
        process_id=process_id,
        normalization_run_id=normalization.id,
        company_id=company.id,
        company_profile_snapshot_id=snapshot.id,
        domain=payload.domain.value,
        status=SpecializedEvaluationJobStatus.PENDING.value,
        priority=100,
        max_attempts=3,
        available_at=datetime.now(UTC),
        force=payload.force,
    )
    session.add(job)
    session.flush()
    run = SpecializedEvaluationRun(
        id=uuid4(),
        job_id=job.id,
        process_id=process_id,
        normalization_run_id=normalization.id,
        company_id=company.id,
        company_profile_snapshot_id=snapshot.id,
        domain=payload.domain.value,
        status=SpecializedEvaluationRunStatus.PENDING.value,
        input_manifest=manifest,
        input_digest=input_digest,
        rule_version=RULE_MAPPING_VERSION,
        requirement_count=len(requirements),
    )
    session.add(run)
    session.flush()
    job.run_id = run.id
    _add_event(
        session,
        job=job,
        run=run,
        event_type="SPECIALIZED_EVALUATION_QUEUED",
        summary="Evaluacion especializada encolada.",
        details={"input_digest": input_digest, "requirement_count": len(requirements)},
    )
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        active = _active_job(
            session, process_id, normalization.id, company.id, snapshot.id, payload.domain.value
        )
        if active is not None and active.run_id is not None:
            active_run = session.get(SpecializedEvaluationRun, active.run_id)
            if active_run is not None:
                return SpecializedEvaluationQueueResponse(
                    job=job_summary(active), run=run_summary(active_run)
                )
        raise _domain_error(
            SpecializedErrorCode.SPECIALIZED_EVALUATION_ALREADY_QUEUED,
            "Ya existe una evaluacion especializada activa para esas entradas.",
            HTTPStatus.CONFLICT,
        ) from exc
    except SQLAlchemyError as exc:
        session.rollback()
        raise _domain_error(
            SpecializedErrorCode.DATABASE_ERROR,
            "No fue posible encolar la evaluacion especializada.",
            HTTPStatus.INTERNAL_SERVER_ERROR,
        ) from exc
    session.refresh(job)
    session.refresh(run)
    return SpecializedEvaluationQueueResponse(job=job_summary(job), run=run_summary(run))


@router.get("/{process_id}/specialized-evaluations", response_model=SpecializedEvaluationList)
def list_specialized_evaluations(
    process_id: UUID,
    session: SessionDep,
    company_id: UUID | None = None,
    company_profile_snapshot_id: UUID | None = None,
    domain: SpecializedEvaluationDomain | None = None,
    status: SpecializedEvaluationRunStatus | None = None,
    limit: LimitParam = 20,
    offset: OffsetParam = 0,
) -> SpecializedEvaluationList:
    _process_or_404(session, process_id)
    conditions = [SpecializedEvaluationRun.process_id == process_id]
    if company_id is not None:
        conditions.append(SpecializedEvaluationRun.company_id == company_id)
    if company_profile_snapshot_id is not None:
        conditions.append(
            SpecializedEvaluationRun.company_profile_snapshot_id == company_profile_snapshot_id
        )
    if domain is not None:
        conditions.append(SpecializedEvaluationRun.domain == domain.value)
    if status is not None:
        conditions.append(SpecializedEvaluationRun.status == status.value)
    total = (
        session.scalar(
            select(func.count()).select_from(SpecializedEvaluationRun).where(*conditions)
        )
        or 0
    )
    runs = session.scalars(
        select(SpecializedEvaluationRun)
        .where(*conditions)
        .order_by(SpecializedEvaluationRun.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return SpecializedEvaluationList(
        items=[run_summary(run) for run in runs], total=total, limit=limit, offset=offset
    )


@router.get(
    "/{process_id}/specialized-evaluations/{run_id}",
    response_model=SpecializedEvaluationRunDetail,
)
def get_specialized_evaluation(
    process_id: UUID, run_id: UUID, session: SessionDep
) -> SpecializedEvaluationRunDetail:
    return run_detail(session, _run_or_404(session, process_id, run_id))


@router.post(
    "/{process_id}/specialized-evaluations/{run_id}/retry",
    response_model=SpecializedEvaluationQueueResponse,
    status_code=HTTPStatus.ACCEPTED,
)
def retry_specialized_evaluation(
    process_id: UUID,
    run_id: UUID,
    session: SessionDep,
) -> SpecializedEvaluationQueueResponse:
    run = _run_or_404(session, process_id, run_id)
    if run.status != SpecializedEvaluationRunStatus.FAILED.value:
        raise _domain_error(
            SpecializedErrorCode.SPECIALIZED_EVALUATION_ALREADY_COMPLETED,
            "Solo las evaluaciones especializadas fallidas pueden reintentarse.",
            HTTPStatus.CONFLICT,
        )
    job = SpecializedEvaluationJob(
        id=uuid4(),
        process_id=process_id,
        normalization_run_id=run.normalization_run_id,
        company_id=run.company_id,
        company_profile_snapshot_id=run.company_profile_snapshot_id,
        domain=run.domain,
        run_id=run.id,
        status=SpecializedEvaluationJobStatus.PENDING.value,
        priority=100,
        max_attempts=3,
        available_at=datetime.now(UTC),
        force=True,
    )
    session.add(job)
    run.job_id = job.id
    run.status = SpecializedEvaluationRunStatus.PENDING.value
    run.error_code = None
    run.error_message = None
    _add_event(
        session,
        job=job,
        run=run,
        event_type="SPECIALIZED_EVALUATION_RETRIED",
        summary="Evaluacion especializada reenviada a la cola.",
        details={},
    )
    session.commit()
    session.refresh(job)
    session.refresh(run)
    return SpecializedEvaluationQueueResponse(job=job_summary(job), run=run_summary(run))


@router.get(
    "/{process_id}/specialized-evaluations/{run_id}/results",
    response_model=SpecializedEvaluationResultList,
)
def list_specialized_results(
    process_id: UUID,
    run_id: UUID,
    session: SessionDep,
    limit: LimitParam = 100,
    offset: OffsetParam = 0,
) -> SpecializedEvaluationResultList:
    _run_or_404(session, process_id, run_id)
    total = (
        session.scalar(
            select(func.count())
            .select_from(SpecializedEvaluationResult)
            .where(SpecializedEvaluationResult.run_id == run_id)
        )
        or 0
    )
    results = session.scalars(
        select(SpecializedEvaluationResult)
        .where(SpecializedEvaluationResult.run_id == run_id)
        .order_by(SpecializedEvaluationResult.created_at.asc())
        .limit(limit)
        .offset(offset)
    ).all()
    return SpecializedEvaluationResultList(
        items=[result_contract(result) for result in results],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{process_id}/specialized-evaluations/{run_id}/results/{result_id}",
    response_model=SpecializedEvaluationResultDetail,
)
def get_specialized_result(
    process_id: UUID,
    run_id: UUID,
    result_id: UUID,
    session: SessionDep,
) -> SpecializedEvaluationResultDetail:
    return result_detail(session, _result_or_404(session, process_id, run_id, result_id))


@router.post(
    "/{process_id}/specialized-evaluations/{run_id}/results/{result_id}/review",
    response_model=SpecializedEvaluationResultDetail,
)
def review_specialized_result(
    process_id: UUID,
    run_id: UUID,
    result_id: UUID,
    payload: SpecializedEvaluationResultReviewRequest,
    session: SessionDep,
) -> SpecializedEvaluationResultDetail:
    result = _result_or_404(session, process_id, run_id, result_id)
    now = datetime.now(UTC)
    action = {
        SpecializedEvaluationReviewStatus.CONFIRMED: "CONFIRM",
        SpecializedEvaluationReviewStatus.OVERRIDDEN: "OVERRIDE",
        SpecializedEvaluationReviewStatus.REJECTED: "REJECT",
        SpecializedEvaluationReviewStatus.PENDING: "CONFIRM",
    }[payload.review_status]
    review = SpecializedEvaluationReview(
        id=uuid4(),
        result_id=result.id,
        action=action,
        original_status=result.status,
        reviewed_status=payload.override_result.value if payload.override_result else None,
        reason=payload.override_reason or payload.review_notes,
        reviewed_at=now,
    )
    session.add(review)
    result.review_status = payload.review_status.value
    result.reviewed_status = (
        payload.override_result.value if payload.override_result else result.status
    )
    result.review_notes = payload.override_reason or payload.review_notes
    result.reviewed_at = now
    run = session.get(SpecializedEvaluationRun, run_id)
    _add_event(
        session,
        job=None,
        run=run,
        event_type="SPECIALIZED_RESULT_OVERRIDDEN"
        if payload.review_status == SpecializedEvaluationReviewStatus.OVERRIDDEN
        else "SPECIALIZED_RESULT_REVIEWED",
        summary="Resultado especializado revisado manualmente.",
        details={"result_id": str(result.id), "review_status": payload.review_status.value},
    )
    session.commit()
    session.refresh(result)
    return result_detail(session, result)


@router.get(
    "/{process_id}/specialized-requirements/{requirement_id}/rule",
    response_model=SpecializedRequirementRuleContract,
)
def get_specialized_rule(
    process_id: UUID,
    requirement_id: UUID,
    domain: SpecializedEvaluationDomain,
    session: SessionDep,
) -> SpecializedRequirementRuleContract:
    requirement = _requirement_or_404(session, process_id, requirement_id)
    rule = _latest_rule(session, requirement.id, domain.value)
    if rule is None:
        rule = _create_rule(session, requirement, domain.value)
        session.commit()
        session.refresh(rule)
    return rule_to_contract(rule)


@router.patch(
    "/{process_id}/specialized-requirements/{requirement_id}/rule",
    response_model=SpecializedRequirementRuleContract,
)
def update_specialized_rule(
    process_id: UUID,
    requirement_id: UUID,
    payload: SpecializedRequirementRuleUpdate,
    session: SessionDep,
) -> SpecializedRequirementRuleContract:
    requirement = _requirement_or_404(session, process_id, requirement_id)
    if not payload.override_reason:
        raise _domain_error(
            SpecializedErrorCode.INVALID_SPECIALIZED_OVERRIDE,
            "override_reason es obligatorio para modificar una regla especializada.",
            HTTPStatus.BAD_REQUEST,
        )
    domain = payload.domain.value if payload.domain else _domain_for_category(requirement.category)
    latest = _latest_rule(session, requirement.id, domain)
    if latest is None:
        latest = _create_rule(session, requirement, domain)
        session.flush()
    values = rule_values(latest)
    updates = payload.model_dump(exclude_unset=True)
    override_reason = updates.pop("override_reason", None)
    updates.pop("domain", None)
    for key, value in updates.items():
        values[key] = value.value if hasattr(value, "value") else value
    values["source_basis"] = SpecializedRuleSourceBasis.MANUAL_OVERRIDE.value
    values["mapping_status"] = _manual_mapping_status(values)
    values["requires_human_review"] = True
    values["version"] = latest.version + 1
    values["is_manual_override"] = True
    values["manual_override_payload"] = {"reason": override_reason}
    rule = SpecializedRequirementRule(id=uuid4(), **values)
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule_to_contract(rule)


def _process_or_404(session: Session, process_id: UUID) -> Process:
    process = session.get(Process, process_id)
    if process is None:
        raise _domain_error(
            SpecializedErrorCode.SPECIALIZED_EVALUATION_INPUT_NOT_READY,
            "El proceso no existe.",
            HTTPStatus.NOT_FOUND,
        )
    return process


def _company_or_404(session: Session, company_id: UUID) -> CompanyProfile:
    company = session.get(CompanyProfile, company_id)
    if company is None:
        raise _domain_error(
            SpecializedErrorCode.SPECIALIZED_INPUT_MISMATCH,
            "La empresa no existe.",
            HTTPStatus.NOT_FOUND,
        )
    return company


def _normalization_or_404(
    session: Session, process_id: UUID, run_id: UUID
) -> RequirementNormalizationRun:
    run = session.scalar(
        select(RequirementNormalizationRun).where(
            RequirementNormalizationRun.id == run_id,
            RequirementNormalizationRun.process_id == process_id,
        )
    )
    if run is None:
        raise _domain_error(
            SpecializedErrorCode.SPECIALIZED_EVALUATION_INPUT_NOT_READY,
            "La normalizacion no existe para este proceso.",
            HTTPStatus.NOT_FOUND,
        )
    return run


def _ensure_normalization_completed(run: RequirementNormalizationRun) -> None:
    if run.status not in {
        RequirementNormalizationStatus.COMPLETED.value,
        RequirementNormalizationStatus.COMPLETED_WITH_WARNINGS.value,
    }:
        raise _domain_error(
            SpecializedErrorCode.SPECIALIZED_EVALUATION_INPUT_NOT_READY,
            "La normalizacion debe estar completada.",
            HTTPStatus.CONFLICT,
        )
    if run.provider not in {NormalizationProvider.OPENAI.value, NormalizationProvider.FAKE.value}:
        raise _domain_error(
            SpecializedErrorCode.SPECIALIZED_EVALUATION_INPUT_NOT_READY,
            "La normalizacion no tiene proveedor valido.",
            HTTPStatus.CONFLICT,
        )


def _snapshot_or_404(
    session: Session, company_id: UUID, snapshot_id: UUID
) -> CompanyProfileSnapshot:
    snapshot = session.scalar(
        select(CompanyProfileSnapshot).where(
            CompanyProfileSnapshot.id == snapshot_id,
            CompanyProfileSnapshot.company_id == company_id,
        )
    )
    if snapshot is None:
        raise _domain_error(
            SpecializedErrorCode.SPECIALIZED_INPUT_MISMATCH,
            "El snapshot de empresa no existe.",
            HTTPStatus.NOT_FOUND,
        )
    return snapshot


def _ensure_snapshot_published(snapshot: CompanyProfileSnapshot) -> None:
    if snapshot.status != CompanySnapshotStatus.PUBLISHED.value:
        raise _domain_error(
            SpecializedErrorCode.SPECIALIZED_SNAPSHOT_NOT_PUBLISHED,
            "La evaluacion especializada exige un snapshot publicado.",
            HTTPStatus.CONFLICT,
        )


def _requirements(
    session: Session, process_id: UUID, normalization_run_id: UUID, domain: str
) -> list[Requirement]:
    categories = categories_for_domain(domain)
    return list(
        session.scalars(
            select(Requirement)
            .where(
                Requirement.process_id == process_id,
                Requirement.normalization_run_id == normalization_run_id,
                Requirement.category.in_(categories),
                Requirement.is_active.is_(True),
            )
            .order_by(Requirement.created_at.asc(), Requirement.id.asc())
        ).all()
    )


def _ensure_rules(
    session: Session, requirements: list[Requirement], domain: str
) -> list[SpecializedRequirementRule]:
    rules = []
    for requirement in requirements:
        rule = _latest_rule(session, requirement.id, domain)
        if rule is None:
            rule = _create_rule(session, requirement, domain)
        rules.append(rule)
    session.flush()
    return rules


def _create_rule(
    session: Session, requirement: Requirement, domain: str
) -> SpecializedRequirementRule:
    rule = SpecializedRequirementRule(
        id=uuid4(), **map_specialized_requirement(requirement, domain)
    )
    session.add(rule)
    return rule


def _latest_rule(
    session: Session, requirement_id: UUID, domain: str
) -> SpecializedRequirementRule | None:
    return session.scalar(
        select(SpecializedRequirementRule)
        .where(
            SpecializedRequirementRule.requirement_id == requirement_id,
            SpecializedRequirementRule.domain == domain,
        )
        .order_by(SpecializedRequirementRule.version.desc())
        .limit(1)
    )


def _existing_run(
    session: Session, process_id: UUID, input_digest: str, force: bool
) -> SpecializedEvaluationRun | None:
    if force:
        return None
    return session.scalar(
        select(SpecializedEvaluationRun)
        .where(
            SpecializedEvaluationRun.process_id == process_id,
            SpecializedEvaluationRun.input_digest == input_digest,
            SpecializedEvaluationRun.status.in_(
                [
                    SpecializedEvaluationRunStatus.COMPLETED.value,
                    SpecializedEvaluationRunStatus.COMPLETED_WITH_WARNINGS.value,
                    SpecializedEvaluationRunStatus.PENDING.value,
                    SpecializedEvaluationRunStatus.PROCESSING.value,
                ]
            ),
        )
        .order_by(SpecializedEvaluationRun.created_at.desc())
        .limit(1)
    )


def _active_job(
    session: Session,
    process_id: UUID,
    normalization_run_id: UUID,
    company_id: UUID,
    snapshot_id: UUID,
    domain: str,
) -> SpecializedEvaluationJob | None:
    return session.scalar(
        select(SpecializedEvaluationJob)
        .where(
            SpecializedEvaluationJob.process_id == process_id,
            SpecializedEvaluationJob.normalization_run_id == normalization_run_id,
            SpecializedEvaluationJob.company_id == company_id,
            SpecializedEvaluationJob.company_profile_snapshot_id == snapshot_id,
            SpecializedEvaluationJob.domain == domain,
            SpecializedEvaluationJob.status.in_(
                [
                    SpecializedEvaluationJobStatus.PENDING.value,
                    SpecializedEvaluationJobStatus.PROCESSING.value,
                ]
            ),
        )
        .limit(1)
    )


def _run_or_404(session: Session, process_id: UUID, run_id: UUID) -> SpecializedEvaluationRun:
    run = session.get(SpecializedEvaluationRun, run_id)
    if run is None or run.process_id != process_id:
        raise _domain_error(
            SpecializedErrorCode.SPECIALIZED_EVALUATION_NOT_FOUND,
            "La evaluacion especializada no existe para ese proceso.",
            HTTPStatus.NOT_FOUND,
        )
    return run


def _result_or_404(
    session: Session, process_id: UUID, run_id: UUID, result_id: UUID
) -> SpecializedEvaluationResult:
    _run_or_404(session, process_id, run_id)
    result = session.get(SpecializedEvaluationResult, result_id)
    if result is None or result.run_id != run_id:
        raise _domain_error(
            SpecializedErrorCode.SPECIALIZED_RESULT_NOT_FOUND,
            "El resultado especializado no existe.",
            HTTPStatus.NOT_FOUND,
        )
    return result


def _requirement_or_404(session: Session, process_id: UUID, requirement_id: UUID) -> Requirement:
    requirement = session.get(Requirement, requirement_id)
    if requirement is None or requirement.process_id != process_id:
        raise _domain_error(
            SpecializedErrorCode.SPECIALIZED_REQUIREMENTS_NOT_FOUND,
            "El requisito no existe para ese proceso.",
            HTTPStatus.NOT_FOUND,
        )
    return requirement


def _domain_for_category(category: str) -> str:
    for domain in supported_domains():
        if category in categories_for_domain(domain):
            return domain
    return SpecializedEvaluationDomain.LEGAL.value


def _manual_mapping_status(values: dict[str, Any]) -> str:
    if values.get("rule_type") and values.get("operator"):
        return SpecializedRuleMappingStatus.MAPPED.value
    return SpecializedRuleMappingStatus.AMBIGUOUS.value


def job_summary(job: SpecializedEvaluationJob) -> SpecializedEvaluationJobSummary:
    return SpecializedEvaluationJobSummary(
        id=job.id,
        process_id=job.process_id,
        normalization_run_id=job.normalization_run_id,
        company_id=job.company_id,
        company_profile_snapshot_id=job.company_profile_snapshot_id,
        domain=SpecializedEvaluationDomain(job.domain),
        status=SpecializedEvaluationJobStatus(job.status),
        attempt_count=job.attempt_count,
        max_attempts=job.max_attempts,
        force=job.force,
        last_error_code=job.last_error_code,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def run_summary(run: SpecializedEvaluationRun):
    return {
        "id": run.id,
        "job_id": run.job_id,
        "process_id": run.process_id,
        "normalization_run_id": run.normalization_run_id,
        "company_id": run.company_id,
        "company_profile_snapshot_id": run.company_profile_snapshot_id,
        "domain": SpecializedEvaluationDomain(run.domain),
        "status": SpecializedEvaluationRunStatus(run.status),
        "input_digest": run.input_digest,
        "rule_version": run.rule_version,
        "requirement_count": run.requirement_count,
        "evaluated_count": run.evaluated_count,
        "complies_count": run.complies_count,
        "does_not_comply_count": run.does_not_comply_count,
        "partial_count": run.partial_count,
        "unknown_count": run.unknown_count,
        "not_applicable_count": run.not_applicable_count,
        "conflicting_count": run.conflicting_count,
        "warning_count": run.warning_count,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
        "error_code": run.error_code,
        "error_message": run.error_message,
        "created_at": run.created_at,
        "updated_at": run.updated_at,
    }


def run_detail(session: Session, run: SpecializedEvaluationRun) -> SpecializedEvaluationRunDetail:
    rules = session.scalars(
        select(SpecializedRequirementRule)
        .where(SpecializedRequirementRule.normalization_run_id == run.normalization_run_id)
        .where(SpecializedRequirementRule.domain == run.domain)
        .order_by(SpecializedRequirementRule.created_at.asc())
    ).all()
    results = session.scalars(
        select(SpecializedEvaluationResult)
        .where(SpecializedEvaluationResult.run_id == run.id)
        .order_by(SpecializedEvaluationResult.created_at.asc())
    ).all()
    events = session.scalars(
        select(SpecializedEvaluationEvent)
        .where(SpecializedEvaluationEvent.run_id == run.id)
        .order_by(SpecializedEvaluationEvent.created_at.asc())
    ).all()
    job = session.get(SpecializedEvaluationJob, run.job_id)
    return SpecializedEvaluationRunDetail(
        **run_summary(run),
        input_manifest=run.input_manifest or {},
        job=job_summary(job) if job is not None else None,
        rules=[rule_to_contract(rule) for rule in rules],
        results=[result_contract(result) for result in results],
        events=[
            {
                "event_type": event.event_type,
                "summary": event.summary,
                "details": event.details,
                "created_at": event.created_at.isoformat(),
            }
            for event in events
        ],
    )


def rule_to_contract(rule: SpecializedRequirementRule) -> SpecializedRequirementRuleContract:
    return SpecializedRequirementRuleContract(
        id=rule.id,
        requirement_id=rule.requirement_id,
        normalization_run_id=rule.normalization_run_id,
        domain=SpecializedEvaluationDomain(rule.domain),
        rule_type=rule.rule_type,
        subject=rule.subject,
        operator=rule.operator,
        expected_value=rule.expected_value,
        expected_min_value=rule.expected_min_value,
        expected_max_value=rule.expected_max_value,
        unit=rule.unit,
        currency=rule.currency,
        period_policy=rule.period_policy,
        condition_group=rule.condition_group or {},
        source_basis=rule.source_basis,
        mapping_status=rule.mapping_status,
        mapping_warnings=list(rule.mapping_warnings or []),
        requires_human_review=rule.requires_human_review,
        manual_override_payload=rule.manual_override_payload or {},
        version=rule.version,
        is_manual_override=rule.is_manual_override,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


def rule_values(rule: SpecializedRequirementRule) -> dict[str, Any]:
    return {
        "requirement_id": rule.requirement_id,
        "normalization_run_id": rule.normalization_run_id,
        "domain": rule.domain,
        "rule_type": rule.rule_type,
        "subject": rule.subject,
        "operator": rule.operator,
        "expected_value": rule.expected_value,
        "expected_min_value": rule.expected_min_value,
        "expected_max_value": rule.expected_max_value,
        "unit": rule.unit,
        "currency": rule.currency,
        "period_policy": rule.period_policy,
        "condition_group": rule.condition_group or {},
        "source_basis": rule.source_basis,
        "mapping_status": rule.mapping_status,
        "mapping_warnings": list(rule.mapping_warnings or []),
        "requires_human_review": rule.requires_human_review,
        "manual_override_payload": rule.manual_override_payload or {},
        "version": rule.version,
        "is_manual_override": rule.is_manual_override,
    }


def result_contract(result: SpecializedEvaluationResult):
    return {
        "id": result.id,
        "run_id": result.run_id,
        "requirement_id": result.requirement_id,
        "specialized_rule_id": result.specialized_rule_id,
        "domain": SpecializedEvaluationDomain(result.domain),
        "status": SpecializedEvaluationResultStatus(result.status),
        "rule_type": result.rule_type,
        "subject": result.subject,
        "operator": result.operator,
        "expected_value": result.expected_value,
        "actual_value": result.actual_value,
        "unit": result.unit,
        "source_record_type": result.source_record_type,
        "source_record_id": result.source_record_id,
        "explanation_code": result.explanation_code,
        "explanation_parameters": result.explanation_parameters or {},
        "requires_human_review": result.requires_human_review,
        "review_status": SpecializedEvaluationReviewStatus(result.review_status),
        "reviewed_status": (
            SpecializedEvaluationResultStatus(result.reviewed_status)
            if result.reviewed_status
            else None
        ),
        "review_notes": result.review_notes,
        "created_at": result.created_at,
        "updated_at": result.updated_at,
    }


def result_detail(session: Session, result: SpecializedEvaluationResult):
    evidence = session.scalars(
        select(SpecializedEvaluationEvidence)
        .where(SpecializedEvaluationEvidence.result_id == result.id)
        .order_by(SpecializedEvaluationEvidence.created_at.asc())
    ).all()
    reviews = session.scalars(
        select(SpecializedEvaluationReview)
        .where(SpecializedEvaluationReview.result_id == result.id)
        .order_by(SpecializedEvaluationReview.created_at.asc())
    ).all()
    rule = session.get(SpecializedRequirementRule, result.specialized_rule_id)
    return SpecializedEvaluationResultDetail(
        **result_contract(result),
        rule=rule_to_contract(rule) if rule is not None else None,
        evidence=[
            {
                "id": item.id,
                "result_id": item.result_id,
                "evidence_type": item.evidence_type,
                "company_evidence_link_id": item.company_evidence_link_id,
                "company_evidence_document_id": item.company_evidence_document_id,
                "requirement_evidence_id": item.requirement_evidence_id,
                "extracted_segment_id": item.extracted_segment_id,
                "quoted_text": item.quoted_text,
                "source_location": item.source_location or {},
                "validation_status": item.validation_status,
                "created_at": item.created_at,
            }
            for item in evidence
        ],
        reviews=[
            {
                "id": item.id,
                "action": item.action,
                "original_status": item.original_status,
                "reviewed_status": item.reviewed_status,
                "reason": item.reason,
                "reviewed_at": item.reviewed_at.isoformat(),
            }
            for item in reviews
        ],
    )


def _add_event(
    session: Session,
    *,
    job: SpecializedEvaluationJob | None,
    run: SpecializedEvaluationRun | None,
    event_type: str,
    summary: str,
    details: dict[str, Any],
) -> None:
    session.add(
        SpecializedEvaluationEvent(
            id=uuid4(),
            job_id=job.id if job is not None else None,
            run_id=run.id if run is not None else None,
            process_id=job.process_id if job is not None else run.process_id,
            company_id=job.company_id if job is not None else run.company_id,
            domain=job.domain if job is not None else run.domain,
            event_type=event_type,
            summary=summary,
            details=details,
        )
    )


def _domain_error(code: SpecializedErrorCode, message: str, status: HTTPStatus) -> DomainError:
    return DomainError(code, message, status_code=status)
