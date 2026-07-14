"""API HTTP de monitores y alertas internas."""
# mypy: disable-error-code="no-untyped-def,no-untyped-call,arg-type"

from datetime import UTC, datetime, timedelta
from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from pliegocheck_api.auth import CurrentUser
from pliegocheck_api.config import Settings, get_settings
from pliegocheck_api.db import get_session
from pliegocheck_api.errors import DomainError
from pliegocheck_api.models import (
    OpportunityAlert,
    OpportunityAlertEvent,
    OpportunityAssessment,
    OpportunityCandidate,
    OpportunityMonitor,
    OpportunityMonitorRun,
)
from pliegocheck_schemas import (
    OpportunityAlertActionRequest,
    OpportunityAlertActionResponse,
    OpportunityAlertBulkActionRequest,
    OpportunityAlertDetail,
    OpportunityAlertDigest,
    OpportunityAlertList,
    OpportunityAlertSeverity,
    OpportunityAlertStatus,
    OpportunityAlertSummary,
    OpportunityAlertType,
    OpportunityAlertUnreadCount,
    OpportunityErrorCode,
    OpportunityMonitorCreateRequest,
    OpportunityMonitorDetail,
    OpportunityMonitoringReadiness,
    OpportunityMonitorList,
    OpportunityMonitorManualRunRequest,
    OpportunityMonitorManualRunResponse,
    OpportunityMonitorRunDetail,
    OpportunityMonitorRunSummary,
    OpportunityMonitorStatus,
    OpportunityMonitorSummary,
    OpportunityMonitorTriggerType,
    OpportunityMonitorUpdateRequest,
    OpportunityOutcome,
)

from .digest import digest_counts
from .service import (
    apply_alert_action,
    create_monitor,
    monitor_or_404,
    request_run,
    set_monitor_status,
    update_monitor,
)

router = APIRouter(tags=["opportunity-monitoring"])
SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def _actor(request: Request) -> CurrentUser | None:
    value = getattr(request.state, "current_user", None)
    return cast(CurrentUser, value) if value is not None else None


def _run(row: OpportunityMonitorRun, *, detail: bool = False):
    data = {
        key: getattr(row, key)
        for key in (
            "id",
            "monitor_id",
            "trigger_type",
            "status",
            "scheduled_for",
            "started_at",
            "finished_at",
            "discovery_run_id",
            "candidate_count",
            "new_candidate_count",
            "changed_candidate_count",
            "alert_count",
            "warning_count",
            "error_code",
            "error_message",
            "created_at",
        )
    }
    if detail:
        data["input_digest"] = row.input_digest
    return (OpportunityMonitorRunDetail if detail else OpportunityMonitorRunSummary).model_validate(
        data
    )


def _monitor(row: OpportunityMonitor, *, detail: bool = False, runs=None):
    keys = (
        "id",
        "name",
        "description",
        "company_profile_id",
        "company_snapshot_id",
        "policy_version",
        "policy_hash",
        "status",
        "frequency",
        "timezone",
        "source_systems",
        "last_run_at",
        "next_run_at",
        "last_success_at",
        "last_failure_at",
        "consecutive_failures",
        "baseline_run_id",
        "created_at",
        "updated_at",
    )
    data = {key: getattr(row, key) for key in keys}
    if detail:
        data.update(
            filters=row.filters,
            alert_rules=row.alert_rules,
            latest_runs=[_run(x) for x in (runs or [])],
        )
    return (OpportunityMonitorDetail if detail else OpportunityMonitorSummary).model_validate(data)


def _alert(row: OpportunityAlert, *, detail=False, events=None):
    keys = (
        "id",
        "monitor_id",
        "monitor_run_id",
        "opportunity_id",
        "assessment_id",
        "alert_type",
        "severity",
        "status",
        "title",
        "summary",
        "reason_code",
        "occurred_at",
        "first_seen_at",
        "last_seen_at",
        "read_at",
        "archived_at",
    )
    data = {key: getattr(row, key) for key in keys}
    if detail:
        data.update(
            explanation_parameters=row.explanation_parameters,
            alert_fingerprint=row.alert_fingerprint,
            events=[
                {
                    "event_type": x.event_type,
                    "metadata": x.event_metadata,
                    "created_at": x.created_at.isoformat(),
                }
                for x in (events or [])
            ],
        )
    return (OpportunityAlertDetail if detail else OpportunityAlertSummary).model_validate(data)


@router.get("/opportunity-monitoring/readiness", response_model=OpportunityMonitoringReadiness)
def readiness(session: SessionDep, settings: SettingsDep):
    active = (
        session.scalar(
            select(func.count())
            .select_from(OpportunityMonitor)
            .where(OpportunityMonitor.status == "ACTIVE")
        )
        or 0
    )
    pending = (
        session.scalar(
            select(func.count())
            .select_from(OpportunityMonitorRun)
            .where(OpportunityMonitorRun.status == "PENDING")
        )
        or 0
    )
    return OpportunityMonitoringReadiness(
        ready=settings.monitoring_enabled,
        enabled=settings.monitoring_enabled,
        active_monitors=active,
        pending_runs=pending,
        reasons=[]
        if settings.monitoring_enabled
        else ["El scheduler de monitoreo está deshabilitado por configuración."],
    )


@router.post("/opportunity-monitors", response_model=OpportunityMonitorDetail, status_code=201)
def create(payload: OpportunityMonitorCreateRequest, request: Request, session: SessionDep):
    return _monitor(create_monitor(session, payload, _actor(request)), detail=True)


@router.get("/opportunity-monitors", response_model=OpportunityMonitorList)
def monitors(
    session: SessionDep, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)
):
    total = session.scalar(select(func.count()).select_from(OpportunityMonitor)) or 0
    rows = session.scalars(
        select(OpportunityMonitor)
        .order_by(OpportunityMonitor.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return OpportunityMonitorList(
        items=[_monitor(x) for x in rows], total=total, limit=limit, offset=offset
    )


@router.get("/opportunity-monitors/{monitor_id}", response_model=OpportunityMonitorDetail)
def monitor_detail(monitor_id: UUID, session: SessionDep):
    row = monitor_or_404(session, monitor_id)
    runs = session.scalars(
        select(OpportunityMonitorRun)
        .where(OpportunityMonitorRun.monitor_id == monitor_id)
        .order_by(OpportunityMonitorRun.created_at.desc())
        .limit(10)
    ).all()
    return _monitor(row, detail=True, runs=runs)


@router.patch("/opportunity-monitors/{monitor_id}", response_model=OpportunityMonitorDetail)
def patch_monitor(
    monitor_id: UUID,
    payload: OpportunityMonitorUpdateRequest,
    request: Request,
    session: SessionDep,
):
    return _monitor(
        update_monitor(session, monitor_or_404(session, monitor_id), payload, _actor(request)),
        detail=True,
    )


@router.post("/opportunity-monitors/{monitor_id}/pause", response_model=OpportunityMonitorSummary)
def pause(monitor_id: UUID, request: Request, session: SessionDep):
    return _monitor(
        set_monitor_status(
            session,
            monitor_or_404(session, monitor_id),
            OpportunityMonitorStatus.PAUSED,
            _actor(request),
        )
    )


@router.post("/opportunity-monitors/{monitor_id}/resume", response_model=OpportunityMonitorSummary)
def resume(monitor_id: UUID, request: Request, session: SessionDep):
    return _monitor(
        set_monitor_status(
            session,
            monitor_or_404(session, monitor_id),
            OpportunityMonitorStatus.ACTIVE,
            _actor(request),
        )
    )


@router.post(
    "/opportunity-monitors/{monitor_id}/run",
    response_model=OpportunityMonitorManualRunResponse,
    status_code=202,
)
def manual_run(
    monitor_id: UUID,
    payload: OpportunityMonitorManualRunRequest,
    request: Request,
    session: SessionDep,
):
    row, reused = request_run(
        session,
        monitor_or_404(session, monitor_id),
        OpportunityMonitorTriggerType.MANUAL,
        _actor(request),
    )
    return OpportunityMonitorManualRunResponse(run=_run(row), reused=reused)


@router.get(
    "/opportunity-monitors/{monitor_id}/runs", response_model=list[OpportunityMonitorRunSummary]
)
def runs(monitor_id: UUID, session: SessionDep):
    monitor_or_404(session, monitor_id)
    return [
        _run(x)
        for x in session.scalars(
            select(OpportunityMonitorRun)
            .where(OpportunityMonitorRun.monitor_id == monitor_id)
            .order_by(OpportunityMonitorRun.created_at.desc())
        ).all()
    ]


@router.get(
    "/opportunity-monitors/{monitor_id}/runs/{run_id}", response_model=OpportunityMonitorRunDetail
)
def run_detail(monitor_id: UUID, run_id: UUID, session: SessionDep):
    row = session.scalar(
        select(OpportunityMonitorRun).where(
            OpportunityMonitorRun.id == run_id, OpportunityMonitorRun.monitor_id == monitor_id
        )
    )
    if row is None:
        raise DomainError(
            OpportunityErrorCode.OPPORTUNITY_NOT_FOUND, "La ejecución no existe.", status_code=404
        )
    return _run(row, detail=True)


@router.get("/opportunity-alerts/unread-count", response_model=OpportunityAlertUnreadCount)
def unread_count(session: SessionDep):
    return OpportunityAlertUnreadCount(
        count=session.scalar(
            select(func.count())
            .select_from(OpportunityAlert)
            .where(OpportunityAlert.status == "UNREAD")
        )
        or 0
    )


@router.get("/opportunity-alerts/digest", response_model=OpportunityAlertDigest)
def digest(
    session: SessionDep,
    period: str = Query("LAST_24_HOURS", pattern="^(TODAY|LAST_24_HOURS|LAST_7_DAYS)$"),
):
    now = datetime.now(UTC)
    start = (
        now.replace(hour=0, minute=0, second=0, microsecond=0)
        if period == "TODAY"
        else now - timedelta(days=7 if period == "LAST_7_DAYS" else 1)
    )
    values = session.scalars(
        select(OpportunityAlert.alert_type).where(OpportunityAlert.occurred_at >= start)
    ).all()
    return OpportunityAlertDigest(period=period, generated_at=now, **digest_counts(values))


@router.post("/opportunity-alerts/actions/bulk", response_model=OpportunityAlertActionResponse)
def bulk_action(payload: OpportunityAlertBulkActionRequest, request: Request, session: SessionDep):
    rows = list(
        session.scalars(select(OpportunityAlert).where(OpportunityAlert.id.in_(payload.alert_ids)))
    )
    return apply_alert_action(session, rows, payload.action, _actor(request))


@router.get("/opportunity-alerts", response_model=OpportunityAlertList)
def alerts(
    session: SessionDep,
    monitor_id: UUID | None = None,
    company_snapshot_id: UUID | None = None,
    alert_type: OpportunityAlertType | None = None,
    severity: OpportunityAlertSeverity | None = None,
    status: OpportunityAlertStatus | None = None,
    source_system: str | None = Query(default=None, pattern="^(SECOP_I|SECOP_II)$"),
    opportunity_outcome: OpportunityOutcome | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    closing_from: datetime | None = None,
    closing_to: datetime | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort: str = Query("newest", pattern="^(newest|oldest|severity|closing_date|compatibility)$"),
):
    filters = []
    if monitor_id:
        filters.append(OpportunityAlert.monitor_id == monitor_id)
    if company_snapshot_id:
        filters.append(
            OpportunityAlert.monitor_id.in_(
                select(OpportunityMonitor.id).where(
                    OpportunityMonitor.company_snapshot_id == company_snapshot_id
                )
            )
        )
    if alert_type:
        filters.append(OpportunityAlert.alert_type == alert_type.value)
    if severity:
        filters.append(OpportunityAlert.severity == severity.value)
    if status:
        filters.append(OpportunityAlert.status == status.value)
    candidate_ids = select(OpportunityAssessment.id).join(
        OpportunityCandidate,
        OpportunityCandidate.id == OpportunityAssessment.candidate_id,
    )
    if source_system:
        candidate_ids = candidate_ids.where(OpportunityCandidate.source_system == source_system)
    if opportunity_outcome:
        candidate_ids = candidate_ids.where(
            OpportunityAssessment.outcome == opportunity_outcome.value
        )
    if closing_from:
        candidate_ids = candidate_ids.where(OpportunityCandidate.closing_date >= closing_from)
    if closing_to:
        candidate_ids = candidate_ids.where(OpportunityCandidate.closing_date <= closing_to)
    if source_system or opportunity_outcome or closing_from or closing_to:
        filters.append(OpportunityAlert.assessment_id.in_(candidate_ids))
    if created_from:
        filters.append(OpportunityAlert.occurred_at >= created_from)
    if created_to:
        filters.append(OpportunityAlert.occurred_at <= created_to)
    order = (
        OpportunityAlert.occurred_at.asc()
        if sort == "oldest"
        else OpportunityAlert.occurred_at.desc()
    )
    total = session.scalar(select(func.count()).select_from(OpportunityAlert).where(*filters)) or 0
    rows = session.scalars(
        select(OpportunityAlert).where(*filters).order_by(order).offset(offset).limit(limit)
    ).all()
    return OpportunityAlertList(
        items=[_alert(x) for x in rows], total=total, limit=limit, offset=offset
    )


@router.get("/opportunity-alerts/{alert_id}", response_model=OpportunityAlertDetail)
def alert_detail(alert_id: UUID, session: SessionDep):
    row = session.get(OpportunityAlert, alert_id)
    if row is None:
        raise DomainError(
            OpportunityErrorCode.OPPORTUNITY_NOT_FOUND, "La alerta no existe.", status_code=404
        )
    events = session.scalars(
        select(OpportunityAlertEvent)
        .where(OpportunityAlertEvent.alert_id == alert_id)
        .order_by(OpportunityAlertEvent.created_at)
    ).all()
    return _alert(row, detail=True, events=events)


@router.post(
    "/opportunity-alerts/{alert_id}/actions", response_model=OpportunityAlertActionResponse
)
def alert_action(
    alert_id: UUID, payload: OpportunityAlertActionRequest, request: Request, session: SessionDep
):
    row = session.get(OpportunityAlert, alert_id)
    if row is None:
        raise DomainError(
            OpportunityErrorCode.OPPORTUNITY_NOT_FOUND, "La alerta no existe.", status_code=404
        )
    return apply_alert_action(session, [row], payload.action, _actor(request))
