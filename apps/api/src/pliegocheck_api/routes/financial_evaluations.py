# mypy: ignore-errors
"""Endpoints de evaluacion financiera inicial."""

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
from pliegocheck_api.financial import (
    FORMULA_VERSIONS,
    RULE_MAPPING_VERSION,
    build_input_manifest,
    map_financial_requirement,
    stable_digest,
)
from pliegocheck_api.models import (
    CompanyProfile,
    CompanyProfileSnapshot,
    FinancialEvaluationEvent,
    FinancialEvaluationJob,
    FinancialEvaluationResult,
    FinancialEvaluationResultReview,
    FinancialEvaluationRun,
    FinancialMetricCalculation,
    FinancialRequirementRule,
    Process,
    Requirement,
    RequirementNormalizationRun,
)
from pliegocheck_schemas import (
    CompanySnapshotStatus,
    FinancialErrorCode,
    FinancialEvaluationJobStatus,
    FinancialEvaluationList,
    FinancialEvaluationQueueResponse,
    FinancialEvaluationRequest,
    FinancialEvaluationResultDetail,
    FinancialEvaluationResultList,
    FinancialEvaluationResultReviewRequest,
    FinancialEvaluationResultStatus,
    FinancialEvaluationReviewStatus,
    FinancialEvaluationRunDetail,
    FinancialEvaluationRunStatus,
    FinancialRequirementRuleUpdate,
    FinancialRuleMappingStatus,
    FinancialRuleSourceBasis,
    NormalizationProvider,
    RequirementCategory,
    RequirementNormalizationStatus,
)
from pliegocheck_schemas import (
    FinancialMetricCalculation as FinancialMetricCalculationContract,
)
from pliegocheck_schemas import (
    FinancialRequirementRule as FinancialRequirementRuleContract,
)

router = APIRouter(prefix="/processes", tags=["financial-evaluations"])
SessionDep = Annotated[Session, Depends(get_session)]
LimitParam = Annotated[int, Query(ge=1, le=100)]
OffsetParam = Annotated[int, Query(ge=0)]


@router.post(
    "/{process_id}/financial-evaluations",
    response_model=FinancialEvaluationQueueResponse,
    status_code=HTTPStatus.ACCEPTED,
)
def create_financial_evaluation(
    process_id: UUID,
    payload: FinancialEvaluationRequest,
    response: Response,
    session: SessionDep,
) -> FinancialEvaluationQueueResponse:
    request = payload
    process = _process_or_404(session, process_id)
    normalization_run = _normalization_run_or_404(session, process_id, request.normalization_run_id)
    _ensure_normalization_completed(normalization_run)
    company = _company_or_404(session, request.company_id)
    snapshot = _snapshot_or_404(
        session,
        company_id=company.id,
        snapshot_id=request.company_profile_snapshot_id,
    )
    _ensure_snapshot_published(snapshot)
    requirements = _financial_requirements(session, process_id, normalization_run.id)
    if not requirements:
        raise DomainError(
            FinancialErrorCode.FINANCIAL_REQUIREMENTS_NOT_FOUND,
            "La normalizacion no contiene requisitos financieros activos.",
            status_code=HTTPStatus.CONFLICT,
        )
    rules = _ensure_rules(session, requirements, process)
    manifest = build_input_manifest(
        process=process,
        normalization_run=normalization_run,
        snapshot=snapshot,
        requirements=requirements,
    )
    manifest["financial_rule_versions"] = [
        {
            "requirement_id": str(rule.requirement_id),
            "rule_id": str(rule.id),
            "version": rule.version,
        }
        for rule in rules
    ]
    input_digest = stable_digest(manifest)

    existing = _existing_run(session, process_id, input_digest, request.force)
    if existing is not None:
        job = session.get(FinancialEvaluationJob, existing.job_id)
        if job is not None:
            response.status_code = HTTPStatus.ACCEPTED
            return FinancialEvaluationQueueResponse(
                job=job_to_summary(job), run=run_to_summary(existing)
            )

    job = FinancialEvaluationJob(
        id=uuid4(),
        process_id=process_id,
        normalization_run_id=normalization_run.id,
        company_id=company.id,
        company_profile_snapshot_id=snapshot.id,
        status=FinancialEvaluationJobStatus.PENDING.value,
        priority=100,
        max_attempts=3,
        available_at=datetime.now(UTC),
        force=request.force,
    )
    session.add(job)
    session.flush()
    run = FinancialEvaluationRun(
        id=uuid4(),
        job_id=job.id,
        process_id=process_id,
        normalization_run_id=normalization_run.id,
        company_id=company.id,
        company_profile_snapshot_id=snapshot.id,
        status=FinancialEvaluationRunStatus.PENDING.value,
        input_manifest=manifest,
        input_digest=input_digest,
        rule_version=RULE_MAPPING_VERSION,
        formula_versions=FORMULA_VERSIONS,
        requirement_count=len(requirements),
        evaluated_count=0,
        complies_count=0,
        does_not_comply_count=0,
        partial_count=0,
        unknown_count=0,
        not_applicable_count=0,
        conflicting_count=0,
        warning_count=0,
    )
    session.add(run)
    session.flush()
    job.run_id = run.id
    _add_event(
        session,
        job=job,
        run=run,
        event_type="FINANCIAL_EVALUATION_QUEUED",
        summary="Evaluacion financiera encolada.",
        details={"input_digest": input_digest, "requirement_count": len(requirements)},
    )
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        active = _active_job(session, process_id, normalization_run.id, company.id, snapshot.id)
        if active is not None and active.run_id is not None:
            active_run = session.get(FinancialEvaluationRun, active.run_id)
            if active_run is not None:
                return FinancialEvaluationQueueResponse(
                    job=job_to_summary(active),
                    run=run_to_summary(active_run),
                )
        raise DomainError(
            FinancialErrorCode.FINANCIAL_EVALUATION_ALREADY_QUEUED,
            "Ya existe una evaluacion financiera activa para esas entradas.",
            status_code=HTTPStatus.CONFLICT,
        ) from exc
    except SQLAlchemyError as exc:
        session.rollback()
        raise DomainError(
            FinancialErrorCode.DATABASE_ERROR,
            "No fue posible encolar la evaluacion financiera.",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        ) from exc
    session.refresh(job)
    session.refresh(run)
    return FinancialEvaluationQueueResponse(job=job_to_summary(job), run=run_to_summary(run))


@router.get("/{process_id}/financial-evaluations", response_model=FinancialEvaluationList)
def list_financial_evaluations(
    process_id: UUID,
    session: SessionDep,
    limit: LimitParam = 20,
    offset: OffsetParam = 0,
) -> FinancialEvaluationList:
    _process_or_404(session, process_id)
    total = (
        session.scalar(
            select(func.count())
            .select_from(FinancialEvaluationRun)
            .where(FinancialEvaluationRun.process_id == process_id)
        )
        or 0
    )
    runs = session.scalars(
        select(FinancialEvaluationRun)
        .where(FinancialEvaluationRun.process_id == process_id)
        .order_by(FinancialEvaluationRun.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return FinancialEvaluationList(
        items=[run_to_summary(run) for run in runs],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{process_id}/financial-evaluations/{run_id}",
    response_model=FinancialEvaluationRunDetail,
)
def get_financial_evaluation(
    process_id: UUID, run_id: UUID, session: SessionDep
) -> FinancialEvaluationRunDetail:
    run = _run_or_404(session, process_id, run_id)
    return run_to_detail(session, run)


@router.post(
    "/{process_id}/financial-evaluations/{run_id}/retry",
    response_model=FinancialEvaluationQueueResponse,
    status_code=HTTPStatus.ACCEPTED,
)
def retry_financial_evaluation(
    process_id: UUID,
    run_id: UUID,
    session: SessionDep,
) -> FinancialEvaluationQueueResponse:
    run = _run_or_404(session, process_id, run_id)
    if run.status != FinancialEvaluationRunStatus.FAILED.value:
        raise DomainError(
            FinancialErrorCode.FINANCIAL_EVALUATION_ALREADY_COMPLETED,
            "Solo las evaluaciones financieras fallidas pueden reintentarse.",
            status_code=HTTPStatus.CONFLICT,
        )
    active = _active_job(
        session,
        process_id,
        run.normalization_run_id,
        run.company_id,
        run.company_profile_snapshot_id,
    )
    if active is not None and active.run_id is not None:
        active_run = session.get(FinancialEvaluationRun, active.run_id)
        if active_run is not None:
            return FinancialEvaluationQueueResponse(
                job=job_to_summary(active), run=run_to_summary(active_run)
            )
    job = FinancialEvaluationJob(
        id=uuid4(),
        process_id=process_id,
        normalization_run_id=run.normalization_run_id,
        company_id=run.company_id,
        company_profile_snapshot_id=run.company_profile_snapshot_id,
        run_id=run.id,
        status=FinancialEvaluationJobStatus.PENDING.value,
        priority=100,
        max_attempts=3,
        available_at=datetime.now(UTC),
        force=True,
    )
    session.add(job)
    run.job_id = job.id
    run.status = FinancialEvaluationRunStatus.PENDING.value
    run.error_code = None
    run.error_message = None
    _add_event(
        session,
        job=job,
        run=run,
        event_type="FINANCIAL_EVALUATION_RETRIED",
        summary="Evaluacion financiera reenviada a la cola.",
        details={},
    )
    session.commit()
    session.refresh(job)
    session.refresh(run)
    return FinancialEvaluationQueueResponse(job=job_to_summary(job), run=run_to_summary(run))


@router.get(
    "/{process_id}/financial-evaluations/{run_id}/results",
    response_model=FinancialEvaluationResultList,
)
def list_financial_evaluation_results(
    process_id: UUID,
    run_id: UUID,
    session: SessionDep,
    limit: LimitParam = 100,
    offset: OffsetParam = 0,
) -> FinancialEvaluationResultList:
    _run_or_404(session, process_id, run_id)
    total = (
        session.scalar(
            select(func.count())
            .select_from(FinancialEvaluationResult)
            .where(FinancialEvaluationResult.run_id == run_id)
        )
        or 0
    )
    results = session.scalars(
        select(FinancialEvaluationResult)
        .where(FinancialEvaluationResult.run_id == run_id)
        .order_by(FinancialEvaluationResult.created_at.asc())
        .limit(limit)
        .offset(offset)
    ).all()
    return FinancialEvaluationResultList(
        items=[result_to_contract(result) for result in results],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{process_id}/financial-evaluations/{run_id}/results/{result_id}",
    response_model=FinancialEvaluationResultDetail,
)
def get_financial_evaluation_result(
    process_id: UUID,
    run_id: UUID,
    result_id: UUID,
    session: SessionDep,
) -> FinancialEvaluationResultDetail:
    result = _result_or_404(session, process_id, run_id, result_id)
    return result_to_detail(session, result)


@router.post(
    "/{process_id}/financial-evaluations/{run_id}/results/{result_id}/review",
    response_model=FinancialEvaluationResultDetail,
)
def review_financial_evaluation_result(
    process_id: UUID,
    run_id: UUID,
    result_id: UUID,
    payload: FinancialEvaluationResultReviewRequest,
    session: SessionDep,
) -> FinancialEvaluationResultDetail:
    result = _result_or_404(session, process_id, run_id, result_id)
    now = datetime.now(UTC)
    review = FinancialEvaluationResultReview(
        id=uuid4(),
        result_id=result.id,
        review_status=payload.review_status.value,
        override_status=payload.override_result.value if payload.override_result else None,
        override_reason=payload.override_reason,
        original_status=result.status,
        reviewer="local-user",
        review_notes=payload.review_notes,
        reviewed_at=now,
    )
    session.add(review)
    result.review_status = payload.review_status.value
    result.reviewed_status = (
        payload.override_result.value if payload.override_result else result.status
    )
    result.review_notes = payload.override_reason or payload.review_notes
    result.reviewed_at = now
    _add_event(
        session,
        job=None,
        run=session.get(FinancialEvaluationRun, run_id),
        event_type="FINANCIAL_RESULT_REVIEWED",
        summary="Resultado financiero revisado manualmente.",
        details={
            "result_id": str(result.id),
            "review_status": payload.review_status.value,
            "override_status": review.override_status,
        },
    )
    session.commit()
    session.refresh(result)
    return result_to_detail(session, result)


@router.get(
    "/{process_id}/financial-requirements/{requirement_id}/rule",
    response_model=FinancialRequirementRuleContract,
)
def get_financial_requirement_rule(
    process_id: UUID,
    requirement_id: UUID,
    session: SessionDep,
) -> FinancialRequirementRuleContract:
    requirement = _requirement_or_404(session, process_id, requirement_id)
    rule = _latest_rule(session, requirement.id)
    if rule is None:
        rule = _create_rule(session, requirement, _process_or_404(session, process_id))
        session.commit()
        session.refresh(rule)
    return rule_to_contract(rule)


@router.patch(
    "/{process_id}/financial-requirements/{requirement_id}/rule",
    response_model=FinancialRequirementRuleContract,
)
def update_financial_requirement_rule(
    process_id: UUID,
    requirement_id: UUID,
    payload: FinancialRequirementRuleUpdate,
    session: SessionDep,
) -> FinancialRequirementRuleContract:
    requirement = _requirement_or_404(session, process_id, requirement_id)
    if not payload.override_reason:
        raise DomainError(
            FinancialErrorCode.INVALID_FINANCIAL_OVERRIDE,
            "override_reason es obligatorio para modificar una regla financiera.",
            status_code=HTTPStatus.BAD_REQUEST,
        )
    latest = _latest_rule(session, requirement.id)
    if latest is None:
        latest = _create_rule(session, requirement, _process_or_404(session, process_id))
        session.flush()
    values = _rule_values(latest)
    updates = payload.model_dump(exclude_unset=True)
    override_reason = updates.pop("override_reason", None)
    for key, value in updates.items():
        values[key] = value.value if hasattr(value, "value") else value
    values["source_basis"] = FinancialRuleSourceBasis.MANUAL_OVERRIDE.value
    values["mapping_status"] = _manual_rule_mapping_status(values)
    values["requires_human_review"] = True
    values["version"] = latest.version + 1
    values["is_manual_override"] = True
    values["override_reason"] = override_reason
    rule = FinancialRequirementRule(id=uuid4(), **values)
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule_to_contract(rule)


def _process_or_404(session: Session, process_id: UUID) -> Process:
    process = session.get(Process, process_id)
    if process is None:
        raise DomainError(
            FinancialErrorCode.FINANCIAL_EVALUATION_INPUT_NOT_READY,
            "El proceso no existe.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return process


def _company_or_404(session: Session, company_id: UUID) -> CompanyProfile:
    company = session.get(CompanyProfile, company_id)
    if company is None:
        raise DomainError(
            FinancialErrorCode.COMPANY_SNAPSHOT_NOT_FOUND,
            "La empresa no existe.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return company


def _normalization_run_or_404(
    session: Session, process_id: UUID, run_id: UUID
) -> RequirementNormalizationRun:
    run = session.scalar(
        select(RequirementNormalizationRun).where(
            RequirementNormalizationRun.id == run_id,
            RequirementNormalizationRun.process_id == process_id,
        )
    )
    if run is None:
        raise DomainError(
            FinancialErrorCode.FINANCIAL_EVALUATION_INPUT_NOT_READY,
            "La normalizacion no existe para este proceso.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return run


def _ensure_normalization_completed(run: RequirementNormalizationRun) -> None:
    if run.status not in {
        RequirementNormalizationStatus.COMPLETED.value,
        RequirementNormalizationStatus.COMPLETED_WITH_WARNINGS.value,
    }:
        raise DomainError(
            FinancialErrorCode.FINANCIAL_EVALUATION_INPUT_NOT_READY,
            "La normalizacion debe estar completada antes de evaluar requisitos financieros.",
            status_code=HTTPStatus.CONFLICT,
        )
    if run.provider not in {NormalizationProvider.OPENAI.value, NormalizationProvider.FAKE.value}:
        raise DomainError(
            FinancialErrorCode.FINANCIAL_EVALUATION_INPUT_NOT_READY,
            "La normalizacion no tiene proveedor valido.",
            status_code=HTTPStatus.CONFLICT,
        )


def _snapshot_or_404(
    session: Session, *, company_id: UUID, snapshot_id: UUID
) -> CompanyProfileSnapshot:
    snapshot = session.scalar(
        select(CompanyProfileSnapshot).where(
            CompanyProfileSnapshot.id == snapshot_id,
            CompanyProfileSnapshot.company_id == company_id,
        )
    )
    if snapshot is None:
        raise DomainError(
            FinancialErrorCode.COMPANY_SNAPSHOT_NOT_FOUND,
            "El snapshot de empresa no existe.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return snapshot


def _ensure_snapshot_published(snapshot: CompanyProfileSnapshot) -> None:
    if snapshot.status != CompanySnapshotStatus.PUBLISHED.value:
        raise DomainError(
            FinancialErrorCode.COMPANY_SNAPSHOT_NOT_PUBLISHED,
            "La evaluacion financiera exige un snapshot publicado.",
            status_code=HTTPStatus.CONFLICT,
        )


def _financial_requirements(
    session: Session, process_id: UUID, normalization_run_id: UUID
) -> list[Requirement]:
    return list(
        session.scalars(
            select(Requirement)
            .where(
                Requirement.process_id == process_id,
                Requirement.normalization_run_id == normalization_run_id,
                Requirement.category == RequirementCategory.FINANCIAL.value,
                Requirement.is_active.is_(True),
            )
            .order_by(Requirement.created_at.asc(), Requirement.id.asc())
        ).all()
    )


def _ensure_rules(
    session: Session, requirements: list[Requirement], process: Process
) -> list[FinancialRequirementRule]:
    rules = []
    for requirement in requirements:
        rule = _latest_rule(session, requirement.id)
        if rule is None:
            rule = _create_rule(session, requirement, process)
        rules.append(rule)
    session.flush()
    return rules


def _create_rule(
    session: Session, requirement: Requirement, process: Process
) -> FinancialRequirementRule:
    payload = map_financial_requirement(requirement, process)
    rule = FinancialRequirementRule(id=uuid4(), **payload)
    session.add(rule)
    return rule


def _latest_rule(session: Session, requirement_id: UUID) -> FinancialRequirementRule | None:
    return session.scalar(
        select(FinancialRequirementRule)
        .where(FinancialRequirementRule.requirement_id == requirement_id)
        .order_by(FinancialRequirementRule.version.desc())
        .limit(1)
    )


def _existing_run(
    session: Session, process_id: UUID, input_digest: str, force: bool
) -> FinancialEvaluationRun | None:
    if force:
        return None
    return session.scalar(
        select(FinancialEvaluationRun)
        .where(
            FinancialEvaluationRun.process_id == process_id,
            FinancialEvaluationRun.input_digest == input_digest,
            FinancialEvaluationRun.status.in_(
                [
                    FinancialEvaluationRunStatus.PENDING.value,
                    FinancialEvaluationRunStatus.PROCESSING.value,
                    FinancialEvaluationRunStatus.COMPLETED.value,
                    FinancialEvaluationRunStatus.COMPLETED_WITH_WARNINGS.value,
                ]
            ),
        )
        .order_by(FinancialEvaluationRun.created_at.desc())
        .limit(1)
    )


def _active_job(
    session: Session,
    process_id: UUID,
    normalization_run_id: UUID,
    company_id: UUID,
    snapshot_id: UUID,
) -> FinancialEvaluationJob | None:
    return session.scalar(
        select(FinancialEvaluationJob)
        .where(
            FinancialEvaluationJob.process_id == process_id,
            FinancialEvaluationJob.normalization_run_id == normalization_run_id,
            FinancialEvaluationJob.company_id == company_id,
            FinancialEvaluationJob.company_profile_snapshot_id == snapshot_id,
            FinancialEvaluationJob.status.in_(
                [
                    FinancialEvaluationJobStatus.PENDING.value,
                    FinancialEvaluationJobStatus.PROCESSING.value,
                ]
            ),
        )
        .order_by(FinancialEvaluationJob.created_at.asc())
        .limit(1)
    )


def _run_or_404(session: Session, process_id: UUID, run_id: UUID) -> FinancialEvaluationRun:
    run = session.scalar(
        select(FinancialEvaluationRun).where(
            FinancialEvaluationRun.id == run_id,
            FinancialEvaluationRun.process_id == process_id,
        )
    )
    if run is None:
        raise DomainError(
            FinancialErrorCode.FINANCIAL_EVALUATION_NOT_FOUND,
            "La evaluacion financiera no existe para este proceso.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return run


def _result_or_404(
    session: Session, process_id: UUID, run_id: UUID, result_id: UUID
) -> FinancialEvaluationResult:
    _run_or_404(session, process_id, run_id)
    result = session.scalar(
        select(FinancialEvaluationResult).where(
            FinancialEvaluationResult.id == result_id,
            FinancialEvaluationResult.run_id == run_id,
        )
    )
    if result is None:
        raise DomainError(
            FinancialErrorCode.FINANCIAL_EVALUATION_NOT_FOUND,
            "El resultado financiero no existe para esta evaluacion.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return result


def _requirement_or_404(session: Session, process_id: UUID, requirement_id: UUID) -> Requirement:
    requirement = session.scalar(
        select(Requirement).where(
            Requirement.id == requirement_id,
            Requirement.process_id == process_id,
            Requirement.category == RequirementCategory.FINANCIAL.value,
        )
    )
    if requirement is None:
        raise DomainError(
            FinancialErrorCode.FINANCIAL_REQUIREMENTS_NOT_FOUND,
            "El requisito financiero no existe para este proceso.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return requirement


def _add_event(
    session: Session,
    *,
    job: FinancialEvaluationJob | None,
    run: FinancialEvaluationRun | None,
    event_type: str,
    summary: str,
    details: dict[str, Any],
) -> None:
    process_id = run.process_id if run is not None else job.process_id
    company_id = run.company_id if run is not None else job.company_id
    session.add(
        FinancialEvaluationEvent(
            id=uuid4(),
            job_id=job.id if job is not None else None,
            run_id=run.id if run is not None else None,
            process_id=process_id,
            company_id=company_id,
            event_type=event_type,
            summary=summary,
            details=details,
        )
    )


def _rule_values(rule: FinancialRequirementRule) -> dict[str, Any]:
    return {
        "requirement_id": rule.requirement_id,
        "normalization_run_id": rule.normalization_run_id,
        "rule_type": rule.rule_type,
        "metric_type": rule.metric_type,
        "operator": rule.operator,
        "required_value": rule.required_value,
        "required_min_value": rule.required_min_value,
        "required_max_value": rule.required_max_value,
        "unit": rule.unit,
        "currency": rule.currency,
        "period_policy": rule.period_policy,
        "period_year": rule.period_year,
        "condition_group": rule.condition_group,
        "source_basis": rule.source_basis,
        "mapping_status": rule.mapping_status,
        "mapping_warnings": rule.mapping_warnings,
        "requires_human_review": rule.requires_human_review,
        "version": rule.version,
        "is_manual_override": rule.is_manual_override,
        "override_reason": rule.override_reason,
    }


def _manual_rule_mapping_status(values: dict[str, Any]) -> str:
    if (
        values.get("metric_type")
        and values.get("operator")
        and (
            values.get("required_value") is not None
            or values.get("required_min_value") is not None
            or values.get("required_max_value") is not None
        )
    ):
        return FinancialRuleMappingStatus.MAPPED.value
    return FinancialRuleMappingStatus.AMBIGUOUS.value


def job_to_summary(job: FinancialEvaluationJob):
    from pliegocheck_schemas import FinancialEvaluationJobSummary

    return FinancialEvaluationJobSummary(
        id=job.id,
        process_id=job.process_id,
        normalization_run_id=job.normalization_run_id,
        company_id=job.company_id,
        company_profile_snapshot_id=job.company_profile_snapshot_id,
        status=FinancialEvaluationJobStatus(job.status),
        attempt_count=job.attempt_count,
        max_attempts=job.max_attempts,
        force=job.force,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def run_to_summary(run: FinancialEvaluationRun):
    from pliegocheck_schemas import FinancialEvaluationRunSummary

    return FinancialEvaluationRunSummary(
        id=run.id,
        job_id=run.job_id,
        process_id=run.process_id,
        normalization_run_id=run.normalization_run_id,
        company_id=run.company_id,
        company_profile_snapshot_id=run.company_profile_snapshot_id,
        status=FinancialEvaluationRunStatus(run.status),
        input_digest=run.input_digest,
        rule_version=run.rule_version,
        requirement_count=run.requirement_count,
        evaluated_count=run.evaluated_count,
        complies_count=run.complies_count,
        does_not_comply_count=run.does_not_comply_count,
        partial_count=run.partial_count,
        unknown_count=run.unknown_count,
        not_applicable_count=run.not_applicable_count,
        conflicting_count=run.conflicting_count,
        warning_count=run.warning_count,
        started_at=run.started_at,
        finished_at=run.finished_at,
        error_code=run.error_code,
        error_message=run.error_message,
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


def run_to_detail(session: Session, run: FinancialEvaluationRun) -> FinancialEvaluationRunDetail:
    job = session.get(FinancialEvaluationJob, run.job_id)
    rules = session.scalars(
        select(FinancialRequirementRule)
        .where(FinancialRequirementRule.normalization_run_id == run.normalization_run_id)
        .order_by(
            FinancialRequirementRule.requirement_id.asc(),
            FinancialRequirementRule.version.asc(),
        )
    ).all()
    calculations = session.scalars(
        select(FinancialMetricCalculation)
        .where(FinancialMetricCalculation.run_id == run.id)
        .order_by(FinancialMetricCalculation.created_at.asc())
    ).all()
    results = session.scalars(
        select(FinancialEvaluationResult)
        .where(FinancialEvaluationResult.run_id == run.id)
        .order_by(FinancialEvaluationResult.created_at.asc())
    ).all()
    events = session.scalars(
        select(FinancialEvaluationEvent)
        .where(FinancialEvaluationEvent.run_id == run.id)
        .order_by(FinancialEvaluationEvent.created_at.asc())
    ).all()
    return FinancialEvaluationRunDetail(
        **run_to_summary(run).model_dump(),
        input_manifest=run.input_manifest,
        job=job_to_summary(job) if job is not None else None,
        rules=[rule_to_contract(rule) for rule in rules],
        calculations=[calculation_to_contract(item) for item in calculations],
        results=[result_to_contract(result) for result in results],
        events=[
            {
                "id": str(event.id),
                "event_type": event.event_type,
                "summary": event.summary,
                "details": event.details,
                "created_at": event.created_at.isoformat(),
            }
            for event in events
        ],
    )


def rule_to_contract(rule: FinancialRequirementRule) -> FinancialRequirementRuleContract:
    return FinancialRequirementRuleContract(
        id=rule.id,
        requirement_id=rule.requirement_id,
        normalization_run_id=rule.normalization_run_id,
        rule_type=rule.rule_type,
        metric_type=rule.metric_type,
        operator=rule.operator,
        required_value=rule.required_value,
        required_min_value=rule.required_min_value,
        required_max_value=rule.required_max_value,
        unit=rule.unit,
        currency=rule.currency,
        period_policy=rule.period_policy,
        period_year=rule.period_year,
        condition_group=rule.condition_group,
        source_basis=rule.source_basis,
        mapping_status=rule.mapping_status,
        mapping_warnings=rule.mapping_warnings,
        requires_human_review=rule.requires_human_review,
        version=rule.version,
        is_manual_override=rule.is_manual_override,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


def calculation_to_contract(
    calculation: FinancialMetricCalculation,
) -> FinancialMetricCalculationContract:
    return FinancialMetricCalculationContract(
        id=calculation.id,
        run_id=calculation.run_id,
        financial_period_id=calculation.financial_period_id,
        metric_type=calculation.metric_type,
        formula_name=calculation.formula_name,
        formula_version=calculation.formula_version,
        input_values=calculation.input_values,
        raw_result=calculation.raw_result,
        rounded_result=calculation.rounded_result,
        unit=calculation.unit,
        status=calculation.status,
        warning_codes=calculation.warning_codes,
        created_at=calculation.created_at,
    )


def result_to_contract(result: FinancialEvaluationResult):
    from pliegocheck_schemas import FinancialEvaluationResult as FinancialEvaluationResultContract

    return FinancialEvaluationResultContract(
        id=result.id,
        run_id=result.run_id,
        requirement_id=result.requirement_id,
        financial_rule_id=result.financial_rule_id,
        status=FinancialEvaluationResultStatus(result.status),
        metric_type=result.metric_type,
        operator=result.operator,
        required_value=result.required_value,
        required_min_value=result.required_min_value,
        required_max_value=result.required_max_value,
        required_unit=result.required_unit,
        actual_value=result.actual_value,
        actual_unit=result.actual_unit,
        currency=result.currency,
        financial_period_id=result.financial_period_id,
        calculation_id=result.calculation_id,
        explanation_code=result.explanation_code,
        explanation_parameters=result.explanation_parameters,
        requires_human_review=result.requires_human_review,
        review_status=FinancialEvaluationReviewStatus(result.review_status),
        reviewed_status=(
            FinancialEvaluationResultStatus(result.reviewed_status)
            if result.reviewed_status
            else None
        ),
        review_notes=result.review_notes,
        reviewed_at=result.reviewed_at,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


def result_to_detail(
    session: Session, result: FinancialEvaluationResult
) -> FinancialEvaluationResultDetail:
    requirement = session.get(Requirement, result.requirement_id)
    rule = (
        session.get(FinancialRequirementRule, result.financial_rule_id)
        if result.financial_rule_id
        else None
    )
    calculation = (
        session.get(FinancialMetricCalculation, result.calculation_id)
        if result.calculation_id
        else None
    )
    reviews = session.scalars(
        select(FinancialEvaluationResultReview)
        .where(FinancialEvaluationResultReview.result_id == result.id)
        .order_by(FinancialEvaluationResultReview.reviewed_at.asc())
    ).all()
    return FinancialEvaluationResultDetail(
        **result_to_contract(result).model_dump(),
        requirement={
            "id": str(requirement.id),
            "stable_key": requirement.stable_key,
            "description": requirement.description,
            "condition_text": requirement.condition_text,
        }
        if requirement is not None
        else {},
        rule=rule_to_contract(rule) if rule is not None else None,
        calculation=calculation_to_contract(calculation) if calculation is not None else None,
        metric_inputs=result.metric_inputs,
        evidence=result.evidence_refs,
        reviews=[
            {
                "id": str(review.id),
                "review_status": review.review_status,
                "override_status": review.override_status,
                "override_reason": review.override_reason,
                "original_status": review.original_status,
                "reviewer": review.reviewer,
                "review_notes": review.review_notes,
                "reviewed_at": review.reviewed_at.isoformat(),
            }
            for review in reviews
        ],
    )
