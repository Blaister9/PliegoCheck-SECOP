# mypy: ignore-errors
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import pytest

from pliegocheck_api.auth import ROLE_PERMISSIONS
from pliegocheck_api.config import get_settings
from pliegocheck_api.db import get_sessionmaker
from pliegocheck_api.middleware import required_permission
from pliegocheck_api.models import NotificationDestination
from pliegocheck_api.notification_delivery.policy import (
    digest_period_bounds,
    parse_retry_after,
    quiet_hours_end,
    retry_delay_seconds,
    subscription_matches,
)
from pliegocheck_api.notification_delivery.providers import (
    prepare_webhook_request,
    render_email,
    validate_email,
    validate_webhook_url,
    webhook_signature,
)
from pliegocheck_api.notification_delivery.service import (
    DISCLAIMER,
    claim_next,
    create_outbox,
    process_next,
)
from pliegocheck_schemas import AuthPermission, AuthRoleName


def test_email_validation_and_header_injection():
    assert validate_email("pilot@example.test", ["example.test"]) == "pilot@example.test"
    with pytest.raises(ValueError):
        validate_email("a@example.test\nBcc:x@y.test", [])
    with pytest.raises(ValueError):
        validate_email("a@blocked.test", ["example.test"])


def test_rendered_email_has_text_html_escape_and_no_tracking():
    subject, text, html = render_email(
        {
            "title": "<Proceso>",
            "severity": "HIGH",
            "summary": "A & B",
            "opportunity_link": "/opportunities/1",
            "disclaimer": DISCLAIMER,
        },
        "d1",
    )
    assert "<Proceso>" in subject and DISCLAIMER in text
    assert "&lt;Proceso&gt;" in html and "tracking" not in html and "<script" not in html


def test_hmac_signature_is_stable_and_body_sensitive():
    first = webhook_signature("secret", "123", b"{}")
    assert first == webhook_signature("secret", "123", b"{}")
    assert first != webhook_signature("secret", "123", b'{"x":1}')


def test_webhook_dry_run_preparation_validates_and_signs_without_network():
    settings = get_settings().model_copy(update={"webhook_allowed_hosts": ["hooks.example.test"]})
    with patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("8.8.8.8", 443))]):
        body, headers = prepare_webhook_request(
            "https://hooks.example.test/events",
            "fixture-secret",
            {"event_type": "TEST_DELIVERY"},
            "delivery-1",
            "key-1",
            "123",
            settings,
        )
    assert headers["X-PliegoCheck-Signature"] == webhook_signature("fixture-secret", "123", body)
    assert headers["X-PliegoCheck-Idempotency-Key"] == "key-1"


def test_webhook_ssrf_and_allowlist():
    settings = get_settings().model_copy(update={"webhook_allowed_hosts": ["hooks.example.test"]})
    with patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("8.8.8.8", 443))]):
        assert (
            validate_webhook_url("https://hooks.example.test/x", settings)[0]
            == "hooks.example.test"
        )
    with pytest.raises(ValueError):
        validate_webhook_url("http://hooks.example.test/x", settings)
    with pytest.raises(ValueError):
        validate_webhook_url("https://localhost/x", settings)


def test_backoff_retry_after_and_quiet_hours_are_deterministic():
    assert retry_delay_seconds(2, 60, 3600, 30, "seed") == retry_delay_seconds(
        2, 60, 3600, 30, "seed"
    )
    assert 120 <= retry_delay_seconds(2, 60, 3600, 30, "seed") <= 150
    assert parse_retry_after("90", 3600) == 90 and parse_retry_after("invalid", 3600) is None
    sub = SimpleNamespace(
        quiet_hours={"start": "20:00", "end": "07:00", "critical_bypass": True},
        timezone="America/Bogota",
    )
    now = datetime(2026, 7, 15, 2, tzinfo=UTC)
    assert quiet_hours_end(sub, "HIGH", now) is not None
    assert quiet_hours_end(sub, "CRITICAL", now) is None


def test_digest_periods_are_stable_and_timezone_aware():
    first = datetime(2026, 7, 14, 14, 5, tzinfo=UTC)
    later = datetime(2026, 7, 14, 23, 59, tzinfo=UTC)
    assert digest_period_bounds("DAILY", "America/Bogota", first) == digest_period_bounds(
        "DAILY", "America/Bogota", later
    )
    start, end = digest_period_bounds("WEEKLY", "America/Bogota", first)
    assert end - start == timedelta(days=7)


def test_subscription_filtering():
    monitor = uuid4()
    sub = SimpleNamespace(
        enabled=True, monitor_id=monitor, alert_types=["X"], minimum_severity="HIGH"
    )
    assert subscription_matches(
        sub, SimpleNamespace(monitor_id=monitor, alert_type="X", severity="CRITICAL")
    )
    assert not subscription_matches(
        sub, SimpleNamespace(monitor_id=monitor, alert_type="Y", severity="CRITICAL")
    )


def test_destination_api_masks_and_test_uses_outbox(client):
    created = client.post(
        "/notification-destinations",
        json={
            "channel": "EMAIL_SMTP",
            "name": "Piloto",
            "email_address": "pilot@example.test",
            "configuration": {},
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["masked_destination"] == "p***@example.test" and "email_address" not in body
    test = client.post(f"/notification-destinations/{body['id']}/test", json={"message": "Prueba"})
    assert test.status_code == 200 and test.json()["status"] == "PENDING"
    listed = client.get("/notification-deliveries").json()
    assert listed["total"] == 1


def test_outbox_idempotency_and_dry_run():
    with get_sessionmaker()() as session:
        destination = NotificationDestination(
            id=uuid4(),
            channel="EMAIL_SMTP",
            name="Test",
            status="ACTIVE",
            email_address="pilot@example.test",
            configuration={},
        )
        session.add(destination)
        session.flush()
        settings = get_settings().model_copy(
            update={
                "external_delivery_enabled": True,
                "email_enabled": True,
                "notification_dry_run": True,
                "pilot_mode": False,
            }
        )
        payload = {
            "title": "Test",
            "severity": "INFO",
            "summary": "x",
            "opportunity_link": "/alerts",
            "disclaimer": DISCLAIMER,
        }
        first, reused = create_outbox(
            session,
            destination=destination,
            payload=payload,
            event_type="TEST_DELIVERY",
            period="fixed",
            settings=settings,
        )
        second, reused_second = create_outbox(
            session,
            destination=destination,
            payload=payload,
            event_type="TEST_DELIVERY",
            period="fixed",
            settings=settings,
        )
        session.commit()
        assert not reused and reused_second and first.id == second.id
        processed = process_next(session, settings, "test-worker")
        assert processed.status == "DRY_RUN" and processed.attempt_count == 1


def test_claim_skips_future_and_prevents_second_worker_claim():
    settings = get_settings()
    maker = get_sessionmaker()
    with maker() as session:
        destination = NotificationDestination(
            id=uuid4(),
            channel="EMAIL_SMTP",
            name="Claim",
            status="ACTIVE",
            email_address="pilot@example.test",
            configuration={},
        )
        session.add(destination)
        session.flush()
        future, _ = create_outbox(
            session,
            destination=destination,
            payload={"title": "Future"},
            event_type="TEST_DELIVERY",
            period="future",
            available_at=datetime(2099, 1, 1, tzinfo=UTC),
            settings=settings,
        )
        ready, _ = create_outbox(
            session,
            destination=destination,
            payload={"title": "Ready"},
            event_type="TEST_DELIVERY",
            period="ready",
            settings=settings,
        )
        session.commit()
    with maker() as worker_one:
        claimed = claim_next(worker_one)
        assert claimed and claimed.id == ready.id
    with maker() as worker_two:
        assert claim_next(worker_two) is None
        assert worker_two.get(type(future), future.id).status == "PENDING"


def test_notification_permissions_are_least_privilege_and_routes_are_mapped():
    assert AuthPermission.NOTIFICATION_ADMIN in ROLE_PERMISSIONS[AuthRoleName.ADMIN]
    assert AuthPermission.NOTIFICATION_OPERATE not in ROLE_PERMISSIONS[AuthRoleName.ANALYST]
    assert (
        ROLE_PERMISSIONS[AuthRoleName.VIEWER].intersection(
            {
                AuthPermission.NOTIFICATION_MANAGE_OWN,
                AuthPermission.NOTIFICATION_TEST,
                AuthPermission.NOTIFICATION_OPERATE,
                AuthPermission.NOTIFICATION_ADMIN,
            }
        )
        == set()
    )
    assert (
        required_permission("POST", "/notification-deliveries/id/retry")
        == AuthPermission.NOTIFICATION_OPERATE
    )
    assert (
        required_permission("GET", "/notification-delivery/readiness")
        == AuthPermission.NOTIFICATION_ADMIN
    )


def test_retention_dry_run_api_is_safe_on_postgresql_json(client):
    response = client.post("/notification-retention/run", json={"dry_run": True, "batch_size": 100})
    assert response.status_code == 200
    assert response.json() == {
        "dry_run": True,
        "payloads_cleared": 0,
        "attempts_deleted": 0,
    }
