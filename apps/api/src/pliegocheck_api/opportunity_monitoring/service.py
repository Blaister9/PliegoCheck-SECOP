"""Persistencia y orquestación de monitores sobre discovery existente."""
# mypy: disable-error-code="no-untyped-def,no-untyped-call"

import json
from datetime import UTC, datetime
from hashlib import sha256
from http import HTTPStatus
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from pliegocheck_api.auth import CurrentUser, audit_event
from pliegocheck_api.config import Settings
from pliegocheck_api.errors import DomainError
from pliegocheck_api.models import (
    OpportunityAlert,
    OpportunityAlertEvent,
    OpportunityAssessment,
    OpportunityCandidate,
    OpportunityMonitor,
    OpportunityMonitorCandidateState,
    OpportunityMonitorRun,
)
from pliegocheck_api.opportunities.policy import canonical_hash, load_policy
from pliegocheck_api.opportunities.service import enqueue_discovery, process_discovery_run
from pliegocheck_schemas import (
    OperationalAuditEventType,
    OpportunityAlertAction,
    OpportunityAlertActionResponse,
    OpportunityAlertRules,
    OpportunityAlertStatus,
    OpportunityDiscoveryRequest,
    OpportunityErrorCode,
    OpportunityMonitorCreateRequest,
    OpportunityMonitorFrequency,
    OpportunityMonitorRunStatus,
    OpportunityMonitorStatus,
    OpportunityMonitorTriggerType,
    OpportunityMonitorUpdateRequest,
)

from .alert_engine import alert_fingerprint, changed_alerts, initial_alerts
from .change_detection import detect_changes
from .models import CandidateSnapshot
from .scheduling import next_run_at


def create_monitor(
    session: Session, payload: OpportunityMonitorCreateRequest, actor: CurrentUser | None
) -> OpportunityMonitor:
    from pliegocheck_api.opportunities.service import _published_snapshot

    _published_snapshot(session, payload.company_profile_id, payload.company_snapshot_id)
    policy = load_policy()
    now = datetime.now(UTC)
    row = OpportunityMonitor(
        id=uuid4(),
        name=payload.name,
        description=payload.description,
        company_profile_id=payload.company_profile_id,
        company_snapshot_id=payload.company_snapshot_id,
        policy_version=policy.version,
        policy_hash=policy.policy_hash,
        status=OpportunityMonitorStatus.ACTIVE.value,
        frequency=payload.frequency.value,
        timezone=payload.timezone,
        filters=payload.filters.model_dump(mode="json"),
        source_systems=[x.value for x in payload.source_systems],
        alert_rules=payload.alert_rules.model_dump(mode="json"),
        next_run_at=now,
        created_by=actor.id if actor else None,
    )
    session.add(row)
    session.flush()
    audit_event(
        session,
        event_type=OperationalAuditEventType.OPPORTUNITY_MONITOR_CREATED,
        action="opportunity_monitor.create",
        status="CREATED",
        actor=actor,
        entity_type="opportunity_monitor",
        entity_id=row.id,
        metadata={"frequency": row.frequency, "source_systems": row.source_systems},
    )
    session.commit()
    session.refresh(row)
    return row


def update_monitor(
    session: Session,
    row: OpportunityMonitor,
    payload: OpportunityMonitorUpdateRequest,
    actor: CurrentUser | None,
) -> OpportunityMonitor:
    changes = payload.model_dump(exclude_unset=True)
    if payload.company_snapshot_id and payload.company_snapshot_id != row.company_snapshot_id:
        from pliegocheck_api.opportunities.service import _published_snapshot

        _published_snapshot(session, row.company_profile_id, payload.company_snapshot_id)
        row.baseline_run_id = None
    for key, value in changes.items():
        if key in {"frequency"}:
            value = value.value
        elif key == "source_systems":
            value = [x.value for x in value]
        elif key in {"filters", "alert_rules"}:
            value = value.model_dump(mode="json")
        setattr(row, key, value)
    row.updated_at = datetime.now(UTC)
    audit_event(
        session,
        event_type=OperationalAuditEventType.OPPORTUNITY_MONITOR_UPDATED,
        action="opportunity_monitor.update",
        status="UPDATED",
        actor=actor,
        entity_type="opportunity_monitor",
        entity_id=row.id,
        metadata={"fields": sorted(changes)},
    )
    session.commit()
    session.refresh(row)
    return row


def monitor_or_404(session: Session, monitor_id: UUID) -> OpportunityMonitor:
    row = session.get(OpportunityMonitor, monitor_id)
    if row is None:
        raise DomainError(
            OpportunityErrorCode.OPPORTUNITY_NOT_FOUND,
            "El monitor no existe.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return row


def set_monitor_status(
    session: Session,
    row: OpportunityMonitor,
    status: OpportunityMonitorStatus,
    actor: CurrentUser | None,
) -> OpportunityMonitor:
    row.status = status.value
    if status == OpportunityMonitorStatus.ACTIVE:
        row.next_run_at = datetime.now(UTC)
    event = (
        OperationalAuditEventType.OPPORTUNITY_MONITOR_PAUSED
        if status == OpportunityMonitorStatus.PAUSED
        else OperationalAuditEventType.OPPORTUNITY_MONITOR_RESUMED
    )
    audit_event(
        session,
        event_type=event,
        action=f"opportunity_monitor.{status.value.lower()}",
        status=status.value,
        actor=actor,
        entity_type="opportunity_monitor",
        entity_id=row.id,
        metadata={},
    )
    session.commit()
    session.refresh(row)
    return row


def request_run(
    session: Session,
    monitor: OpportunityMonitor,
    trigger: OpportunityMonitorTriggerType,
    actor: CurrentUser | None = None,
    *,
    scheduled_for: datetime | None = None,
    commit: bool = True,
) -> tuple[OpportunityMonitorRun, bool]:
    existing = session.scalar(
        select(OpportunityMonitorRun)
        .where(
            OpportunityMonitorRun.monitor_id == monitor.id,
            OpportunityMonitorRun.status.in_(
                [
                    OpportunityMonitorRunStatus.PENDING.value,
                    OpportunityMonitorRunStatus.PROCESSING.value,
                ]
            ),
        )
        .limit(1)
    )
    if existing:
        return existing, True
    scheduled = scheduled_for or datetime.now(UTC)
    actual_trigger = (
        OpportunityMonitorTriggerType.BASELINE if monitor.baseline_run_id is None else trigger
    )
    digest = canonical_hash(
        {
            "monitor": str(monitor.id),
            "scheduled_for": scheduled.isoformat(),
            "trigger": actual_trigger.value,
            "snapshot": str(monitor.company_snapshot_id),
            "policy_hash": monitor.policy_hash,
        }
    )
    row = OpportunityMonitorRun(
        id=uuid4(),
        monitor_id=monitor.id,
        trigger_type=actual_trigger.value,
        status=OpportunityMonitorRunStatus.PENDING.value,
        scheduled_for=scheduled,
        input_digest=digest,
    )
    session.add(row)
    audit_event(
        session,
        event_type=OperationalAuditEventType.OPPORTUNITY_MONITOR_RUN_REQUESTED,
        action="opportunity_monitor.run.request",
        status="PENDING",
        actor=actor,
        entity_type="opportunity_monitor_run",
        entity_id=row.id,
        metadata={"trigger": actual_trigger.value},
    )
    if commit:
        session.commit()
        session.refresh(row)
    else:
        session.flush()
    return row, False


def scheduler_tick(
    session: Session, settings: Settings, *, now: datetime | None = None
) -> list[OpportunityMonitorRun]:
    if not settings.monitoring_enabled:
        return []
    current = now or datetime.now(UTC)
    monitors = list(
        session.scalars(
            select(OpportunityMonitor)
            .where(
                OpportunityMonitor.status == OpportunityMonitorStatus.ACTIVE.value,
                OpportunityMonitor.next_run_at <= current,
            )
            .order_by(OpportunityMonitor.next_run_at)
            .with_for_update(skip_locked=True)
            .limit(settings.monitor_max_active_runs)
        )
    )
    runs = []
    for monitor in monitors:
        scheduled = monitor.next_run_at or current
        try:
            run, reused = request_run(
                session,
                monitor,
                OpportunityMonitorTriggerType.SCHEDULED,
                scheduled_for=scheduled,
                commit=False,
            )
            if not reused:
                runs.append(run)
        except IntegrityError:
            session.rollback()
            continue
        monitor.next_run_at = next_run_at(
            scheduled, OpportunityMonitorFrequency(monitor.frequency), monitor.timezone, now=current
        )
        session.commit()
    return runs


def process_next_monitor_run(
    session: Session, settings: Settings, worker_id: str
) -> OpportunityMonitorRun | None:
    row = session.scalar(
        select(OpportunityMonitorRun)
        .where(OpportunityMonitorRun.status == OpportunityMonitorRunStatus.PENDING.value)
        .order_by(OpportunityMonitorRun.created_at)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if row is None:
        return None
    row.status = OpportunityMonitorRunStatus.PROCESSING.value
    row.started_at = datetime.now(UTC)
    session.commit()
    monitor = monitor_or_404(session, row.monitor_id)
    try:
        _process(session, settings, monitor, row)
    except Exception:
        session.rollback()
        row = session.get(OpportunityMonitorRun, row.id)
        restored_monitor = session.get(OpportunityMonitor, monitor.id)
        assert row is not None and restored_monitor is not None
        monitor = restored_monitor
        now = datetime.now(UTC)
        row.status = OpportunityMonitorRunStatus.FAILED.value
        row.finished_at = now
        row.error_code = "DISCOVERY_FAILED"
        row.error_message = "No fue posible completar el monitoreo."
        monitor.last_failure_at = now
        monitor.consecutive_failures += 1
        threshold = settings.monitor_failure_alert_threshold
        if monitor.consecutive_failures >= threshold:
            monitor.status = OpportunityMonitorStatus.ERROR.value
            _system_alert(
                session,
                monitor,
                row,
                "MONITOR_FAILURE",
                "CRITICAL",
                "Monitor con fallos repetidos",
                "El monitor dejó de consultar después de fallos consecutivos.",
                f"failure:{monitor.consecutive_failures // threshold}",
            )
        audit_event(
            session,
            event_type=OperationalAuditEventType.OPPORTUNITY_MONITOR_RUN_FAILED,
            action="opportunity_monitor.run",
            status="FAILED",
            entity_type="opportunity_monitor_run",
            entity_id=row.id,
            metadata={"error_code": row.error_code},
        )
        session.commit()
        return row
    return row


def _process(
    session: Session, settings: Settings, monitor: OpportunityMonitor, run: OpportunityMonitorRun
) -> None:
    filters = monitor.filters
    payload = OpportunityDiscoveryRequest(
        company_profile_id=monitor.company_profile_id,
        company_snapshot_id=monitor.company_snapshot_id,
        search_requests=filters.get("search_requests", []),
        candidate_ids=filters.get("candidate_ids", []),
        effective_at=run.scheduled_for,
        force=True,
    )
    discovery = enqueue_discovery(session, payload, actor=None, settings=settings)
    discovery_row = session.get(
        __import__(
            "pliegocheck_api.models", fromlist=["OpportunityDiscoveryRun"]
        ).OpportunityDiscoveryRun,
        discovery.run.id,
    )
    assert discovery_row is not None
    process_discovery_run(session, settings, discovery_row)
    run.discovery_run_id = discovery_row.id
    pairs = session.execute(
        select(OpportunityCandidate, OpportunityAssessment)
        .join(OpportunityAssessment, OpportunityAssessment.candidate_id == OpportunityCandidate.id)
        .where(OpportunityCandidate.discovery_run_id == discovery_row.id)
    ).all()
    rules = OpportunityAlertRules.model_validate(monitor.alert_rules)
    new_count = changed_count = alert_count = 0
    baseline = monitor.baseline_run_id is None and not rules.alert_on_initial_results
    now = datetime.now(UTC)
    for candidate, assessment in pairs:
        current = _snapshot(candidate, assessment)
        state = session.scalar(
            select(OpportunityMonitorCandidateState).where(
                OpportunityMonitorCandidateState.monitor_id == monitor.id,
                OpportunityMonitorCandidateState.source_system == candidate.source_system,
                OpportunityMonitorCandidateState.source_process_id == candidate.source_process_id,
            )
        )
        decisions = []
        if state is None:
            new_count += 1
            if not baseline:
                decisions = initial_alerts(current, rules)
            state = OpportunityMonitorCandidateState(
                id=uuid4(),
                monitor_id=monitor.id,
                source_system=current.source_system,
                source_process_id=current.source_process_id,
                opportunity_id=assessment.id,
                assessment_id=assessment.id,
                outcome=current.outcome,
                compatibility_score=current.compatibility_score,
                urgency_status=current.urgency_status,
                information_completeness=current.information_completeness,
                closing_date=current.closing_date,
                document_state_hash=current.document_state_hash,
                assessment_digest=current.assessment_digest,
                source_status=current.source_status,
                addendum_status=current.addendum_status,
                first_seen_at=now,
                last_seen_at=now,
                is_active=True,
            )
            session.add(state)
        else:
            previous = _snapshot_from_state(state)
            changes = detect_changes(previous, current)
            if changes:
                changed_count += 1
                decisions = changed_alerts(current, changes, rules)
            for field in (
                "opportunity_id",
                "assessment_id",
                "outcome",
                "compatibility_score",
                "urgency_status",
                "information_completeness",
                "closing_date",
                "document_state_hash",
                "assessment_digest",
                "source_status",
                "addendum_status",
            ):
                setattr(state, field, getattr(current, field))
            state.last_seen_at = now
            state.is_active = True
        for decision in decisions:
            fingerprint = alert_fingerprint(
                str(monitor.id),
                current,
                decision,
                monitor.policy_hash,
                str(monitor.company_snapshot_id),
            )
            existing = session.scalar(
                select(OpportunityAlert).where(OpportunityAlert.alert_fingerprint == fingerprint)
            )
            if existing:
                existing.last_seen_at = now
            else:
                alert = OpportunityAlert(
                    id=uuid4(),
                    monitor_id=monitor.id,
                    monitor_run_id=run.id,
                    opportunity_id=assessment.id,
                    assessment_id=assessment.id,
                    alert_type=decision.alert_type,
                    severity=decision.severity,
                    status=OpportunityAlertStatus.UNREAD.value,
                    title=decision.title,
                    summary=decision.summary,
                    reason_code=decision.reason_code,
                    explanation_parameters=decision.parameters,
                    alert_fingerprint=fingerprint,
                    occurred_at=now,
                    first_seen_at=now,
                    last_seen_at=now,
                    created_by_system=True,
                )
                session.add(alert)
                session.flush()
                alert_count += 1
                state.last_alerted_at = now
                session.add(
                    OpportunityAlertEvent(
                        id=uuid4(), alert_id=alert.id, event_type="CREATED", event_metadata={}
                    )
                )
                audit_event(
                    session,
                    event_type=OperationalAuditEventType.OPPORTUNITY_ALERT_CREATED,
                    action="opportunity_alert.create",
                    status="UNREAD",
                    entity_type="opportunity_alert",
                    entity_id=alert.id,
                    metadata={"alert_type": alert.alert_type, "severity": alert.severity},
                )
    recovered = monitor.consecutive_failures > 0
    run.candidate_count = len(pairs)
    run.new_candidate_count = new_count
    run.changed_candidate_count = changed_count
    run.alert_count = alert_count
    run.warning_count = discovery_row.warning_count
    run.status = (
        OpportunityMonitorRunStatus.COMPLETED_WITH_WARNINGS.value
        if run.warning_count
        else OpportunityMonitorRunStatus.COMPLETED.value
    )
    run.finished_at = now
    monitor.last_run_at = now
    monitor.last_success_at = now
    monitor.consecutive_failures = 0
    if monitor.status == OpportunityMonitorStatus.ERROR.value:
        monitor.status = OpportunityMonitorStatus.ACTIVE.value
    if monitor.baseline_run_id is None:
        monitor.baseline_run_id = run.id
    if recovered:
        _system_alert(
            session,
            monitor,
            run,
            "MONITOR_RECOVERED",
            "INFO",
            "Monitor recuperado",
            "El monitor volvió a completar una consulta.",
            f"recovered:{run.id}",
        )
    audit_event(
        session,
        event_type=OperationalAuditEventType.OPPORTUNITY_MONITOR_RUN_COMPLETED,
        action="opportunity_monitor.run",
        status=run.status,
        entity_type="opportunity_monitor_run",
        entity_id=run.id,
        metadata={"candidate_count": run.candidate_count, "alert_count": run.alert_count},
    )
    session.commit()


def _snapshot(candidate, assessment) -> CandidateSnapshot:
    document_hash = sha256(
        json.dumps(
            {"status": candidate.document_status, "reference": candidate.source_reference},
            sort_keys=True,
        ).encode()
    ).hexdigest()
    return CandidateSnapshot(
        candidate.source_system,
        candidate.source_process_id,
        str(assessment.id),
        str(assessment.id),
        assessment.outcome,
        assessment.compatibility_score,
        assessment.urgency_status,
        assessment.information_completeness,
        candidate.closing_date,
        document_hash,
        assessment.input_digest,
        candidate.source_status,
        None,
    )


def _snapshot_from_state(state) -> CandidateSnapshot:
    return CandidateSnapshot(
        state.source_system,
        state.source_process_id,
        str(state.opportunity_id),
        str(state.assessment_id),
        state.outcome,
        state.compatibility_score,
        state.urgency_status,
        state.information_completeness,
        state.closing_date,
        state.document_state_hash,
        state.assessment_digest,
        state.source_status,
        state.addendum_status,
    )


def _system_alert(session, monitor, run, kind, severity, title, summary, identity):
    fingerprint = canonical_hash(
        {
            "monitor": str(monitor.id),
            "type": kind,
            "identity": identity,
            "policy": monitor.policy_hash,
            "snapshot": str(monitor.company_snapshot_id),
        }
    )
    existing = session.scalar(
        select(OpportunityAlert).where(OpportunityAlert.alert_fingerprint == fingerprint)
    )
    now = datetime.now(UTC)
    if existing:
        existing.last_seen_at = now
        return existing
    alert = OpportunityAlert(
        id=uuid4(),
        monitor_id=monitor.id,
        monitor_run_id=run.id,
        alert_type=kind,
        severity=severity,
        status="UNREAD",
        title=title,
        summary=summary,
        reason_code=kind,
        explanation_parameters={},
        alert_fingerprint=fingerprint,
        occurred_at=now,
        first_seen_at=now,
        last_seen_at=now,
        created_by_system=True,
    )
    session.add(alert)
    session.flush()
    session.add(
        OpportunityAlertEvent(
            id=uuid4(), alert_id=alert.id, event_type="CREATED", event_metadata={}
        )
    )
    return alert


def apply_alert_action(
    session: Session,
    alerts: list[OpportunityAlert],
    action: OpportunityAlertAction,
    actor: CurrentUser | None,
) -> OpportunityAlertActionResponse:
    now = datetime.now(UTC)
    mapping = {
        OpportunityAlertAction.MARK_READ: "READ",
        OpportunityAlertAction.MARK_UNREAD: "UNREAD",
        OpportunityAlertAction.ARCHIVE: "ARCHIVED",
        OpportunityAlertAction.RESTORE: "UNREAD",
        OpportunityAlertAction.RESOLVE: "RESOLVED",
    }
    status = mapping[action]
    for alert in alerts:
        alert.status = status
        alert.read_at = now if status == "READ" else None
        alert.archived_at = now if status == "ARCHIVED" else None
        session.add(
            OpportunityAlertEvent(
                id=uuid4(),
                alert_id=alert.id,
                event_type=action.value,
                event_metadata={},
                created_by=actor.id if actor else None,
            )
        )
        event = (
            OperationalAuditEventType.OPPORTUNITY_ALERT_READ
            if action in {OpportunityAlertAction.MARK_READ, OpportunityAlertAction.MARK_UNREAD}
            else (
                OperationalAuditEventType.OPPORTUNITY_ALERT_ARCHIVED
                if action in {OpportunityAlertAction.ARCHIVE, OpportunityAlertAction.RESTORE}
                else OperationalAuditEventType.OPPORTUNITY_ALERT_RESOLVED
            )
        )
        audit_event(
            session,
            event_type=event,
            action=f"opportunity_alert.{action.value.lower()}",
            status=status,
            actor=actor,
            entity_type="opportunity_alert",
            entity_id=alert.id,
            metadata={},
        )
    session.commit()
    return OpportunityAlertActionResponse(
        updated_ids=[x.id for x in alerts], status=OpportunityAlertStatus(status)
    )
