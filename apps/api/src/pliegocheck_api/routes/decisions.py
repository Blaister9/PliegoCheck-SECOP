# mypy: ignore-errors
"""Endpoints del motor deterministico de decision preliminar."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from http import HTTPStatus
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from pliegocheck_api.db import get_session
from pliegocheck_api.decision import DECISION_ENGINE_VERSION
from pliegocheck_api.decision.findings import (
    DEFAULT_ADAPTER_REGISTRY,
    applicability_for_requirement,
    domain_for_category,
)
from pliegocheck_api.decision.manifest import build_decision_manifest, stable_decision_digest
from pliegocheck_api.decision.policy import PolicyLoadError, load_active_policy
from pliegocheck_api.errors import DomainError
from pliegocheck_api.models import (
    CompanyProfile,
    CompanyProfileSnapshot,
    DecisionActionItemRecord,
    DecisionEvent,
    DecisionInputFindingSnapshot,
    DecisionJob,
    DecisionPolicyVersion,
    DecisionReview,
    DecisionRuleEvaluationRecord,
    DecisionRun,
    FinancialEvaluationResult,
    FinancialEvaluationRun,
    Process,
    Requirement,
    RequirementNormalizationRun,
    SpecializedEvaluationResult,
    SpecializedEvaluationRun,
)
from pliegocheck_schemas import (
    CompanySnapshotStatus,
    DecisionActionUpdateRequest,
    DecisionErrorCode,
    DecisionFindingApplicability,
    DecisionFindingOutcome,
    DecisionJobStatus,
    DecisionOutcome,
    DecisionQueueResponse,
    DecisionReadiness,
    DecisionReadinessCategory,
    DecisionRequest,
    DecisionReviewAction,
    DecisionReviewRequest,
    DecisionReviewResponse,
    DecisionRunList,
    DecisionRunStatus,
    FinancialEvaluationRunStatus,
    RequirementNormalizationStatus,
    SpecializedEvaluationRunStatus,
)
from pliegocheck_schemas import (
    DecisionActionItem as DecisionActionItemContract,
)
from pliegocheck_schemas import (
    DecisionInputFinding as DecisionInputFindingContract,
)
from pliegocheck_schemas import (
    DecisionJobSummary as DecisionJobSummaryContract,
)
from pliegocheck_schemas import (
    DecisionPolicySummary as DecisionPolicySummaryContract,
)
from pliegocheck_schemas import (
    DecisionReviewRecord as DecisionReviewRecordContract,
)
from pliegocheck_schemas import (
    DecisionRuleEvaluation as DecisionRuleEvaluationContract,
)
from pliegocheck_schemas import (
    DecisionRunDetail as DecisionRunDetailContract,
)
from pliegocheck_schemas import (
    DecisionRunSummary as DecisionRunSummaryContract,
)

logger = logging.getLogger("pliegocheck.decisions")

router = APIRouter(prefix="/processes", tags=["decisions"])
SessionDep = Annotated[Session, Depends(get_session)]
LimitParam = Annotated[int, Query(ge=1, le=100)]
OffsetParam = Annotated[int, Query(ge=0)]


@router.get("/{process_id}/decision-readiness", response_model=DecisionReadiness)
def decision_readiness(
    process_id: UUID,
    normalization_run_id: UUID,
    company_profile_snapshot_id: UUID,
    financial_evaluation_run_id: UUID,
    session: SessionDep,
) -> DecisionReadiness:
    """Diagnostico previo. No ejecuta el motor ni encola trabajos."""
    process = _process_or_404(session, process_id)
    input_errors: list[str] = []
    warnings: list[str] = []

    normalization_run = session.get(RequirementNormalizationRun, normalization_run_id)
    if normalization_run is None or normalization_run.process_id != process_id:
        input_errors.append(DecisionErrorCode.DECISION_INPUT_MISMATCH.value)
        normalization_run = None
    elif normalization_run.status not in {
        RequirementNormalizationStatus.COMPLETED.value,
        RequirementNormalizationStatus.COMPLETED_WITH_WARNINGS.value,
    }:
        input_errors.append(DecisionErrorCode.DECISION_NORMALIZATION_NOT_COMPLETED.value)

    snapshot = session.get(CompanyProfileSnapshot, company_profile_snapshot_id)
    if snapshot is None:
        input_errors.append(DecisionErrorCode.DECISION_INPUT_NOT_READY.value)
    elif snapshot.status != CompanySnapshotStatus.PUBLISHED.value:
        input_errors.append(DecisionErrorCode.DECISION_COMPANY_SNAPSHOT_NOT_PUBLISHED.value)

    financial_run = session.get(FinancialEvaluationRun, financial_evaluation_run_id)
    if financial_run is None or financial_run.process_id != process_id:
        input_errors.append(DecisionErrorCode.DECISION_INPUT_MISMATCH.value)
        financial_run = None
    else:
        if financial_run.status not in {
            FinancialEvaluationRunStatus.COMPLETED.value,
            FinancialEvaluationRunStatus.COMPLETED_WITH_WARNINGS.value,
        }:
            input_errors.append(DecisionErrorCode.DECISION_FINANCIAL_EVALUATION_NOT_COMPLETED.value)
        if (snapshot is not None and financial_run.company_profile_snapshot_id != snapshot.id) or (
            normalization_run is not None
            and financial_run.normalization_run_id != normalization_run.id
        ):
            input_errors.append(DecisionErrorCode.DECISION_INPUT_MISMATCH.value)

    policy_summary = None
    try:
        policy, _payload, content_hash = load_active_policy()
        policy_summary = DecisionPolicySummaryContract(
            policy_name=policy.policy_name,
            semantic_version=policy.semantic_version,
            content_sha256=content_hash,
            engine_version=DECISION_ENGINE_VERSION,
            is_active=True,
        )
    except PolicyLoadError as exc:
        input_errors.append(exc.code)

    categories: list[DecisionReadinessCategory] = []
    not_evaluated_mandatory = 0
    if normalization_run is not None:
        requirements = _active_requirements(session, process_id, normalization_run.id)
        available_domains = set(DEFAULT_ADAPTER_REGISTRY.available_domains())
        by_category: dict[str, list[Any]] = {}
        for requirement in requirements:
            by_category.setdefault(requirement.category, []).append(requirement)
        for category in sorted(by_category):
            items = by_category[category]
            mandatory_total = sum(
                1
                for requirement in items
                if applicability_for_requirement(requirement, DecisionFindingOutcome.UNKNOWN)
                == DecisionFindingApplicability.MANDATORY
            )
            adapter_available = domain_for_category(category) in available_domains
            if not adapter_available:
                not_evaluated_mandatory += mandatory_total
                if mandatory_total:
                    warnings.append(f"ADAPTER_NOT_AVAILABLE:{category}")
            categories.append(
                DecisionReadinessCategory(
                    category=category,
                    requirements_total=len(items),
                    mandatory_total=mandatory_total,
                    adapter_available=adapter_available,
                )
            )
        if financial_run is not None and snapshot is not None:
            financial_results = list(
                session.scalars(
                    select(FinancialEvaluationResult)
                    .where(FinancialEvaluationResult.run_id == financial_run.id)
                    .order_by(FinancialEvaluationResult.requirement_id.asc())
                ).all()
            )
            specialized_runs = list(
                session.scalars(
                    select(SpecializedEvaluationRun).where(
                        SpecializedEvaluationRun.process_id == process_id,
                        SpecializedEvaluationRun.normalization_run_id == normalization_run.id,
                        SpecializedEvaluationRun.company_id == financial_run.company_id,
                        SpecializedEvaluationRun.company_profile_snapshot_id == snapshot.id,
                        SpecializedEvaluationRun.status.in_(
                            [
                                SpecializedEvaluationRunStatus.COMPLETED.value,
                                SpecializedEvaluationRunStatus.COMPLETED_WITH_WARNINGS.value,
                            ]
                        ),
                    )
                ).all()
            )
            specialized_results: list[SpecializedEvaluationResult] = []
            if specialized_runs:
                specialized_results = list(
                    session.scalars(
                        select(SpecializedEvaluationResult)
                        .where(
                            SpecializedEvaluationResult.run_id.in_(
                                [specialized_run.id for specialized_run in specialized_runs]
                            )
                        )
                        .order_by(SpecializedEvaluationResult.requirement_id.asc())
                    ).all()
                )
            findings = DEFAULT_ADAPTER_REGISTRY.collect_all_findings(
                requirements=requirements,
                context={
                    "financial_results_by_requirement": {
                        result.requirement_id: result for result in financial_results
                    },
                    "financial_evaluation_run_id": financial_run.id,
                    "specialized_results_by_requirement": {
                        result.requirement_id: result for result in specialized_results
                    },
                },
            )
            not_evaluated_mandatory = sum(
                1
                for finding in findings
                if finding.applicability == DecisionFindingApplicability.MANDATORY
                and finding.outcome == DecisionFindingOutcome.NOT_EVALUATED
            )
        if not requirements:
            input_errors.append(DecisionErrorCode.DECISION_INPUT_NOT_READY.value)

    go_blocked_by_coverage = not_evaluated_mandatory > 0
    max_possible = (
        DecisionOutcome.PENDIENTE_INFORMACION if go_blocked_by_coverage else DecisionOutcome.GO
    )
    if go_blocked_by_coverage:
        warnings.append("GO_BLOCKED_BY_INCOMPLETE_COVERAGE")
    return DecisionReadiness(
        process_id=process.id,
        inputs_valid=not input_errors,
        input_errors=sorted(set(input_errors)),
        required_categories=categories,
        available_adapters=DEFAULT_ADAPTER_REGISTRY.available_domains(),
        not_evaluated_mandatory_count=not_evaluated_mandatory,
        warnings=warnings,
        max_possible_outcome=max_possible,
        go_blocked_by_coverage=go_blocked_by_coverage,
        policy=policy_summary,
    )


@router.post(
    "/{process_id}/decisions",
    response_model=DecisionQueueResponse,
    status_code=HTTPStatus.ACCEPTED,
)
def create_decision(
    process_id: UUID, payload: DecisionRequest, session: SessionDep
) -> DecisionQueueResponse:
    process = _process_or_404(session, process_id)
    normalization_run = _normalization_run_or_error(
        session, process_id, payload.normalization_run_id
    )
    company = session.get(CompanyProfile, payload.company_id)
    if company is None:
        raise DomainError(
            DecisionErrorCode.DECISION_INPUT_MISMATCH,
            "La empresa indicada no existe.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    snapshot = session.get(CompanyProfileSnapshot, payload.company_profile_snapshot_id)
    if snapshot is None or snapshot.company_id != company.id:
        raise DomainError(
            DecisionErrorCode.DECISION_INPUT_MISMATCH,
            "El snapshot no pertenece a la empresa indicada.",
            status_code=HTTPStatus.CONFLICT,
        )
    if snapshot.status != CompanySnapshotStatus.PUBLISHED.value:
        raise DomainError(
            DecisionErrorCode.DECISION_COMPANY_SNAPSHOT_NOT_PUBLISHED,
            "El snapshot de empresa no esta publicado.",
            status_code=HTTPStatus.CONFLICT,
        )
    financial_run = session.get(FinancialEvaluationRun, payload.financial_evaluation_run_id)
    if (
        financial_run is None
        or financial_run.process_id != process_id
        or financial_run.normalization_run_id != normalization_run.id
        or financial_run.company_profile_snapshot_id != snapshot.id
    ):
        raise DomainError(
            DecisionErrorCode.DECISION_INPUT_MISMATCH,
            "La evaluacion financiera no corresponde a los inputs indicados.",
            status_code=HTTPStatus.CONFLICT,
        )
    if financial_run.status not in {
        FinancialEvaluationRunStatus.COMPLETED.value,
        FinancialEvaluationRunStatus.COMPLETED_WITH_WARNINGS.value,
    }:
        raise DomainError(
            DecisionErrorCode.DECISION_FINANCIAL_EVALUATION_NOT_COMPLETED,
            "La evaluacion financiera aun no esta completada.",
            status_code=HTTPStatus.CONFLICT,
        )
    requirements = _active_requirements(session, process_id, normalization_run.id)
    if not requirements:
        raise DomainError(
            DecisionErrorCode.DECISION_INPUT_NOT_READY,
            "La normalizacion no contiene requisitos activos.",
            status_code=HTTPStatus.CONFLICT,
        )

    policy_version = _ensure_policy_version(session)
    effective_at = datetime.now(UTC)
    manifest = build_decision_manifest(
        process=process,
        normalization_run=normalization_run,
        snapshot=snapshot,
        financial_run=financial_run,
        requirements=requirements,
        policy_name=policy_version.policy_name,
        policy_version=policy_version.semantic_version,
        policy_hash=policy_version.content_sha256,
        engine_version=DECISION_ENGINE_VERSION,
        effective_at=effective_at.isoformat(),
    )
    input_digest = stable_decision_digest(manifest)

    if not payload.force:
        existing = session.scalar(
            select(DecisionRun)
            .where(
                DecisionRun.process_id == process_id,
                DecisionRun.input_digest == input_digest,
                DecisionRun.status.in_(
                    [
                        DecisionRunStatus.PENDING.value,
                        DecisionRunStatus.PROCESSING.value,
                        DecisionRunStatus.COMPLETED.value,
                        DecisionRunStatus.COMPLETED_WITH_WARNINGS.value,
                    ]
                ),
            )
            .order_by(DecisionRun.created_at.desc())
            .limit(1)
        )
        if existing is not None:
            job = session.get(DecisionJob, existing.job_id)
            if job is not None:
                return DecisionQueueResponse(
                    job=_job_summary(job), run=_run_summary(existing), reused_existing_run=True
                )

    job = DecisionJob(
        id=uuid4(),
        process_id=process_id,
        normalization_run_id=normalization_run.id,
        company_id=company.id,
        company_profile_snapshot_id=snapshot.id,
        financial_evaluation_run_id=financial_run.id,
        status=DecisionJobStatus.PENDING.value,
        priority=100,
        max_attempts=3,
        available_at=effective_at,
        force=payload.force,
    )
    session.add(job)
    session.flush()
    run = DecisionRun(
        id=uuid4(),
        job_id=job.id,
        process_id=process_id,
        normalization_run_id=normalization_run.id,
        company_id=company.id,
        company_profile_snapshot_id=snapshot.id,
        financial_evaluation_run_id=financial_run.id,
        policy_version_id=policy_version.id,
        status=DecisionRunStatus.PENDING.value,
        input_manifest=manifest,
        input_digest=input_digest,
        engine_version=DECISION_ENGINE_VERSION,
        effective_at=effective_at,
        requirement_count=len(requirements),
    )
    session.add(run)
    session.flush()
    job.run_id = run.id
    session.add(
        DecisionEvent(
            id=uuid4(),
            job_id=job.id,
            run_id=run.id,
            process_id=process_id,
            company_id=company.id,
            event_type="DECISION_QUEUED",
            summary="Decision preliminar encolada.",
            details={
                "input_digest": input_digest,
                "requirement_count": len(requirements),
                "policy_version": policy_version.semantic_version,
                "force": payload.force,
            },
        )
    )
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        active = session.scalar(
            select(DecisionJob).where(
                DecisionJob.process_id == process_id,
                DecisionJob.normalization_run_id == normalization_run.id,
                DecisionJob.company_id == company.id,
                DecisionJob.company_profile_snapshot_id == snapshot.id,
                DecisionJob.financial_evaluation_run_id == financial_run.id,
                DecisionJob.status.in_(
                    [DecisionJobStatus.PENDING.value, DecisionJobStatus.PROCESSING.value]
                ),
            )
        )
        if active is not None and active.run_id is not None:
            active_run = session.get(DecisionRun, active.run_id)
            if active_run is not None:
                return DecisionQueueResponse(
                    job=_job_summary(active),
                    run=_run_summary(active_run),
                    reused_existing_run=True,
                )
        raise DomainError(
            DecisionErrorCode.DECISION_ALREADY_QUEUED,
            "Ya existe una decision activa para esas entradas.",
            status_code=HTTPStatus.CONFLICT,
        ) from exc
    except SQLAlchemyError as exc:
        session.rollback()
        raise DomainError(
            DecisionErrorCode.DECISION_ENGINE_FAILED,
            "No fue posible encolar la decision.",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        ) from exc
    session.refresh(job)
    session.refresh(run)
    logger.info(
        "decision encolada process=%s run=%s digest=%s", process_id, run.id, input_digest[:12]
    )
    return DecisionQueueResponse(job=_job_summary(job), run=_run_summary(run))


@router.get("/{process_id}/decisions", response_model=DecisionRunList)
def list_decisions(
    process_id: UUID,
    session: SessionDep,
    company_id: UUID | None = None,
    company_profile_snapshot_id: UUID | None = None,
    outcome: DecisionOutcome | None = None,
    status: DecisionRunStatus | None = None,
    limit: LimitParam = 20,
    offset: OffsetParam = 0,
) -> DecisionRunList:
    _process_or_404(session, process_id)
    conditions = [DecisionRun.process_id == process_id]
    if company_id is not None:
        conditions.append(DecisionRun.company_id == company_id)
    if company_profile_snapshot_id is not None:
        conditions.append(DecisionRun.company_profile_snapshot_id == company_profile_snapshot_id)
    if outcome is not None:
        conditions.append(DecisionRun.effective_outcome == outcome.value)
    if status is not None:
        conditions.append(DecisionRun.status == status.value)
    total = session.scalar(select(func.count()).select_from(DecisionRun).where(*conditions)) or 0
    runs = session.scalars(
        select(DecisionRun)
        .where(*conditions)
        .order_by(DecisionRun.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return DecisionRunList(
        items=[_run_summary(run) for run in runs], total=total, limit=limit, offset=offset
    )


@router.get("/{process_id}/decisions/{decision_run_id}", response_model=DecisionRunDetailContract)
def get_decision(
    process_id: UUID, decision_run_id: UUID, session: SessionDep
) -> DecisionRunDetailContract:
    run = _run_or_404(session, process_id, decision_run_id)
    return _run_detail(session, run)


@router.post(
    "/{process_id}/decisions/{decision_run_id}/retry",
    response_model=DecisionQueueResponse,
    status_code=HTTPStatus.ACCEPTED,
)
def retry_decision(
    process_id: UUID, decision_run_id: UUID, session: SessionDep
) -> DecisionQueueResponse:
    run = _run_or_404(session, process_id, decision_run_id)
    if run.status != DecisionRunStatus.FAILED.value:
        raise DomainError(
            DecisionErrorCode.DECISION_ALREADY_COMPLETED,
            "Solo las decisiones fallidas pueden reintentarse.",
            status_code=HTTPStatus.CONFLICT,
        )
    job = DecisionJob(
        id=uuid4(),
        process_id=process_id,
        normalization_run_id=run.normalization_run_id,
        company_id=run.company_id,
        company_profile_snapshot_id=run.company_profile_snapshot_id,
        financial_evaluation_run_id=run.financial_evaluation_run_id,
        run_id=run.id,
        status=DecisionJobStatus.PENDING.value,
        priority=100,
        max_attempts=3,
        available_at=datetime.now(UTC),
        force=True,
    )
    session.add(job)
    run.job_id = job.id
    run.status = DecisionRunStatus.PENDING.value
    run.error_code = None
    run.error_message = None
    session.add(
        DecisionEvent(
            id=uuid4(),
            job_id=job.id,
            run_id=run.id,
            process_id=process_id,
            company_id=run.company_id,
            event_type="DECISION_RETRIED",
            summary="Decision reenviada a la cola.",
            details={},
        )
    )
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise DomainError(
            DecisionErrorCode.DECISION_ALREADY_QUEUED,
            "Ya existe una decision activa para esas entradas.",
            status_code=HTTPStatus.CONFLICT,
        ) from exc
    session.refresh(job)
    session.refresh(run)
    return DecisionQueueResponse(job=_job_summary(job), run=_run_summary(run))


@router.post(
    "/{process_id}/decisions/{decision_run_id}/review",
    response_model=DecisionReviewResponse,
)
def review_decision(
    process_id: UUID,
    decision_run_id: UUID,
    payload: DecisionReviewRequest,
    session: SessionDep,
) -> DecisionReviewResponse:
    run = _run_or_404(session, process_id, decision_run_id)
    if run.engine_outcome is None or run.status not in {
        DecisionRunStatus.COMPLETED.value,
        DecisionRunStatus.COMPLETED_WITH_WARNINGS.value,
    }:
        raise DomainError(
            DecisionErrorCode.INVALID_DECISION_OVERRIDE,
            "Solo las decisiones completadas pueden revisarse.",
            status_code=HTTPStatus.CONFLICT,
        )
    review = DecisionReview(
        id=uuid4(),
        decision_run_id=run.id,
        action=payload.action.value,
        original_outcome=run.engine_outcome,
        reviewed_outcome=payload.reviewed_outcome.value if payload.reviewed_outcome else None,
        reason=payload.reason,
        reviewer_reference="local-user",
    )
    session.add(review)
    event_type = {
        DecisionReviewAction.CONFIRM: "DECISION_CONFIRMED",
        DecisionReviewAction.OVERRIDE: "DECISION_OVERRIDDEN",
        DecisionReviewAction.REJECT: "DECISION_REJECTED",
    }[payload.action]
    if payload.action == DecisionReviewAction.OVERRIDE:
        run.reviewed_outcome = payload.reviewed_outcome.value
        run.effective_outcome = payload.reviewed_outcome.value
        run.requires_human_review = False
    elif payload.action == DecisionReviewAction.CONFIRM:
        run.reviewed_outcome = run.engine_outcome
        run.effective_outcome = run.engine_outcome
        run.requires_human_review = False
    else:
        run.reviewed_outcome = None
        run.effective_outcome = run.engine_outcome
        run.requires_human_review = True
    session.add(
        DecisionEvent(
            id=uuid4(),
            job_id=run.job_id,
            run_id=run.id,
            process_id=process_id,
            company_id=run.company_id,
            event_type=event_type,
            summary=f"Revision de decision: {payload.action.value}.",
            details={
                "original_outcome": run.engine_outcome,
                "reviewed_outcome": run.reviewed_outcome,
            },
        )
    )
    session.commit()
    session.refresh(run)
    session.refresh(review)
    return DecisionReviewResponse(run=_run_summary(run), review=_review_record(review))


@router.patch(
    "/{process_id}/decisions/{decision_run_id}/actions/{action_id}",
    response_model=DecisionActionItemContract,
)
def update_decision_action(
    process_id: UUID,
    decision_run_id: UUID,
    action_id: UUID,
    payload: DecisionActionUpdateRequest,
    session: SessionDep,
) -> DecisionActionItemContract:
    run = _run_or_404(session, process_id, decision_run_id)
    action = session.get(DecisionActionItemRecord, action_id)
    if action is None or action.decision_run_id != run.id:
        raise DomainError(
            DecisionErrorCode.DECISION_ACTION_NOT_FOUND,
            "La accion no existe para esa decision.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    action.status = payload.status.value
    event_type = {
        "ACKNOWLEDGED": "ACTION_ACKNOWLEDGED",
        "RESOLVED": "ACTION_RESOLVED",
        "DISMISSED": "ACTION_RESOLVED",
    }[payload.status.value]
    session.add(
        DecisionEvent(
            id=uuid4(),
            job_id=run.job_id,
            run_id=run.id,
            process_id=process_id,
            company_id=run.company_id,
            event_type=event_type,
            summary=f"Accion {payload.status.value.lower()}: {action.title_code}.",
            details={"action_id": str(action.id), "note": payload.note or ""},
        )
    )
    session.commit()
    session.refresh(action)
    return _action_contract(action)


def _process_or_404(session: Session, process_id: UUID) -> Process:
    process = session.get(Process, process_id)
    if process is None:
        raise DomainError(
            DecisionErrorCode.DECISION_NOT_FOUND,
            "El proceso no existe.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return process


def _normalization_run_or_error(
    session: Session, process_id: UUID, run_id: UUID
) -> RequirementNormalizationRun:
    run = session.get(RequirementNormalizationRun, run_id)
    if run is None or run.process_id != process_id:
        raise DomainError(
            DecisionErrorCode.DECISION_INPUT_MISMATCH,
            "La normalizacion no pertenece al proceso.",
            status_code=HTTPStatus.CONFLICT,
        )
    if run.status not in {
        RequirementNormalizationStatus.COMPLETED.value,
        RequirementNormalizationStatus.COMPLETED_WITH_WARNINGS.value,
    }:
        raise DomainError(
            DecisionErrorCode.DECISION_NORMALIZATION_NOT_COMPLETED,
            "La normalizacion aun no esta completada.",
            status_code=HTTPStatus.CONFLICT,
        )
    return run


def _active_requirements(
    session: Session, process_id: UUID, normalization_run_id: UUID
) -> list[Requirement]:
    return list(
        session.scalars(
            select(Requirement)
            .where(
                Requirement.process_id == process_id,
                Requirement.normalization_run_id == normalization_run_id,
                Requirement.is_active.is_(True),
            )
            .order_by(Requirement.created_at.asc(), Requirement.id.asc())
        ).all()
    )


def _ensure_policy_version(session: Session) -> DecisionPolicyVersion:
    try:
        policy, payload, content_hash = load_active_policy()
    except PolicyLoadError as exc:
        raise DomainError(
            DecisionErrorCode(exc.code),
            exc.message,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        ) from exc
    existing = session.scalar(
        select(DecisionPolicyVersion).where(
            DecisionPolicyVersion.policy_name == policy.policy_name,
            DecisionPolicyVersion.semantic_version == policy.semantic_version,
        )
    )
    if existing is not None:
        if existing.content_sha256 != content_hash:
            raise DomainError(
                DecisionErrorCode.DECISION_POLICY_INVALID,
                "La politica cambio sin cambiar de version; cree una version nueva.",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
        return existing
    version = DecisionPolicyVersion(
        id=uuid4(),
        policy_name=policy.policy_name,
        semantic_version=policy.semantic_version,
        content_sha256=content_hash,
        policy_payload=payload,
        engine_version=DECISION_ENGINE_VERSION,
        is_active=True,
    )
    session.add(version)
    session.flush()
    return version


def _run_or_404(session: Session, process_id: UUID, run_id: UUID) -> DecisionRun:
    run = session.get(DecisionRun, run_id)
    if run is None or run.process_id != process_id:
        raise DomainError(
            DecisionErrorCode.DECISION_NOT_FOUND,
            "La decision no existe para ese proceso.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return run


def _job_summary(job: DecisionJob) -> DecisionJobSummaryContract:
    return DecisionJobSummaryContract(
        id=job.id,
        process_id=job.process_id,
        normalization_run_id=job.normalization_run_id,
        company_id=job.company_id,
        company_profile_snapshot_id=job.company_profile_snapshot_id,
        financial_evaluation_run_id=job.financial_evaluation_run_id,
        status=DecisionJobStatus(job.status),
        attempt_count=job.attempt_count,
        max_attempts=job.max_attempts,
        force=job.force,
        last_error_code=job.last_error_code,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def _run_summary(run: DecisionRun) -> DecisionRunSummaryContract:
    manifest = run.input_manifest if isinstance(run.input_manifest, dict) else {}
    return DecisionRunSummaryContract(
        id=run.id,
        job_id=run.job_id,
        process_id=run.process_id,
        normalization_run_id=run.normalization_run_id,
        company_id=run.company_id,
        company_profile_snapshot_id=run.company_profile_snapshot_id,
        financial_evaluation_run_id=run.financial_evaluation_run_id,
        policy_name=str(manifest.get("policy_name", "")),
        policy_version=str(manifest.get("policy_version", "")),
        status=DecisionRunStatus(run.status),
        engine_outcome=DecisionOutcome(run.engine_outcome) if run.engine_outcome else None,
        reviewed_outcome=DecisionOutcome(run.reviewed_outcome) if run.reviewed_outcome else None,
        effective_outcome=(
            DecisionOutcome(run.effective_outcome) if run.effective_outcome else None
        ),
        reason_codes=list(run.reason_codes or []),
        input_digest=run.input_digest,
        engine_version=run.engine_version,
        requirement_count=run.requirement_count,
        finding_count=run.finding_count,
        action_count=run.action_count,
        warning_count=run.warning_count,
        warnings=list(run.warnings or []),
        requires_human_review=run.requires_human_review,
        started_at=run.started_at,
        finished_at=run.finished_at,
        error_code=run.error_code,
        error_message=run.error_message,
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


def _review_record(review: DecisionReview) -> DecisionReviewRecordContract:
    return DecisionReviewRecordContract(
        id=review.id,
        decision_run_id=review.decision_run_id,
        action=DecisionReviewAction(review.action),
        original_outcome=DecisionOutcome(review.original_outcome),
        reviewed_outcome=(
            DecisionOutcome(review.reviewed_outcome) if review.reviewed_outcome else None
        ),
        reason=review.reason,
        reviewer_reference=review.reviewer_reference,
        created_at=review.created_at,
    )


def _action_contract(action: DecisionActionItemRecord) -> DecisionActionItemContract:
    return DecisionActionItemContract(
        id=action.id,
        decision_run_id=action.decision_run_id,
        action_type=action.action_type,
        priority=action.priority,
        title_code=action.title_code,
        description_code=action.description_code,
        parameters=action.parameters or {},
        requirement_ids=[UUID(item) for item in action.requirement_ids or []],
        finding_ids=[UUID(item) for item in action.finding_ids or []],
        due_at=action.due_at,
        status=action.status,
        created_at=action.created_at,
        updated_at=action.updated_at,
    )


def _run_detail(session: Session, run: DecisionRun) -> DecisionRunDetailContract:
    findings = session.scalars(
        select(DecisionInputFindingSnapshot)
        .where(DecisionInputFindingSnapshot.decision_run_id == run.id)
        .order_by(DecisionInputFindingSnapshot.category.asc())
    ).all()
    requirement_ids = {finding.requirement_id for finding in findings}
    stable_keys: dict[UUID, str] = {}
    if requirement_ids:
        stable_keys = {
            requirement.id: requirement.stable_key
            for requirement in session.scalars(
                select(Requirement).where(Requirement.id.in_(requirement_ids))
            ).all()
        }
    rules = session.scalars(
        select(DecisionRuleEvaluationRecord)
        .where(DecisionRuleEvaluationRecord.decision_run_id == run.id)
        .order_by(DecisionRuleEvaluationRecord.priority.asc())
    ).all()
    actions = session.scalars(
        select(DecisionActionItemRecord)
        .where(DecisionActionItemRecord.decision_run_id == run.id)
        .order_by(DecisionActionItemRecord.created_at.asc())
    ).all()
    reviews = session.scalars(
        select(DecisionReview)
        .where(DecisionReview.decision_run_id == run.id)
        .order_by(DecisionReview.created_at.asc())
    ).all()
    events = session.scalars(
        select(DecisionEvent)
        .where(DecisionEvent.run_id == run.id)
        .order_by(DecisionEvent.created_at.asc())
    ).all()
    policy_version = session.get(DecisionPolicyVersion, run.policy_version_id)
    job = session.get(DecisionJob, run.job_id)
    summary = _run_summary(run)
    return DecisionRunDetailContract(
        **summary.model_dump(),
        input_manifest=run.input_manifest or {},
        coverage=run.coverage_summary or None,
        findings=[_finding_contract(finding, stable_keys) for finding in findings],
        rule_evaluations=[_rule_contract(rule) for rule in rules],
        actions=[_action_contract(action) for action in actions],
        reviews=[_review_record(review) for review in reviews],
        job=_job_summary(job) if job is not None else None,
        policy=(
            DecisionPolicySummaryContract(
                id=policy_version.id,
                policy_name=policy_version.policy_name,
                semantic_version=policy_version.semantic_version,
                content_sha256=policy_version.content_sha256,
                engine_version=policy_version.engine_version,
                is_active=policy_version.is_active,
                created_at=policy_version.created_at,
            )
            if policy_version is not None
            else None
        ),
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


def _finding_contract(
    finding: DecisionInputFindingSnapshot, stable_keys: dict[UUID, str]
) -> DecisionInputFindingContract:
    return DecisionInputFindingContract(
        id=finding.id,
        requirement_id=finding.requirement_id,
        requirement_stable_key=stable_keys.get(finding.requirement_id, "0" * 64),
        category=finding.category,
        scope=finding.scope,
        modality=finding.modality,
        criticality=finding.criticality,
        criticality_basis=finding.criticality_basis,
        subsanability=finding.subsanability,
        subsanability_basis=finding.subsanability_basis,
        evaluation_domain=finding.evaluation_domain,
        source_type=finding.source_type,
        source_run_id=finding.source_run_id,
        source_result_id=finding.source_result_id,
        outcome=finding.outcome,
        applicability=finding.applicability,
        evidence_quality=finding.evidence_quality,
        review_status=finding.review_status,
        requires_human_review=finding.requires_human_review,
        is_blocking=finding.is_blocking,
        is_remediable=finding.is_remediable,
        partner_solvable=finding.partner_solvable,
        submission_blocker=finding.submission_blocker,
        condition_codes=list(finding.condition_codes or []),
        warning_codes=list(finding.warning_codes or []),
        evidence_references=list(finding.evidence_references or []),
        created_at=finding.created_at,
    )


def _rule_contract(rule: DecisionRuleEvaluationRecord) -> DecisionRuleEvaluationContract:
    return DecisionRuleEvaluationContract(
        id=rule.id,
        rule_code=rule.rule_code,
        rule_version=rule.rule_version,
        priority=rule.priority,
        status=rule.status,
        suggested_outcome=rule.suggested_outcome,
        fact_payload=rule.fact_payload or {},
        requirement_ids=[UUID(item) for item in rule.requirement_ids or []],
        finding_ids=[UUID(item) for item in rule.finding_ids or []],
        reason_code=rule.reason_code,
        created_at=rule.created_at,
    )
