"""API de destinos, suscripciones, outbox y operación de notificaciones."""
# mypy: ignore-errors

from datetime import UTC, datetime, timedelta
from typing import Annotated, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from pliegocheck_api.auth import CurrentUser, audit_event
from pliegocheck_api.config import Settings, get_settings
from pliegocheck_api.db import get_session
from pliegocheck_api.models import (
    NotificationDeliveryAttempt,
    NotificationDestination,
    NotificationDigestRun,
    NotificationOperationEvent,
    NotificationOutboxMessage,
    NotificationSubscription,
)
from pliegocheck_schemas import (
    AuthPermission,
    NotificationAttemptSummary,
    NotificationDeliveryDetail,
    NotificationDeliveryList,
    NotificationDeliverySummary,
    NotificationDestinationCreateRequest,
    NotificationDestinationDetail,
    NotificationDestinationList,
    NotificationDestinationStatus,
    NotificationDestinationSummary,
    NotificationDestinationUpdateRequest,
    NotificationDigestPeriod,
    NotificationDigestSummary,
    NotificationOperationResponse,
    NotificationOutboxStatus,
    NotificationReadiness,
    NotificationRetentionRequest,
    NotificationRetentionResponse,
    NotificationStatistics,
    NotificationSubscriptionCreateRequest,
    NotificationSubscriptionDetail,
    NotificationSubscriptionList,
    NotificationSubscriptionSummary,
    NotificationSubscriptionUpdateRequest,
    NotificationTestRequest,
    NotificationTestResponse,
    OperationalAuditEventType,
)

from .providers import validate_email, validate_webhook_url
from .service import (
    DISCLAIMER,
    cancel,
    create_outbox,
    manual_retry,
    mask_destination,
    run_digests,
    run_retention,
)

router = APIRouter(tags=["notification-delivery"])
SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def _actor(request: Request) -> CurrentUser | None:
    value = getattr(request.state, "current_user", None)
    return cast(CurrentUser, value) if value is not None else None


def _admin(actor: CurrentUser | None) -> bool:
    return actor is None or AuthPermission.NOTIFICATION_ADMIN in actor.permissions


def _owned(row, actor: CurrentUser | None) -> None:
    if actor is not None and row.owner_actor_id != actor.id and not _admin(actor):
        raise HTTPException(status_code=403, detail="No puede operar una configuración ajena.")


def _destination(row: NotificationDestination, detail: bool = False):
    data = dict(
        id=row.id,
        owner_actor_id=row.owner_actor_id,
        channel=row.channel,
        name=row.name,
        status=row.status,
        masked_destination=mask_destination(row),
        verified_at=row.verified_at,
        last_tested_at=row.last_tested_at,
        last_test_status=row.last_test_status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
    if detail:
        data.update(configuration=row.configuration, secret_configured=bool(row.secret_reference))
    return (
        NotificationDestinationDetail if detail else NotificationDestinationSummary
    ).model_validate(data)


def _subscription(row: NotificationSubscription, detail: bool = False):
    data = {
        key: getattr(row, key)
        for key in (
            "id",
            "owner_actor_id",
            "destination_id",
            "monitor_id",
            "enabled",
            "delivery_mode",
            "minimum_severity",
            "alert_types",
            "timezone",
            "created_at",
            "updated_at",
        )
    }
    if detail:
        data.update(
            quiet_hours=row.quiet_hours,
            daily_digest_time=row.daily_digest_time,
            weekly_digest_day=row.weekly_digest_day,
            include_summary=row.include_summary,
            include_opportunity_link=row.include_opportunity_link,
        )
    return (
        NotificationSubscriptionDetail if detail else NotificationSubscriptionSummary
    ).model_validate(data)


def _delivery(session: Session, row: NotificationOutboxMessage, detail: bool = False):
    destination = session.get(NotificationDestination, row.destination_id)
    assert destination is not None
    data = dict(
        id=row.id,
        alert_id=row.alert_id,
        destination_id=row.destination_id,
        channel=row.channel,
        delivery_mode=row.delivery_mode,
        status=row.status,
        masked_destination=mask_destination(destination),
        attempt_count=row.attempt_count,
        available_at=row.available_at,
        delivered_at=row.delivered_at,
        last_error_code=row.last_error_code,
        created_at=row.created_at,
    )
    if detail:
        attempts = session.scalars(
            select(NotificationDeliveryAttempt)
            .where(NotificationDeliveryAttempt.outbox_message_id == row.id)
            .order_by(NotificationDeliveryAttempt.attempt_number)
        ).all()
        data.update(
            subject=row.subject,
            template_version=row.template_version,
            payload_metadata={
                "event_type": row.event_type,
                "payload_hash": row.payload_hash,
                "retained": row.payload.get("retained", True),
            },
            attempts=[
                NotificationAttemptSummary.model_validate(
                    {
                        key: getattr(item, key)
                        for key in (
                            "id",
                            "attempt_number",
                            "status",
                            "started_at",
                            "finished_at",
                            "http_status",
                            "smtp_response_code",
                            "latency_ms",
                            "error_code",
                            "error_message_sanitized",
                        )
                    }
                )
                for item in attempts
            ],
        )
    return (NotificationDeliveryDetail if detail else NotificationDeliverySummary).model_validate(
        data
    )


@router.get("/notification-delivery/readiness", response_model=NotificationReadiness)
def readiness(session: SessionDep, settings: SettingsDep):
    now = datetime.now(UTC)
    counts = dict(
        session.execute(
            select(NotificationOutboxMessage.status, func.count()).group_by(
                NotificationOutboxMessage.status
            )
        ).all()
    )
    oldest = session.scalar(
        select(func.min(NotificationOutboxMessage.available_at)).where(
            NotificationOutboxMessage.status.in_(["PENDING", "FAILED_RETRYABLE"])
        )
    )
    delivered = (
        session.scalar(
            select(func.count())
            .select_from(NotificationOutboxMessage)
            .where(
                NotificationOutboxMessage.status == "DELIVERED",
                NotificationOutboxMessage.delivered_at >= now - timedelta(days=1),
            )
        )
        or 0
    )
    suppressed = (
        session.scalar(
            select(func.count())
            .select_from(NotificationOutboxMessage)
            .where(
                NotificationOutboxMessage.status == "SUPPRESSED",
                NotificationOutboxMessage.updated_at >= now - timedelta(days=1),
            )
        )
        or 0
    )
    last_attempt = session.scalar(select(func.max(NotificationDeliveryAttempt.created_at)))
    last_digest = session.scalar(select(func.max(NotificationDigestRun.finished_at)))
    reasons = []
    if not settings.external_delivery_enabled:
        reasons.append("Entrega externa deshabilitada por configuración operativa.")
    if settings.notification_dry_run:
        reasons.append("Modo dry-run activo: no se abren conexiones externas.")
    return NotificationReadiness(
        external_delivery_enabled=settings.external_delivery_enabled,
        dry_run=settings.notification_dry_run,
        email_enabled=settings.email_enabled,
        webhook_enabled=settings.webhook_enabled,
        pending_count=counts.get("PENDING", 0),
        processing_count=counts.get("PROCESSING", 0),
        retryable_count=counts.get("FAILED_RETRYABLE", 0),
        permanent_failure_count=counts.get("FAILED_PERMANENT", 0),
        delivered_last_24h=delivered,
        suppressed_last_24h=suppressed,
        oldest_pending_age_seconds=max(0, int((now - oldest).total_seconds())) if oldest else None,
        worker_last_seen=last_attempt,
        digest_last_run=last_digest,
        retention_last_run=session.scalar(
            select(func.max(NotificationOperationEvent.created_at)).where(
                NotificationOperationEvent.event_type == "NOTIFICATION_RETENTION_EXECUTED"
            )
        ),
        reasons=reasons,
    )


@router.get("/notification-delivery/statistics", response_model=NotificationStatistics)
def statistics(session: SessionDep):
    return NotificationStatistics(
        by_status=dict(
            session.execute(
                select(NotificationOutboxMessage.status, func.count()).group_by(
                    NotificationOutboxMessage.status
                )
            ).all()
        ),
        by_channel=dict(
            session.execute(
                select(NotificationOutboxMessage.channel, func.count()).group_by(
                    NotificationOutboxMessage.channel
                )
            ).all()
        ),
        generated_at=datetime.now(UTC),
    )


@router.post(
    "/notification-destinations", response_model=NotificationDestinationDetail, status_code=201
)
def create_destination(
    payload: NotificationDestinationCreateRequest,
    request: Request,
    session: SessionDep,
    settings: SettingsDep,
):
    actor = _actor(request)
    email = (
        validate_email(payload.email_address, settings.smtp_allowed_recipient_domains)
        if payload.email_address
        else None
    )
    host = None
    if payload.webhook_url:
        host, _ = validate_webhook_url(payload.webhook_url, settings)
    if payload.secret_reference and not _admin(actor):
        raise HTTPException(status_code=403, detail="Solo ADMIN configura referencias de secreto.")
    row = NotificationDestination(
        id=uuid4(),
        owner_actor_id=actor.id if actor else None,
        channel=payload.channel.value,
        name=payload.name,
        status=NotificationDestinationStatus.ACTIVE.value,
        email_address=email,
        webhook_url=payload.webhook_url,
        webhook_host=host,
        secret_reference=payload.secret_reference,
        configuration=payload.configuration,
        created_by=actor.id if actor else None,
    )
    session.add(row)
    session.flush()
    audit_event(
        session,
        event_type=OperationalAuditEventType.NOTIFICATION_DESTINATION_CREATED,
        action="notification.destination.create",
        status="CREATED",
        actor=actor,
        entity_type="notification_destination",
        entity_id=row.id,
        metadata={"channel": row.channel},
    )
    session.commit()
    session.refresh(row)
    return _destination(row, True)


@router.get("/notification-destinations", response_model=NotificationDestinationList)
def list_destinations(request: Request, session: SessionDep):
    actor = _actor(request)
    query = select(NotificationDestination).order_by(NotificationDestination.created_at.desc())
    if actor and not _admin(actor):
        query = query.where(NotificationDestination.owner_actor_id == actor.id)
    rows = list(session.scalars(query))
    return NotificationDestinationList(items=[_destination(x) for x in rows], total=len(rows))


@router.get(
    "/notification-destinations/{destination_id}", response_model=NotificationDestinationDetail
)
def destination_detail(destination_id: UUID, request: Request, session: SessionDep):
    row = session.get(NotificationDestination, destination_id)
    if not row:
        raise HTTPException(404, "Destino no encontrado.")
    _owned(row, _actor(request))
    return _destination(row, True)


@router.patch(
    "/notification-destinations/{destination_id}", response_model=NotificationDestinationDetail
)
def update_destination(
    destination_id: UUID,
    payload: NotificationDestinationUpdateRequest,
    request: Request,
    session: SessionDep,
    settings: SettingsDep,
):
    row = session.get(NotificationDestination, destination_id)
    if not row:
        raise HTTPException(404, "Destino no encontrado.")
    actor = _actor(request)
    _owned(row, actor)
    changes = payload.model_dump(exclude_unset=True)
    if "secret_reference" in changes and not _admin(actor):
        raise HTTPException(403, "Solo ADMIN configura referencias de secreto.")
    if changes.get("email_address"):
        changes["email_address"] = validate_email(
            changes["email_address"], settings.smtp_allowed_recipient_domains
        )
    if changes.get("webhook_url"):
        changes["webhook_host"], _ = validate_webhook_url(changes["webhook_url"], settings)
    for key, value in changes.items():
        setattr(row, key, value)
    audit_event(
        session,
        event_type=OperationalAuditEventType.NOTIFICATION_DESTINATION_UPDATED,
        action="notification.destination.update",
        status="UPDATED",
        actor=actor,
        entity_type="notification_destination",
        entity_id=row.id,
        metadata={"fields": sorted(changes)},
    )
    session.commit()
    session.refresh(row)
    return _destination(row, True)


def _set_destination(destination_id: UUID, enabled: bool, request: Request, session: Session):
    row = session.get(NotificationDestination, destination_id)
    if not row:
        raise HTTPException(404, "Destino no encontrado.")
    actor = _actor(request)
    _owned(row, actor)
    row.status = "ACTIVE" if enabled else "PAUSED"
    event = (
        OperationalAuditEventType.NOTIFICATION_DESTINATION_RESUMED
        if enabled
        else OperationalAuditEventType.NOTIFICATION_DESTINATION_PAUSED
    )
    audit_event(
        session,
        event_type=event,
        action="notification.destination.status",
        status=row.status,
        actor=actor,
        entity_type="notification_destination",
        entity_id=row.id,
        metadata={},
    )
    session.commit()
    session.refresh(row)
    return _destination(row, True)


@router.post(
    "/notification-destinations/{destination_id}/pause",
    response_model=NotificationDestinationDetail,
)
def pause_destination(destination_id: UUID, request: Request, session: SessionDep):
    return _set_destination(destination_id, False, request, session)


@router.post(
    "/notification-destinations/{destination_id}/resume",
    response_model=NotificationDestinationDetail,
)
def resume_destination(destination_id: UUID, request: Request, session: SessionDep):
    return _set_destination(destination_id, True, request, session)


@router.post(
    "/notification-destinations/{destination_id}/test", response_model=NotificationTestResponse
)
def test_destination(
    destination_id: UUID,
    payload: NotificationTestRequest,
    request: Request,
    session: SessionDep,
    settings: SettingsDep,
):
    row = session.get(NotificationDestination, destination_id)
    if not row:
        raise HTTPException(404, "Destino no encontrado.")
    actor = _actor(request)
    _owned(row, actor)
    content = {
        "schema_version": "1.0.0",
        "event_type": "TEST_DELIVERY",
        "title": "Prueba de entrega PliegoCheck",
        "severity": "INFO",
        "summary": payload.message,
        "opportunity_link": "/settings/notifications",
        "disclaimer": DISCLAIMER,
    }
    delivery, _ = create_outbox(
        session,
        destination=row,
        payload=content,
        event_type="TEST_DELIVERY",
        period=str(uuid4()),
        settings=settings,
    )
    row.last_tested_at = datetime.now(UTC)
    row.last_test_status = "PENDING"
    audit_event(
        session,
        event_type=OperationalAuditEventType.NOTIFICATION_TEST_REQUESTED,
        action="notification.test",
        status="PENDING",
        actor=actor,
        entity_type="notification_destination",
        entity_id=row.id,
        metadata={"delivery_id": str(delivery.id)},
    )
    session.commit()
    return NotificationTestResponse(delivery_id=delivery.id, status=delivery.status)


@router.post(
    "/notification-subscriptions", response_model=NotificationSubscriptionDetail, status_code=201
)
def create_subscription(
    payload: NotificationSubscriptionCreateRequest, request: Request, session: SessionDep
):
    actor = _actor(request)
    destination = session.get(NotificationDestination, payload.destination_id)
    if not destination:
        raise HTTPException(404, "Destino no encontrado.")
    _owned(destination, actor)
    row = NotificationSubscription(
        id=uuid4(),
        owner_actor_id=actor.id if actor else None,
        destination_id=payload.destination_id,
        monitor_id=payload.monitor_id,
        enabled=True,
        delivery_mode=payload.delivery_mode.value,
        minimum_severity=payload.minimum_severity,
        alert_types=payload.alert_types,
        quiet_hours=payload.quiet_hours.model_dump() if payload.quiet_hours else None,
        timezone=payload.timezone,
        daily_digest_time=payload.daily_digest_time,
        weekly_digest_day=payload.weekly_digest_day,
        include_summary=payload.include_summary,
        include_opportunity_link=payload.include_opportunity_link,
        created_by=actor.id if actor else None,
    )
    session.add(row)
    session.flush()
    audit_event(
        session,
        event_type=OperationalAuditEventType.NOTIFICATION_SUBSCRIPTION_CREATED,
        action="notification.subscription.create",
        status="CREATED",
        actor=actor,
        entity_type="notification_subscription",
        entity_id=row.id,
        metadata={},
    )
    session.commit()
    session.refresh(row)
    return _subscription(row, True)


@router.get("/notification-subscriptions", response_model=NotificationSubscriptionList)
def list_subscriptions(request: Request, session: SessionDep):
    actor = _actor(request)
    query = select(NotificationSubscription).order_by(NotificationSubscription.created_at.desc())
    if actor and not _admin(actor):
        query = query.where(NotificationSubscription.owner_actor_id == actor.id)
    rows = list(session.scalars(query))
    return NotificationSubscriptionList(items=[_subscription(x) for x in rows], total=len(rows))


@router.get(
    "/notification-subscriptions/{subscription_id}", response_model=NotificationSubscriptionDetail
)
def subscription_detail(subscription_id: UUID, request: Request, session: SessionDep):
    row = session.get(NotificationSubscription, subscription_id)
    if not row:
        raise HTTPException(404, "Suscripción no encontrada.")
    _owned(row, _actor(request))
    return _subscription(row, True)


@router.patch(
    "/notification-subscriptions/{subscription_id}", response_model=NotificationSubscriptionDetail
)
def update_subscription(
    subscription_id: UUID,
    payload: NotificationSubscriptionUpdateRequest,
    request: Request,
    session: SessionDep,
):
    row = session.get(NotificationSubscription, subscription_id)
    if not row:
        raise HTTPException(404, "Suscripción no encontrada.")
    actor = _actor(request)
    _owned(row, actor)
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(
            row,
            key,
            value.value
            if hasattr(value, "value")
            else (value.model_dump() if hasattr(value, "model_dump") else value),
        )
    audit_event(
        session,
        event_type=OperationalAuditEventType.NOTIFICATION_SUBSCRIPTION_UPDATED,
        action="notification.subscription.update",
        status="UPDATED",
        actor=actor,
        entity_type="notification_subscription",
        entity_id=row.id,
        metadata={"fields": sorted(changes)},
    )
    session.commit()
    session.refresh(row)
    return _subscription(row, True)


def _set_subscription(subscription_id: UUID, enabled: bool, request: Request, session: Session):
    row = session.get(NotificationSubscription, subscription_id)
    if not row:
        raise HTTPException(404, "Suscripción no encontrada.")
    actor = _actor(request)
    _owned(row, actor)
    row.enabled = enabled
    event = (
        OperationalAuditEventType.NOTIFICATION_SUBSCRIPTION_RESUMED
        if enabled
        else OperationalAuditEventType.NOTIFICATION_SUBSCRIPTION_PAUSED
    )
    audit_event(
        session,
        event_type=event,
        action="notification.subscription.status",
        status="ACTIVE" if enabled else "PAUSED",
        actor=actor,
        entity_type="notification_subscription",
        entity_id=row.id,
        metadata={},
    )
    session.commit()
    session.refresh(row)
    return _subscription(row, True)


@router.post(
    "/notification-subscriptions/{subscription_id}/pause",
    response_model=NotificationSubscriptionDetail,
)
def pause_subscription(subscription_id: UUID, request: Request, session: SessionDep):
    return _set_subscription(subscription_id, False, request, session)


@router.post(
    "/notification-subscriptions/{subscription_id}/resume",
    response_model=NotificationSubscriptionDetail,
)
def resume_subscription(subscription_id: UUID, request: Request, session: SessionDep):
    return _set_subscription(subscription_id, True, request, session)


@router.get("/notification-deliveries", response_model=NotificationDeliveryList)
def deliveries(
    request: Request,
    session: SessionDep,
    status: NotificationOutboxStatus | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    actor = _actor(request)
    query = select(NotificationOutboxMessage)
    count_query = select(func.count()).select_from(NotificationOutboxMessage)
    if actor and not _admin(actor):
        owned = select(NotificationDestination.id).where(
            NotificationDestination.owner_actor_id == actor.id
        )
        query = query.where(NotificationOutboxMessage.destination_id.in_(owned))
        count_query = count_query.where(NotificationOutboxMessage.destination_id.in_(owned))
    if status:
        query = query.where(NotificationOutboxMessage.status == status.value)
        count_query = count_query.where(NotificationOutboxMessage.status == status.value)
    rows = session.scalars(
        query.order_by(NotificationOutboxMessage.created_at.desc()).offset(offset).limit(limit)
    ).all()
    total = session.scalar(count_query) or 0
    return NotificationDeliveryList(
        items=[_delivery(session, x) for x in rows], total=total, limit=limit, offset=offset
    )


@router.get("/notification-deliveries/{delivery_id}", response_model=NotificationDeliveryDetail)
def delivery_detail(delivery_id: UUID, request: Request, session: SessionDep):
    row = session.get(NotificationOutboxMessage, delivery_id)
    if not row:
        raise HTTPException(404, "Entrega no encontrada.")
    destination = session.get(NotificationDestination, row.destination_id)
    assert destination
    _owned(destination, _actor(request))
    return _delivery(session, row, True)


@router.post(
    "/notification-deliveries/{delivery_id}/retry", response_model=NotificationOperationResponse
)
def retry_delivery(delivery_id: UUID, request: Request, session: SessionDep):
    actor = _actor(request)
    if actor and AuthPermission.NOTIFICATION_OPERATE not in actor.permissions:
        raise HTTPException(403, "Permiso de operación requerido.")
    row = session.get(NotificationOutboxMessage, delivery_id)
    if not row:
        raise HTTPException(404, "Entrega no encontrada.")
    manual_retry(session, row, actor)
    return NotificationOperationResponse(delivery_id=row.id, status=row.status)


@router.post(
    "/notification-deliveries/{delivery_id}/cancel", response_model=NotificationOperationResponse
)
def cancel_delivery(delivery_id: UUID, request: Request, session: SessionDep):
    actor = _actor(request)
    if actor and AuthPermission.NOTIFICATION_OPERATE not in actor.permissions:
        raise HTTPException(403, "Permiso de operación requerido.")
    row = session.get(NotificationOutboxMessage, delivery_id)
    if not row:
        raise HTTPException(404, "Entrega no encontrada.")
    cancel(session, row, actor)
    return NotificationOperationResponse(delivery_id=row.id, status=row.status)


@router.get("/notification-digests", response_model=list[NotificationDigestSummary])
def digests(session: SessionDep):
    return [
        NotificationDigestSummary.model_validate(
            {
                key: getattr(row, key)
                for key in (
                    "id",
                    "destination_id",
                    "period",
                    "period_start",
                    "period_end",
                    "status",
                    "alert_count",
                    "outbox_message_id",
                )
            }
        )
        for row in session.scalars(
            select(NotificationDigestRun)
            .order_by(NotificationDigestRun.created_at.desc())
            .limit(100)
        )
    ]


@router.post("/notification-digests/run")
def digest_run(period: NotificationDigestPeriod, session: SessionDep, settings: SettingsDep):
    return {"created": run_digests(session, settings, period)}


@router.post("/notification-retention/run", response_model=NotificationRetentionResponse)
def retention_run(
    payload: NotificationRetentionRequest,
    request: Request,
    session: SessionDep,
    settings: SettingsDep,
):
    actor = _actor(request)
    if actor and AuthPermission.NOTIFICATION_ADMIN not in actor.permissions:
        raise HTTPException(403, "Permiso administrativo requerido.")
    payloads, attempts = run_retention(session, settings, payload.dry_run, payload.batch_size)
    return NotificationRetentionResponse(
        dry_run=payload.dry_run, payloads_cleared=payloads, attempts_deleted=attempts
    )
