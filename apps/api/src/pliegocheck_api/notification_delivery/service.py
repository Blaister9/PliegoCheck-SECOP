"""Outbox, selección, entrega, digests y retención de notificaciones."""
# mypy: disable-error-code="no-untyped-def,no-untyped-call,arg-type,type-arg"

import json
import os
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from time import monotonic
from uuid import UUID, uuid4

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from pliegocheck_api.auth import CurrentUser, audit_event
from pliegocheck_api.config import Settings
from pliegocheck_api.models import (
    NotificationDeliveryAttempt,
    NotificationDestination,
    NotificationDigestRun,
    NotificationOperationEvent,
    NotificationOutboxMessage,
    NotificationSubscription,
    OpportunityAlert,
    OpportunityAssessment,
    OpportunityCandidate,
    OpportunityMonitor,
)
from pliegocheck_schemas import (
    NotificationAttemptStatus,
    NotificationChannel,
    NotificationDeliveryMode,
    NotificationDigestPeriod,
    NotificationOutboxStatus,
    OperationalAuditEventType,
)

from .policy import (
    SEVERITY_RANK,
    digest_period_bounds,
    quiet_hours_end,
    retry_delay_seconds,
    subscription_matches,
)
from .providers import (
    ProviderResult,
    SignedWebhookNotificationProvider,
    SmtpNotificationProvider,
    prepare_webhook_request,
    render_email,
    validate_email,
)

TEMPLATE_VERSION = "v1"
DISCLAIMER = (
    "Esta alerta señala una novedad o cambio relevante según la configuración de PliegoCheck. "
    "No constituye una recomendación automática de presentar oferta ni representa probabilidad "
    "de adjudicación."
)
_TEMPLATE_DIR = Path(__file__).parents[5] / "config" / "notification-templates" / TEMPLATE_VERSION
TEMPLATE_HASH = sha256(
    b"\0".join(path.read_bytes() for path in sorted(_TEMPLATE_DIR.iterdir()) if path.is_file())
).hexdigest()


def canonical_hash(value) -> str:
    return sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
        ).encode()
    ).hexdigest()


def mask_destination(destination: NotificationDestination) -> str:
    if destination.email_address:
        local, domain = destination.email_address.rsplit("@", 1)
        return f"{local[:1]}***@{domain}"
    if destination.webhook_host:
        return f"https://{destination.webhook_host}/***"
    return "Interno"


def build_alert_payload(session: Session, alert: OpportunityAlert) -> dict:
    monitor = session.get(OpportunityMonitor, alert.monitor_id)
    assessment = (
        session.get(OpportunityAssessment, alert.assessment_id) if alert.assessment_id else None
    )
    candidate = session.get(OpportunityCandidate, assessment.candidate_id) if assessment else None
    opportunity_id = str(alert.opportunity_id) if alert.opportunity_id else None
    return {
        "schema_version": "1.0.0",
        "event_type": "OPPORTUNITY_ALERT",
        "occurred_at": alert.occurred_at.isoformat(),
        "severity": alert.severity,
        "title": alert.title,
        "summary": alert.summary,
        "alert": {
            "id": str(alert.id),
            "type": alert.alert_type,
            "title": alert.title,
            "summary": alert.summary,
            "reason_code": alert.reason_code,
            "status": alert.status,
        },
        "monitor": {"id": str(alert.monitor_id), "name": monitor.name if monitor else "Monitor"},
        "opportunity": {
            "id": opportunity_id,
            "source_system": candidate.source_system if candidate else None,
            "source_reference": candidate.source_reference if candidate else None,
            "entity_name": candidate.entity_name if candidate else None,
            "title": candidate.title if candidate else None,
            "outcome": assessment.outcome if assessment else None,
            "compatibility_score": str(assessment.compatibility_score) if assessment else None,
            "urgency_status": assessment.urgency_status if assessment else None,
            "closing_date": candidate.closing_date.isoformat()
            if candidate and candidate.closing_date
            else None,
        },
        "links": {
            "alert": f"/alerts/{alert.id}",
            "opportunity": f"/opportunities/{opportunity_id}" if opportunity_id else None,
            "secop": candidate.source_reference if candidate else None,
        },
        "opportunity_link": f"/opportunities/{opportunity_id}" if opportunity_id else "/alerts",
        "disclaimer": DISCLAIMER,
    }


def _idempotency(
    alert: OpportunityAlert | None,
    subscription,
    destination,
    event_type: str,
    period: str | None = None,
) -> str:
    return canonical_hash(
        {
            "alert_id": str(alert.id) if alert else None,
            "alert_fingerprint": alert.alert_fingerprint if alert else None,
            "subscription_id": str(subscription.id) if subscription else None,
            "destination_id": str(destination.id),
            "channel": destination.channel,
            "delivery_mode": subscription.delivery_mode if subscription else "IMMEDIATE",
            "template_version": TEMPLATE_VERSION,
            "event_type": event_type,
            "period": period,
        }
    )


def create_outbox(
    session: Session,
    *,
    destination: NotificationDestination,
    subscription=None,
    alert: OpportunityAlert | None = None,
    payload: dict,
    event_type: str,
    period: str | None = None,
    available_at: datetime | None = None,
    settings: Settings,
) -> tuple[NotificationOutboxMessage, bool]:
    key = _idempotency(alert, subscription, destination, event_type, period)
    existing = session.scalar(
        select(NotificationOutboxMessage).where(NotificationOutboxMessage.idempotency_key == key)
    )
    if existing:
        return existing, True
    now = datetime.now(UTC)
    row_id = uuid4()
    values = dict(
        id=row_id,
        alert_id=alert.id if alert else None,
        subscription_id=subscription.id if subscription else None,
        destination_id=destination.id,
        channel=destination.channel,
        delivery_mode=subscription.delivery_mode
        if subscription
        else NotificationDeliveryMode.IMMEDIATE.value,
        status=NotificationOutboxStatus.PENDING.value,
        event_type=event_type,
        scheduled_for=available_at or now,
        available_at=available_at or now,
        subject=str(payload.get("title", "Notificación PliegoCheck"))[:300],
        template_version=TEMPLATE_VERSION,
        template_hash=TEMPLATE_HASH,
        payload=payload,
        payload_hash=canonical_hash(payload),
        idempotency_key=key,
        attempt_count=0,
        max_attempts=settings.notification_max_attempts,
    )
    inserted_id = session.scalar(
        pg_insert(NotificationOutboxMessage)
        .values(**values)
        .on_conflict_do_nothing(index_elements=["idempotency_key"])
        .returning(NotificationOutboxMessage.id)
    )
    if inserted_id is None:
        reused = session.scalar(
            select(NotificationOutboxMessage).where(
                NotificationOutboxMessage.idempotency_key == key
            )
        )
        assert reused is not None
        return reused, True
    row = session.get(NotificationOutboxMessage, inserted_id)
    assert row is not None
    _event(
        session,
        "notification_outbox",
        row.id,
        "NOTIFICATION_OUTBOX_CREATED",
        {"channel": row.channel},
    )
    return row, False


def enqueue_for_alert(session: Session, alert: OpportunityAlert, settings: Settings) -> int:
    subscriptions = session.scalars(
        select(NotificationSubscription).where(
            NotificationSubscription.enabled.is_(True),
            NotificationSubscription.delivery_mode == NotificationDeliveryMode.IMMEDIATE.value,
        )
    ).all()
    payload = build_alert_payload(session, alert)
    created = 0
    for subscription in subscriptions:
        destination = session.get(NotificationDestination, subscription.destination_id)
        if not destination or destination.channel == NotificationChannel.INTERNAL_ONLY.value:
            continue
        if destination.status != "ACTIVE" or not subscription_matches(subscription, alert):
            continue
        available = quiet_hours_end(subscription, alert.severity, datetime.now(UTC))
        _, reused = create_outbox(
            session,
            destination=destination,
            subscription=subscription,
            alert=alert,
            payload=payload,
            event_type="OPPORTUNITY_ALERT",
            available_at=available,
            settings=settings,
        )
        created += int(not reused)
    return created


def _event(
    session: Session,
    entity_type: str,
    entity_id: UUID,
    event_type: str,
    metadata: dict,
    actor_id: UUID | None = None,
) -> None:
    session.add(
        NotificationOperationEvent(
            id=uuid4(),
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            event_metadata=metadata,
            created_by=actor_id,
        )
    )


def _suppression_reason(
    session: Session,
    row: NotificationOutboxMessage,
    destination: NotificationDestination,
    settings: Settings,
    now: datetime,
) -> str | None:
    if not settings.external_delivery_enabled:
        return "GLOBAL_KILL_SWITCH"
    if row.channel == NotificationChannel.EMAIL_SMTP.value and not settings.email_enabled:
        return "EMAIL_DISABLED"
    if row.channel == NotificationChannel.SIGNED_WEBHOOK.value and not settings.webhook_enabled:
        return "WEBHOOK_DISABLED"
    if destination.status != "ACTIVE":
        return "DESTINATION_INACTIVE"
    if settings.pilot_mode:
        if row.channel == NotificationChannel.EMAIL_SMTP.value:
            address = (destination.email_address or "").lower()
            domain = address.rsplit("@", 1)[-1]
            if (
                address not in settings.pilot_allowed_recipients
                and domain not in settings.pilot_allowed_recipient_domains
            ):
                return "PILOT_RECIPIENT_NOT_ALLOWED"
        today = now - timedelta(days=1)
        pilot_count = (
            session.scalar(
                select(func.count())
                .select_from(NotificationOutboxMessage)
                .where(
                    NotificationOutboxMessage.status.in_(["DELIVERED", "DRY_RUN"]),
                    NotificationOutboxMessage.created_at >= today,
                )
            )
            or 0
        )
        if pilot_count >= settings.pilot_max_deliveries_per_day:
            return "PILOT_DAILY_LIMIT"
    hour = now - timedelta(hours=1)
    day = now - timedelta(days=1)
    sent_statuses = [
        NotificationOutboxStatus.DELIVERED.value,
        NotificationOutboxStatus.DRY_RUN.value,
    ]
    per_hour = (
        session.scalar(
            select(func.count())
            .select_from(NotificationOutboxMessage)
            .where(
                NotificationOutboxMessage.destination_id == destination.id,
                NotificationOutboxMessage.status.in_(sent_statuses),
                NotificationOutboxMessage.delivered_at >= hour,
            )
        )
        or 0
    )
    per_day = (
        session.scalar(
            select(func.count())
            .select_from(NotificationOutboxMessage)
            .where(
                NotificationOutboxMessage.destination_id == destination.id,
                NotificationOutboxMessage.status.in_(sent_statuses),
                NotificationOutboxMessage.delivered_at >= day,
            )
        )
        or 0
    )
    global_hour = (
        session.scalar(
            select(func.count())
            .select_from(NotificationOutboxMessage)
            .where(
                NotificationOutboxMessage.status.in_(sent_statuses),
                NotificationOutboxMessage.delivered_at >= hour,
            )
        )
        or 0
    )
    if (
        per_hour >= settings.notification_max_per_destination_per_hour
        or per_day >= settings.notification_max_per_destination_per_day
        or global_hour >= settings.notification_max_global_per_hour
    ):
        return "RATE_LIMIT"
    return None


def claim_next(session: Session, now: datetime | None = None) -> NotificationOutboxMessage | None:
    current = now or datetime.now(UTC)
    stale = current - timedelta(minutes=10)
    row = session.scalar(
        select(NotificationOutboxMessage)
        .where(
            or_(
                NotificationOutboxMessage.status.in_(["PENDING", "FAILED_RETRYABLE"]),
                (NotificationOutboxMessage.status == "PROCESSING")
                & (NotificationOutboxMessage.updated_at < stale),
            ),
            NotificationOutboxMessage.available_at <= current,
        )
        .order_by(NotificationOutboxMessage.available_at, NotificationOutboxMessage.created_at)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if row:
        row.status = NotificationOutboxStatus.PROCESSING.value
        row.last_attempt_at = current
        session.commit()
        session.refresh(row)
    return row


def process_next(
    session: Session, settings: Settings, worker_id: str
) -> NotificationOutboxMessage | None:
    row = claim_next(session)
    if not row:
        return None
    destination = session.get(NotificationDestination, row.destination_id)
    assert destination is not None
    now = datetime.now(UTC)
    reason = _suppression_reason(session, row, destination, settings, now)
    if reason:
        row.status = NotificationOutboxStatus.SUPPRESSED.value
        row.last_error_code = reason
        _event(
            session, "notification_outbox", row.id, "NOTIFICATION_SUPPRESSED", {"reason": reason}
        )
        session.commit()
        return row
    started = monotonic()
    attempt_number = row.attempt_count + 1
    if settings.notification_dry_run:
        try:
            if row.channel == NotificationChannel.EMAIL_SMTP.value:
                validate_email(
                    destination.email_address or "", settings.smtp_allowed_recipient_domains
                )
                render_email(row.payload, str(row.id))
            else:
                secret = os.getenv(destination.secret_reference or "", "")
                if not secret:
                    raise ValueError("WEBHOOK_SECRET_UNAVAILABLE")
                prepare_webhook_request(
                    destination.webhook_url or "",
                    secret,
                    row.payload,
                    str(row.id),
                    row.idempotency_key,
                    str(int(now.timestamp())),
                    settings,
                )
            result = ProviderResult(True, error_code="DRY_RUN")
            attempt_status = NotificationAttemptStatus.DRY_RUN.value
        except ValueError as exc:
            result = ProviderResult(False, error_code=str(exc))
            attempt_status = NotificationAttemptStatus.PERMANENT.value
    elif row.channel == NotificationChannel.EMAIL_SMTP.value:
        result = SmtpNotificationProvider(settings).deliver(
            destination.email_address or "", row.payload, str(row.id)
        )
        attempt_status = (
            NotificationAttemptStatus.DELIVERED.value
            if result.delivered
            else (
                NotificationAttemptStatus.RETRYABLE.value
                if result.retryable
                else NotificationAttemptStatus.PERMANENT.value
            )
        )
    else:
        secret = os.getenv(destination.secret_reference or "", "")
        if not secret:
            result = ProviderResult(False, error_code="WEBHOOK_SECRET_UNAVAILABLE")
        else:
            result = SignedWebhookNotificationProvider(settings).deliver(
                destination.webhook_url or "",
                secret,
                row.payload,
                str(row.id),
                row.idempotency_key,
                str(int(now.timestamp())),
            )
        attempt_status = (
            NotificationAttemptStatus.DELIVERED.value
            if result.delivered
            else (
                NotificationAttemptStatus.RETRYABLE.value
                if result.retryable
                else NotificationAttemptStatus.PERMANENT.value
            )
        )
    row.attempt_count = attempt_number
    row.last_attempt_at = now
    session.add(
        NotificationDeliveryAttempt(
            id=uuid4(),
            outbox_message_id=row.id,
            attempt_number=attempt_number,
            status=attempt_status,
            started_at=now,
            finished_at=datetime.now(UTC),
            http_status=result.status_code if row.channel == "SIGNED_WEBHOOK" else None,
            smtp_response_code=result.status_code if row.channel == "EMAIL_SMTP" else None,
            provider_message_id=result.provider_message_id,
            latency_ms=int((monotonic() - started) * 1000),
            error_code=result.error_code,
            error_class="RETRYABLE"
            if result.retryable
            else ("PERMANENT" if not result.delivered else None),
            error_message_sanitized=(result.error_message or "")[:500] or None,
            response_metadata={"worker_id": worker_id},
        )
    )
    if settings.notification_dry_run and result.delivered:
        row.status = NotificationOutboxStatus.DRY_RUN.value
        row.delivered_at = now
    elif result.delivered:
        row.status = NotificationOutboxStatus.DELIVERED.value
        row.delivered_at = now
        _event(
            session,
            "notification_outbox",
            row.id,
            "NOTIFICATION_DELIVERED",
            {"channel": row.channel},
        )
    elif result.retryable and attempt_number < row.max_attempts:
        row.status = NotificationOutboxStatus.FAILED_RETRYABLE.value
        delay = result.retry_after or retry_delay_seconds(
            attempt_number,
            settings.notification_retry_base_seconds,
            settings.notification_retry_max_seconds,
            settings.notification_retry_jitter_seconds,
            row.idempotency_key,
        )
        row.available_at = now + timedelta(seconds=delay)
        row.failure_class = "RETRYABLE"
        row.last_error_code = result.error_code
        _event(
            session,
            "notification_outbox",
            row.id,
            "NOTIFICATION_RETRY_SCHEDULED",
            {"delay_seconds": delay},
        )
    else:
        row.status = NotificationOutboxStatus.FAILED_PERMANENT.value
        row.failure_class = "PERMANENT"
        row.last_error_code = result.error_code or "MAX_ATTEMPTS_EXHAUSTED"
        _event(
            session,
            "notification_outbox",
            row.id,
            "NOTIFICATION_FAILED_PERMANENT",
            {"attempt_count": attempt_number},
        )
    session.commit()
    return row


def manual_retry(
    session: Session, row: NotificationOutboxMessage, actor: CurrentUser | None
) -> None:
    row.status = NotificationOutboxStatus.PENDING.value
    row.available_at = datetime.now(UTC)
    row.cancelled_at = None
    row.failure_class = None
    row.last_error_code = None
    row.max_attempts = max(row.max_attempts, row.attempt_count + 1)
    _event(
        session,
        "notification_outbox",
        row.id,
        "NOTIFICATION_RETRIED_MANUALLY",
        {},
        actor.id if actor else None,
    )
    audit_event(
        session,
        event_type=OperationalAuditEventType.NOTIFICATION_RETRIED_MANUALLY,
        action="notification.retry",
        status="PENDING",
        actor=actor,
        entity_type="notification_outbox",
        entity_id=row.id,
        metadata={},
    )
    session.commit()


def cancel(session: Session, row: NotificationOutboxMessage, actor: CurrentUser | None) -> None:
    row.status = NotificationOutboxStatus.CANCELLED.value
    row.cancelled_at = datetime.now(UTC)
    _event(
        session,
        "notification_outbox",
        row.id,
        "NOTIFICATION_CANCELLED",
        {},
        actor.id if actor else None,
    )
    audit_event(
        session,
        event_type=OperationalAuditEventType.NOTIFICATION_CANCELLED,
        action="notification.cancel",
        status="CANCELLED",
        actor=actor,
        entity_type="notification_outbox",
        entity_id=row.id,
        metadata={},
    )
    session.commit()


def run_digests(
    session: Session,
    settings: Settings,
    period: NotificationDigestPeriod = NotificationDigestPeriod.DAILY,
    now: datetime | None = None,
) -> int:
    current = now or datetime.now(UTC)
    mode = (
        NotificationDeliveryMode.WEEKLY_DIGEST.value
        if period == NotificationDigestPeriod.WEEKLY
        else NotificationDeliveryMode.DAILY_DIGEST.value
    )
    subscriptions = session.scalars(
        select(NotificationSubscription).where(
            NotificationSubscription.enabled.is_(True),
            NotificationSubscription.delivery_mode == mode,
        )
    ).all()
    created = 0
    for sub in subscriptions:
        destination = session.get(NotificationDestination, sub.destination_id)
        if not destination or destination.status != "ACTIVE":
            continue
        start, end = digest_period_bounds(period.value, sub.timezone, current)
        alerts_query = select(OpportunityAlert).where(
            OpportunityAlert.occurred_at >= start,
            OpportunityAlert.occurred_at < end,
            OpportunityAlert.status != "ARCHIVED",
        )
        if sub.monitor_id is not None:
            alerts_query = alerts_query.where(OpportunityAlert.monitor_id == sub.monitor_id)
        candidate_alerts = list(
            session.scalars(alerts_query.order_by(OpportunityAlert.occurred_at.desc()))
        )
        matching_alerts = sorted(
            (alert for alert in candidate_alerts if subscription_matches(sub, alert)),
            key=lambda alert: (SEVERITY_RANK.get(alert.severity, 0), alert.occurred_at),
            reverse=True,
        )
        alerts = matching_alerts[: settings.notification_max_digest_alerts]
        if not alerts:
            continue
        digest_key = canonical_hash(
            {
                "destination": str(destination.id),
                "period": period.value,
                "start": start.isoformat(),
                "end": end.isoformat(),
            }
        )
        existing_digest = session.scalar(
            select(NotificationDigestRun.id).where(
                NotificationDigestRun.destination_id == destination.id,
                NotificationDigestRun.period == period.value,
                NotificationDigestRun.period_start == start,
                NotificationDigestRun.period_end == end,
            )
        )
        if existing_digest:
            continue
        digest = NotificationDigestRun(
            id=uuid4(),
            owner_actor_id=sub.owner_actor_id,
            destination_id=destination.id,
            period=period.value,
            period_start=start,
            period_end=end,
            status="COMPLETED",
            alert_count=len(alerts),
            input_digest=digest_key,
            started_at=current,
            finished_at=current,
        )
        session.add(digest)
        session.flush()
        payload = {
            "schema_version": "1.0.0",
            "event_type": "NOTIFICATION_DIGEST",
            "title": f"Digest {period.value.lower()} de PliegoCheck",
            "severity": "INFO",
            "summary": f"{len(alerts)} alertas en el periodo.",
            "alerts": [
                {"id": str(a.id), "type": a.alert_type, "severity": a.severity, "title": a.title}
                for a in alerts
            ],
            "omitted_count": max(0, len(matching_alerts) - len(alerts)),
            "opportunity_link": "/alerts",
            "disclaimer": DISCLAIMER,
        }
        outbox, _ = create_outbox(
            session,
            destination=destination,
            subscription=sub,
            payload=payload,
            event_type="NOTIFICATION_DIGEST",
            period=digest_key,
            settings=settings,
        )
        digest.outbox_message_id = outbox.id
        created += 1
    session.commit()
    return created


def run_retention(
    session: Session, settings: Settings, dry_run: bool, batch_size: int = 500
) -> tuple[int, int]:
    now = datetime.now(UTC)
    payload_cutoff = now - timedelta(days=settings.notification_payload_retention_days)
    attempt_cutoff = now - timedelta(days=settings.notification_attempt_retention_days)
    payload_ids = list(
        session.scalars(
            select(NotificationOutboxMessage.id)
            .where(
                NotificationOutboxMessage.created_at < payload_cutoff,
                NotificationOutboxMessage.payload["retained"].as_boolean().is_distinct_from(False),
            )
            .limit(batch_size)
        )
    )
    attempt_ids = list(
        session.scalars(
            select(NotificationDeliveryAttempt.id)
            .where(NotificationDeliveryAttempt.created_at < attempt_cutoff)
            .limit(batch_size)
        )
    )
    if not dry_run:
        if payload_ids:
            session.execute(
                update(NotificationOutboxMessage)
                .where(NotificationOutboxMessage.id.in_(payload_ids))
                .values(payload={"retained": False})
            )
        if attempt_ids:
            session.execute(
                delete(NotificationDeliveryAttempt).where(
                    NotificationDeliveryAttempt.id.in_(attempt_ids)
                )
            )
        _event(
            session,
            "notification_retention",
            uuid4(),
            "NOTIFICATION_RETENTION_EXECUTED",
            {"payloads_cleared": len(payload_ids), "attempts_deleted": len(attempt_ids)},
        )
        session.commit()
    return len(payload_ids), len(attempt_ids)
