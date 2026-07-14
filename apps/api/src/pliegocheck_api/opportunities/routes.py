"""API de discovery, bandeja, revision e integracion profunda."""

from datetime import datetime
from http import HTTPStatus
from typing import Annotated, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from pliegocheck_api.auth import CurrentUser, audit_event
from pliegocheck_api.config import Settings, get_settings
from pliegocheck_api.db import get_session
from pliegocheck_api.errors import DomainError
from pliegocheck_api.external_procurement.service import import_result
from pliegocheck_api.models import (
    CompanyProfile,
    CompanyProfileSnapshot,
    OpportunityAssessment,
    OpportunityCandidate,
    OpportunityDiscoveryRun,
    OpportunityEvent,
    OpportunityReview,
)
from pliegocheck_schemas import (
    AuthErrorCode,
    AuthPermission,
    CompanySnapshotStatus,
    ExternalProcurementImportResponse,
    ExternalProcurementSourceSystem,
    OperationalAuditEventType,
    OpportunityAnalysisLevel,
    OpportunityAssessmentDetail,
    OpportunityDeepAnalysisResponse,
    OpportunityDiscoveryRequest,
    OpportunityDiscoveryResponse,
    OpportunityDiscoveryRunDetail,
    OpportunityDiscoveryRunSummary,
    OpportunityErrorCode,
    OpportunityInboxResponse,
    OpportunityOutcome,
    OpportunityReadiness,
    OpportunityReviewAction,
    OpportunityReviewRequest,
    OpportunityReviewResponse,
    OpportunityUrgencyStatus,
)

from .policy import load_policy
from .service import (
    assessment_detail,
    create_review,
    deep_analysis_readiness,
    enqueue_discovery,
    reassess,
    run_detail,
    run_summary,
)

router = APIRouter(prefix="/opportunities", tags=["opportunities"])
SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
DISCLAIMER = (
    "La priorizacion expresa compatibilidad preliminar con el perfil empresarial y la "
    "informacion publica disponible. No recomienda presentar oferta ni "
    "reemplaza la revision humana."
)


def _actor(request: Request) -> CurrentUser | None:
    value = getattr(request.state, "current_user", None)
    return cast(CurrentUser, value) if value is not None else None


@router.get("/readiness", response_model=OpportunityReadiness)
def readiness(session: SessionDep) -> OpportunityReadiness:
    policy = load_policy()
    companies = session.scalar(select(func.count()).select_from(CompanyProfile))
    snapshots = session.scalar(
        select(func.count())
        .select_from(CompanyProfileSnapshot)
        .where(CompanyProfileSnapshot.status == CompanySnapshotStatus.PUBLISHED.value)
    )
    reasons = [] if snapshots else ["Se requiere al menos un snapshot empresarial publicado."]
    return OpportunityReadiness(
        ready=bool(companies and snapshots),
        companies_count=companies or 0,
        published_snapshots_count=snapshots or 0,
        policy_version=policy.version,
        policy_hash=policy.policy_hash,
        reasons=reasons,
    )


@router.post(
    "/discovery-runs",
    response_model=OpportunityDiscoveryResponse,
    status_code=HTTPStatus.ACCEPTED,
)
def create_discovery(
    payload: OpportunityDiscoveryRequest,
    request: Request,
    session: SessionDep,
    settings: SettingsDep,
) -> OpportunityDiscoveryResponse:
    response = enqueue_discovery(session, payload, actor=_actor(request), settings=settings)
    audit_event(
        session,
        event_type=OperationalAuditEventType.OPPORTUNITY_DISCOVERY_REQUESTED,
        action="opportunity.discovery.request",
        status="REUSED" if response.reused else "QUEUED",
        actor=_actor(request),
        request=request,
        entity_type="opportunity_discovery_run",
        entity_id=response.run.id,
        metadata={"candidate_count": len(payload.candidate_ids)},
    )
    session.commit()
    return response


@router.get("/discovery-runs", response_model=list[OpportunityDiscoveryRunSummary])
def discovery_runs(session: SessionDep) -> list[OpportunityDiscoveryRunSummary]:
    rows = session.scalars(
        select(OpportunityDiscoveryRun)
        .order_by(OpportunityDiscoveryRun.created_at.desc())
        .limit(100)
    )
    return [run_summary(row) for row in rows]


@router.get("/discovery-runs/{run_id}", response_model=OpportunityDiscoveryRunDetail)
def discovery_run(run_id: UUID, session: SessionDep) -> OpportunityDiscoveryRunDetail:
    row = session.get(OpportunityDiscoveryRun, run_id)
    if row is None:
        raise DomainError(
            OpportunityErrorCode.DISCOVERY_RUN_NOT_FOUND,
            "La ejecucion no existe.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return run_detail(session, row)


@router.get("", response_model=OpportunityInboxResponse)
def inbox(
    session: SessionDep,
    company_snapshot_id: UUID | None = None,
    source_system: ExternalProcurementSourceSystem | None = None,
    outcome: OpportunityOutcome | None = None,
    urgency: OpportunityUrgencyStatus | None = None,
    entity: str | None = Query(default=None, max_length=200),
    department: str | None = Query(default=None, max_length=200),
    municipality: str | None = Query(default=None, max_length=200),
    modality: str | None = Query(default=None, max_length=200),
    min_value: float | None = Query(default=None, ge=0),
    max_value: float | None = Query(default=None, ge=0),
    closing_from: Annotated[datetime | None, Query()] = None,
    closing_to: Annotated[datetime | None, Query()] = None,
    document_status: str | None = Query(default=None, max_length=64),
    analysis_level: OpportunityAnalysisLevel | None = None,
    review_action: OpportunityReviewAction | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort: str = Query(
        default="priority",
        pattern="^(priority|compatibility|urgency|closing_date|publication_date|value)$",
    ),
) -> OpportunityInboxResponse:
    query = select(OpportunityAssessment).join(
        OpportunityCandidate, OpportunityCandidate.id == OpportunityAssessment.candidate_id
    )
    if company_snapshot_id:
        query = query.where(OpportunityAssessment.company_snapshot_id == company_snapshot_id)
    if source_system:
        query = query.where(OpportunityCandidate.source_system == source_system.value)
    if outcome:
        query = query.where(OpportunityAssessment.outcome == outcome.value)
    if urgency:
        query = query.where(OpportunityAssessment.urgency_status == urgency.value)
    if entity:
        query = query.where(OpportunityCandidate.entity_name.ilike(f"%{entity}%"))
    if department:
        query = query.where(OpportunityCandidate.department == department)
    if municipality:
        query = query.where(OpportunityCandidate.municipality == municipality)
    if modality:
        query = query.where(OpportunityCandidate.modality == modality)
    if min_value is not None:
        query = query.where(OpportunityCandidate.estimated_value >= min_value)
    if max_value is not None:
        query = query.where(OpportunityCandidate.estimated_value <= max_value)
    if closing_from is not None:
        query = query.where(OpportunityCandidate.closing_date >= closing_from)
    if closing_to is not None:
        query = query.where(OpportunityCandidate.closing_date <= closing_to)
    if document_status:
        query = query.where(OpportunityCandidate.document_status == document_status)
    if analysis_level:
        query = query.where(OpportunityAssessment.analysis_level == analysis_level.value)
    if review_action:
        latest_action = (
            select(OpportunityReview.action)
            .where(OpportunityReview.assessment_id == OpportunityAssessment.id)
            .order_by(OpportunityReview.created_at.desc())
            .limit(1)
            .scalar_subquery()
        )
        query = query.where(latest_action == review_action.value)
    priority = case(
        (OpportunityAssessment.outcome == OpportunityOutcome.REVISAR_PRIMERO.value, 0),
        (OpportunityAssessment.outcome == OpportunityOutcome.OPORTUNIDAD_POTENCIAL.value, 1),
        (OpportunityAssessment.outcome == OpportunityOutcome.REQUIERE_ALIADO.value, 2),
        (OpportunityAssessment.outcome == OpportunityOutcome.INFORMACION_INSUFICIENTE.value, 3),
        (OpportunityAssessment.outcome == OpportunityOutcome.POCO_COMPATIBLE.value, 4),
        else_=5,
    )
    order = {
        "priority": (
            priority,
            OpportunityAssessment.compatibility_score.desc(),
        ),
        "compatibility": (OpportunityAssessment.compatibility_score.desc(),),
        "urgency": (OpportunityAssessment.urgency_score.desc(),),
        "closing_date": (OpportunityCandidate.closing_date.asc(),),
        "publication_date": (OpportunityCandidate.publication_date.desc(),),
        "value": (OpportunityCandidate.estimated_value.desc(),),
    }[sort]
    total = session.scalar(select(func.count()).select_from(query.subquery()))
    rows = session.scalars(query.order_by(*order).limit(limit).offset(offset))
    return OpportunityInboxResponse(
        items=[assessment_detail(session, row) for row in rows],
        total=total or 0,
        limit=limit,
        offset=offset,
        disclaimer=DISCLAIMER,
    )


@router.get("/{opportunity_id}", response_model=OpportunityAssessmentDetail)
def opportunity(opportunity_id: UUID, session: SessionDep) -> OpportunityAssessmentDetail:
    row = session.get(OpportunityAssessment, opportunity_id)
    if row is None:
        raise DomainError(
            OpportunityErrorCode.OPPORTUNITY_NOT_FOUND,
            "La oportunidad no existe.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return assessment_detail(session, row)


@router.post("/{opportunity_id}/assess", response_model=OpportunityAssessmentDetail)
def assess_again(opportunity_id: UUID, session: SessionDep) -> OpportunityAssessmentDetail:
    result = assessment_detail(session, reassess(session, opportunity_id))
    audit_event(
        session,
        event_type=OperationalAuditEventType.OPPORTUNITY_REASSESSED,
        action="opportunity.assess",
        status="COMPLETED",
        entity_type="opportunity_assessment",
        entity_id=result.id,
    )
    session.commit()
    return result


@router.post("/{opportunity_id}/review", response_model=OpportunityReviewResponse)
def review(
    opportunity_id: UUID,
    payload: OpportunityReviewRequest,
    request: Request,
    session: SessionDep,
) -> OpportunityReviewResponse:
    response = create_review(session, opportunity_id, payload, _actor(request))
    event_type = {
        OpportunityReviewAction.SHORTLIST: OperationalAuditEventType.OPPORTUNITY_SHORTLISTED,
        OpportunityReviewAction.DISMISS: OperationalAuditEventType.OPPORTUNITY_DISMISSED,
        OpportunityReviewAction.SEEK_PARTNER: (
            OperationalAuditEventType.OPPORTUNITY_PARTNER_REVIEW_REQUESTED
        ),
    }.get(payload.action, OperationalAuditEventType.OPPORTUNITY_ASSESSED)
    audit_event(
        session,
        event_type=event_type,
        action="opportunity.review",
        status="COMPLETED",
        actor=_actor(request),
        request=request,
        entity_type="opportunity_assessment",
        entity_id=opportunity_id,
        metadata={"review_action": payload.action.value},
    )
    session.commit()
    return response


@router.post("/{opportunity_id}/import", response_model=ExternalProcurementImportResponse)
def import_opportunity(
    opportunity_id: UUID, request: Request, session: SessionDep
) -> ExternalProcurementImportResponse:
    assessment = session.get(OpportunityAssessment, opportunity_id)
    candidate = session.get(OpportunityCandidate, assessment.candidate_id) if assessment else None
    if candidate is None:
        raise DomainError(
            OpportunityErrorCode.OPPORTUNITY_NOT_FOUND,
            "La oportunidad no existe.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    actor = _actor(request)
    response = import_result(
        session,
        candidate.external_search_result_id,
        expected_source_process_id=candidate.source_process_id,
        actor=actor,
        request=request,
    )
    candidate.process_id = response.process_id
    session.add(
        OpportunityEvent(
            id=uuid4(),
            opportunity_id=opportunity_id,
            event_type="OPPORTUNITY_IMPORTED",
            event_metadata={"process_id": str(response.process_id)},
            created_by=actor.id if actor else None,
        )
    )
    audit_event(
        session,
        event_type=OperationalAuditEventType.OPPORTUNITY_IMPORTED,
        action="opportunity.import",
        status=response.status.value,
        actor=actor,
        request=request,
        entity_type="opportunity_assessment",
        entity_id=opportunity_id,
    )
    session.commit()
    return response


@router.post(
    "/{opportunity_id}/request-deep-analysis",
    response_model=OpportunityDeepAnalysisResponse,
)
def request_deep_analysis(
    opportunity_id: UUID, request: Request, session: SessionDep
) -> OpportunityDeepAnalysisResponse:
    actor = _actor(request)
    if actor and not {
        AuthPermission.OPPORTUNITY_ASSESS,
        AuthPermission.OPPORTUNITY_REVIEW,
    }.intersection(actor.permissions):
        raise DomainError(
            AuthErrorCode.AUTH_PERMISSION_DENIED,
            "Permiso insuficiente.",
            status_code=HTTPStatus.FORBIDDEN,
        )
    response = deep_analysis_readiness(session, opportunity_id, actor)
    audit_event(
        session,
        event_type=OperationalAuditEventType.OPPORTUNITY_DEEP_ANALYSIS_REQUESTED,
        action="opportunity.deep_analysis.request",
        status="BLOCKED" if response.steps_blocked else "READY",
        actor=actor,
        request=request,
        entity_type="opportunity_assessment",
        entity_id=opportunity_id,
        metadata={"blocked_steps": len(response.steps_blocked)},
    )
    session.commit()
    return response
