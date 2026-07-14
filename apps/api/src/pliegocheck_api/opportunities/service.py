"""Orquestacion y persistencia de la bandeja de oportunidades."""
# mypy: disable-error-code="no-untyped-def,no-untyped-call"

from __future__ import annotations

from datetime import UTC, datetime
from http import HTTPStatus
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from pliegocheck_api.auth import CurrentUser, audit_event
from pliegocheck_api.config import Settings
from pliegocheck_api.errors import DomainError
from pliegocheck_api.external_procurement.service import run_search
from pliegocheck_api.models import (
    CompanyProfile,
    CompanyProfileSnapshot,
    DecisionRun,
    DocumentExtraction,
    ExternalProcurementProcessLink,
    ExternalProcurementSearchResult,
    FinancialEvaluationRun,
    OpportunityAssessment,
    OpportunityAssessmentComponentModel,
    OpportunityCandidate,
    OpportunityDiscoveryRun,
    OpportunityEvent,
    OpportunityReview,
    ProcessDocument,
    Requirement,
    SpecializedEvaluationRun,
)
from pliegocheck_schemas import (
    CompanySnapshotStatus,
    ExternalProcurementSourceSystem,
    OperationalAuditEventType,
    OpportunityAnalysisLevel,
    OpportunityAssessmentComponentDetail,
    OpportunityAssessmentDetail,
    OpportunityAssessmentSummary,
    OpportunityCandidateSummary,
    OpportunityComponent,
    OpportunityComponentStatus,
    OpportunityDeepAnalysisResponse,
    OpportunityDiscoveryRequest,
    OpportunityDiscoveryResponse,
    OpportunityDiscoveryRunDetail,
    OpportunityDiscoveryRunSummary,
    OpportunityDiscoveryStatus,
    OpportunityErrorCode,
    OpportunityOutcome,
    OpportunityReviewAction,
    OpportunityReviewRequest,
    OpportunityReviewResponse,
    OpportunityUrgencyStatus,
)

from .engine import assess
from .explanations import explain
from .models import CompanySnapshotInput, ProcessInput
from .policy import canonical_hash, load_policy


def enqueue_discovery(
    session: Session,
    payload: OpportunityDiscoveryRequest,
    *,
    actor: CurrentUser | None,
    settings: Settings,
) -> OpportunityDiscoveryResponse:
    if not settings.opportunities_enabled:
        raise DomainError(
            OpportunityErrorCode.INVALID_FILTER,
            "La bandeja de oportunidades esta deshabilitada.",
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
        )
    if len(payload.candidate_ids) > settings.opportunities_max_candidates:
        raise DomainError(
            OpportunityErrorCode.INVALID_FILTER,
            "La solicitud supera el limite de candidatos.",
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    snapshot = _published_snapshot(session, payload.company_profile_id, payload.company_snapshot_id)
    if not payload.search_requests and not payload.candidate_ids:
        raise DomainError(
            OpportunityErrorCode.INVALID_FILTER,
            "Debe proporcionar filtros SECOP o candidatos persistidos.",
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    policy = load_policy()
    effective_at = (payload.effective_at or datetime.now(UTC)).replace(second=0, microsecond=0)
    digest_payload = {
        "company_snapshot_id": str(snapshot.id),
        "snapshot_digest": snapshot.digest,
        "policy_hash": policy.policy_hash,
        "search_requests": [item.model_dump(mode="json") for item in payload.search_requests],
        "candidate_ids": sorted(str(item) for item in payload.candidate_ids),
        "effective_at": effective_at.isoformat(),
    }
    input_digest = canonical_hash(digest_payload)
    if not payload.force:
        existing = session.scalar(
            select(OpportunityDiscoveryRun)
            .where(OpportunityDiscoveryRun.input_digest == input_digest)
            .order_by(OpportunityDiscoveryRun.created_at.desc())
            .limit(1)
        )
        if existing:
            return OpportunityDiscoveryResponse(run=run_summary(existing), reused=True)
    row = OpportunityDiscoveryRun(
        id=uuid4(),
        company_profile_id=payload.company_profile_id,
        company_snapshot_id=payload.company_snapshot_id,
        policy_version=policy.version,
        policy_hash=policy.policy_hash,
        filters={
            "search_requests": [item.model_dump(mode="json") for item in payload.search_requests],
            "candidate_ids": [str(item) for item in payload.candidate_ids],
        },
        source_systems=[item.source_system.value for item in payload.search_requests],
        status=OpportunityDiscoveryStatus.PENDING.value,
        effective_at=effective_at,
        input_digest=input_digest,
        max_attempts=settings.worker_max_attempts,
        created_by=actor.id if actor else None,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return OpportunityDiscoveryResponse(run=run_summary(row), reused=False)


def process_next_discovery(
    session: Session, settings: Settings, worker_id: str
) -> OpportunityDiscoveryRun | None:
    row = session.scalar(
        select(OpportunityDiscoveryRun)
        .where(
            OpportunityDiscoveryRun.status == OpportunityDiscoveryStatus.PENDING.value,
            OpportunityDiscoveryRun.available_at <= datetime.now(UTC),
        )
        .order_by(OpportunityDiscoveryRun.created_at)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if row is None:
        return None
    row.status = OpportunityDiscoveryStatus.PROCESSING.value
    row.started_at = datetime.now(UTC)
    row.locked_at = row.started_at
    row.locked_by = worker_id
    row.attempt_count += 1
    session.commit()
    try:
        process_discovery_run(session, settings, row)
    except Exception as exc:
        session.rollback()
        row = session.get(OpportunityDiscoveryRun, row.id)
        assert row is not None
        row.status = OpportunityDiscoveryStatus.FAILED.value
        row.error_code = type(exc).__name__[:64]
        row.error_message = "No fue posible completar el screening."
        row.finished_at = datetime.now(UTC)
        session.commit()
        raise
    return row


def process_discovery_run(
    session: Session, settings: Settings, row: OpportunityDiscoveryRun
) -> None:
    policy = load_policy()
    if policy.policy_hash != row.policy_hash:
        raise ValueError("policy hash changed while run was pending")
    result_ids = {UUID(value) for value in row.filters.get("candidate_ids", [])}
    for raw_request in row.filters.get("search_requests", []):
        from pliegocheck_schemas import ExternalProcurementSearchRequest

        response = run_search(
            session, settings, ExternalProcurementSearchRequest.model_validate(raw_request)
        )
        result_ids.update(item.id for item in response.items)
    results = list(
        session.scalars(
            select(ExternalProcurementSearchResult).where(
                ExternalProcurementSearchResult.id.in_(result_ids)
            )
        )
    )
    snapshot = _published_snapshot(session, row.company_profile_id, row.company_snapshot_id)
    for source in results:
        candidate = _persist_candidate(session, row, source)
        _persist_assessment(session, candidate, snapshot, source, policy, row.effective_at)
    row.candidate_count = len(results)
    row.assessed_count = len(results)
    row.warning_count = sum(len(source.warnings) for source in results)
    row.warnings = (
        ["Algunos registros contienen advertencias de fuente."] if row.warning_count else []
    )
    row.status = (
        OpportunityDiscoveryStatus.COMPLETED_WITH_WARNINGS.value
        if row.warning_count
        else OpportunityDiscoveryStatus.COMPLETED.value
    )
    row.finished_at = datetime.now(UTC)
    row.locked_at = None
    row.locked_by = None
    audit_event(
        session,
        event_type=OperationalAuditEventType.OPPORTUNITY_DISCOVERY_COMPLETED,
        action="opportunity.discovery.process",
        status=row.status,
        entity_type="opportunity_discovery_run",
        entity_id=row.id,
        metadata={"candidate_count": row.candidate_count, "warning_count": row.warning_count},
    )
    session.commit()


def reassess(session: Session, assessment_id: UUID) -> OpportunityAssessment:
    current = _assessment(session, assessment_id)
    candidate = session.get(OpportunityCandidate, current.candidate_id)
    assert candidate is not None
    source = session.get(ExternalProcurementSearchResult, candidate.external_search_result_id)
    snapshot = session.get(CompanyProfileSnapshot, current.company_snapshot_id)
    assert source is not None and snapshot is not None
    persisted: OpportunityAssessment = _persist_assessment(
        session, candidate, snapshot, source, load_policy(), datetime.now(UTC)
    )
    session.commit()
    return persisted


def create_review(
    session: Session,
    assessment_id: UUID,
    payload: OpportunityReviewRequest,
    actor: CurrentUser | None,
) -> OpportunityReviewResponse:
    _assessment(session, assessment_id)
    latest = session.scalar(
        select(OpportunityReview)
        .where(OpportunityReview.assessment_id == assessment_id)
        .order_by(OpportunityReview.created_at.desc())
        .limit(1)
    )
    row = OpportunityReview(
        id=uuid4(),
        assessment_id=assessment_id,
        action=payload.action.value,
        reason=payload.reason,
        previous_action=latest.action if latest else None,
        created_by=actor.id if actor else None,
    )
    session.add(row)
    session.add(
        OpportunityEvent(
            id=uuid4(),
            opportunity_id=assessment_id,
            event_type=_review_event(payload.action),
            event_metadata={"action": payload.action.value},
            created_by=actor.id if actor else None,
        )
    )
    session.commit()
    session.refresh(row)
    return OpportunityReviewResponse(
        assessment_id=assessment_id,
        action=payload.action,
        previous_action=OpportunityReviewAction(row.previous_action)
        if row.previous_action
        else None,
        created_at=row.created_at,
    )


def deep_analysis_readiness(
    session: Session, assessment_id: UUID, actor: CurrentUser | None
) -> OpportunityDeepAnalysisResponse:
    assessment = _assessment(session, assessment_id)
    candidate = session.get(OpportunityCandidate, assessment.candidate_id)
    assert candidate is not None
    ready: list[str] = []
    blocked: list[str] = []
    missing: list[str] = []
    process_id = candidate.process_id
    if process_id is None:
        missing.append("imported_process")
        blocked.append("document_pipeline")
    else:
        documents = session.scalar(
            select(func.count())
            .select_from(ProcessDocument)
            .where(ProcessDocument.process_id == process_id)
        )
        extractions = session.scalar(
            select(func.count())
            .select_from(DocumentExtraction)
            .join(ProcessDocument, ProcessDocument.id == DocumentExtraction.document_id)
            .where(ProcessDocument.process_id == process_id)
        )
        requirements = session.scalar(
            select(func.count())
            .select_from(Requirement)
            .where(Requirement.process_id == process_id)
        )
        if documents:
            ready.append("documents")
        else:
            missing.append("documents")
        if extractions:
            ready.append("extraction")
        else:
            blocked.append("extraction")
        if requirements:
            ready.append("normalization")
        else:
            blocked.append("normalization")
        for label, model in (
            ("financial_evaluation", FinancialEvaluationRun),
            ("specialized_evaluations", SpecializedEvaluationRun),
            ("decision", DecisionRun),
        ):
            if session.scalar(select(model.id).where(model.process_id == process_id).limit(1)):
                ready.append(label)
            else:
                blocked.append(label)
    session.add(
        OpportunityEvent(
            id=uuid4(),
            opportunity_id=assessment_id,
            event_type="OPPORTUNITY_DEEP_ANALYSIS_REQUESTED",
            event_metadata={"ready": len(ready), "blocked": len(blocked)},
            created_by=actor.id if actor else None,
        )
    )
    session.commit()
    return OpportunityDeepAnalysisResponse(
        opportunity_id=assessment_id,
        process_id=process_id,
        steps_ready=ready,
        steps_queued=[],
        steps_blocked=blocked,
        missing_inputs=missing,
    )


def run_summary(row: OpportunityDiscoveryRun) -> OpportunityDiscoveryRunSummary:
    return OpportunityDiscoveryRunSummary(
        id=row.id,
        company_profile_id=row.company_profile_id,
        company_snapshot_id=row.company_snapshot_id,
        policy_version=row.policy_version,
        policy_hash=row.policy_hash,
        status=OpportunityDiscoveryStatus(row.status),
        effective_at=row.effective_at,
        input_digest=row.input_digest,
        candidate_count=row.candidate_count,
        assessed_count=row.assessed_count,
        warning_count=row.warning_count,
        started_at=row.started_at,
        finished_at=row.finished_at,
        created_at=row.created_at,
    )


def assessment_detail(session: Session, row: OpportunityAssessment) -> OpportunityAssessmentDetail:
    candidate = session.get(OpportunityCandidate, row.candidate_id)
    assert candidate is not None
    components = list(
        session.scalars(
            select(OpportunityAssessmentComponentModel)
            .where(OpportunityAssessmentComponentModel.assessment_id == row.id)
            .order_by(OpportunityAssessmentComponentModel.component)
        )
    )
    latest = session.scalar(
        select(OpportunityReview)
        .where(OpportunityReview.assessment_id == row.id)
        .order_by(OpportunityReview.created_at.desc())
        .limit(1)
    )
    return OpportunityAssessmentDetail(
        **assessment_summary(row).model_dump(),
        candidate=candidate_summary(candidate),
        components=[
            OpportunityAssessmentComponentDetail(
                id=item.id,
                component=OpportunityComponent(item.component),
                status=OpportunityComponentStatus(item.status),
                score=item.score,
                weight=item.weight,
                weighted_score=item.weighted_score,
                reason_code=item.reason_code,
                explanation=explain(item.reason_code, item.explanation_parameters),
                explanation_parameters=item.explanation_parameters,
                evidence_refs=item.evidence_refs,
                warnings=item.warnings,
                evidence=[],
            )
            for item in components
        ],
        latest_review_action=OpportunityReviewAction(latest.action) if latest else None,
    )


def assessment_summary(row: OpportunityAssessment) -> OpportunityAssessmentSummary:
    return OpportunityAssessmentSummary(
        id=row.id,
        candidate_id=row.candidate_id,
        company_snapshot_id=row.company_snapshot_id,
        policy_version=row.policy_version,
        policy_hash=row.policy_hash,
        analysis_level=OpportunityAnalysisLevel(row.analysis_level),
        outcome=OpportunityOutcome(row.outcome),
        compatibility_score=row.compatibility_score,
        urgency_score=row.urgency_score,
        information_completeness=row.information_completeness,
        days_remaining=row.days_remaining,
        urgency_status=OpportunityUrgencyStatus(row.urgency_status),
        requires_human_review=row.requires_human_review,
        input_digest=row.input_digest,
        summary=row.summary,
        warnings=row.warnings,
        missing_information=row.missing_information,
        partner_reasons=row.partner_reasons,
        effective_at=row.effective_at,
        created_at=row.created_at,
    )


def candidate_summary(row: OpportunityCandidate) -> OpportunityCandidateSummary:
    return OpportunityCandidateSummary(
        id=row.id,
        discovery_run_id=row.discovery_run_id,
        external_search_result_id=row.external_search_result_id,
        process_id=row.process_id,
        source_system=ExternalProcurementSourceSystem(row.source_system),
        source_process_id=row.source_process_id,
        source_reference=row.source_reference,
        title=row.title,
        entity_name=row.entity_name,
        modality=row.modality,
        source_status=row.source_status,
        publication_date=row.publication_date,
        closing_date=row.closing_date,
        estimated_value=row.estimated_value,
        currency=row.currency,
        department=row.department,
        municipality=row.municipality,
        document_status=row.document_status,
        created_at=row.created_at,
    )


def run_detail(session: Session, row: OpportunityDiscoveryRun) -> OpportunityDiscoveryRunDetail:
    assessments = list(
        session.scalars(
            select(OpportunityAssessment)
            .join(
                OpportunityCandidate, OpportunityCandidate.id == OpportunityAssessment.candidate_id
            )
            .where(OpportunityCandidate.discovery_run_id == row.id)
            .order_by(OpportunityAssessment.compatibility_score.desc())
        )
    )
    return OpportunityDiscoveryRunDetail(
        **run_summary(row).model_dump(),
        candidates=[assessment_detail(session, item) for item in assessments],
        warnings=row.warnings,
    )


def _persist_candidate(session, run, source):
    link = session.scalar(
        select(ExternalProcurementProcessLink).where(
            ExternalProcurementProcessLink.source_system == source.source_system,
            ExternalProcurementProcessLink.source_dataset == source.source_dataset,
            ExternalProcurementProcessLink.source_process_id == source.source_process_id,
        )
    )
    row = OpportunityCandidate(
        id=uuid4(),
        discovery_run_id=run.id,
        external_search_result_id=source.id,
        process_id=link.process_id if link else None,
        source_system=source.source_system,
        source_process_id=source.source_process_id,
        source_reference=source.source_process_reference,
        title=source.title,
        entity_name=source.entity_name,
        modality=source.modality,
        source_status=source.status,
        publication_date=source.publication_date,
        closing_date=source.closing_date,
        estimated_value=source.estimated_value,
        currency=source.currency,
        department=source.department,
        municipality=source.municipality,
        document_status=source.documents_status,
    )
    session.add(row)
    session.flush()
    return row


def _persist_assessment(session, candidate, snapshot, source, policy, effective_at):
    normalized = source.normalized_payload
    unspsc = normalized.get("unspsc_codes") or normalized.get("unspsc") or []
    if isinstance(unspsc, str):
        unspsc = [unspsc]
    result = assess(
        CompanySnapshotInput(str(snapshot.id), snapshot.digest, snapshot.payload),
        ProcessInput(
            source.source_process_id,
            source.title,
            source.entity_name,
            normalized.get("description") or normalized.get("object_description"),
            tuple(unspsc),
            source.status,
            source.estimated_value,
            source.currency,
            source.department,
            source.municipality,
            source.publication_date,
            source.closing_date,
            source.documents_status,
            source.source_system,
            source.source_process_reference,
            source.raw_payload_hash,
        ),
        policy,
        effective_at,
    )
    row = OpportunityAssessment(
        id=uuid4(),
        candidate_id=candidate.id,
        company_snapshot_id=snapshot.id,
        policy_version=policy.version,
        policy_hash=policy.policy_hash,
        analysis_level=OpportunityAnalysisLevel.METADATA_SCREENING.value,
        outcome=result.outcome,
        compatibility_score=result.compatibility_score,
        urgency_score=result.urgency_score,
        information_completeness=result.information_completeness,
        days_remaining=result.days_remaining,
        urgency_status=result.urgency_status,
        requires_human_review=True,
        input_digest=result.input_digest,
        summary=result.summary,
        warnings=list(result.warnings),
        missing_information=result.missing_information,
        partner_reasons=list(result.partner_reasons),
        effective_at=effective_at,
    )
    session.add(row)
    session.flush()
    for component in result.components:
        session.add(
            OpportunityAssessmentComponentModel(
                id=uuid4(),
                assessment_id=row.id,
                component=component.component.value,
                status=component.status.value,
                score=component.score,
                weight=component.weight,
                weighted_score=component.weighted_score,
                reason_code=component.reason_code,
                explanation_parameters=component.explanation_parameters,
                evidence_refs=list(component.evidence_refs),
                warnings=list(component.warnings),
            )
        )
    session.add(
        OpportunityEvent(
            id=uuid4(),
            opportunity_id=row.id,
            event_type="OPPORTUNITY_ASSESSED",
            event_metadata={"outcome": result.outcome},
            created_by=None,
        )
    )
    session.flush()
    return row


def _published_snapshot(session, company_id, snapshot_id):
    if session.get(CompanyProfile, company_id) is None:
        raise DomainError(
            OpportunityErrorCode.COMPANY_SNAPSHOT_REQUIRED,
            "La empresa no existe.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    row = session.scalar(
        select(CompanyProfileSnapshot).where(
            CompanyProfileSnapshot.id == snapshot_id,
            CompanyProfileSnapshot.company_id == company_id,
        )
    )
    if row is None:
        raise DomainError(
            OpportunityErrorCode.COMPANY_SNAPSHOT_REQUIRED,
            "Se requiere un snapshot empresarial publicado.",
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    if row.status != CompanySnapshotStatus.PUBLISHED.value:
        raise DomainError(
            OpportunityErrorCode.COMPANY_SNAPSHOT_NOT_PUBLISHED,
            "El snapshot empresarial debe estar publicado.",
            status_code=HTTPStatus.CONFLICT,
        )
    return row


def _assessment(session, assessment_id):
    row = session.get(OpportunityAssessment, assessment_id)
    if row is None:
        raise DomainError(
            OpportunityErrorCode.OPPORTUNITY_NOT_FOUND,
            "La oportunidad no existe.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return row


def _review_event(action):
    return {
        OpportunityReviewAction.SHORTLIST: "OPPORTUNITY_SHORTLISTED",
        OpportunityReviewAction.DISMISS: "OPPORTUNITY_DISMISSED",
        OpportunityReviewAction.SEEK_PARTNER: "OPPORTUNITY_PARTNER_REVIEW_REQUESTED",
        OpportunityReviewAction.REQUEST_DEEP_ANALYSIS: "OPPORTUNITY_DEEP_ANALYSIS_REQUESTED",
    }.get(action, "OPPORTUNITY_REVIEWED")
