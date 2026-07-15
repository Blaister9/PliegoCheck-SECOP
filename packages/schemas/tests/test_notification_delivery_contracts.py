# mypy: ignore-errors
import pytest
from pydantic import ValidationError

from pliegocheck_schemas import (
    NotificationChannel,
    NotificationDestinationCreateRequest,
    NotificationOutboxStatus,
    NotificationQuietHours,
)


def test_notification_enums_are_closed():
    assert set(NotificationChannel) == {"INTERNAL_ONLY", "EMAIL_SMTP", "SIGNED_WEBHOOK"}
    assert "FAILED_PERMANENT" in NotificationOutboxStatus


def test_destination_requires_channel_fields_and_secret_reference_name():
    with pytest.raises(ValidationError):
        NotificationDestinationCreateRequest(channel="SIGNED_WEBHOOK", name="Webhook")
    value = NotificationDestinationCreateRequest(
        channel="SIGNED_WEBHOOK",
        name="Webhook",
        webhook_url="https://hooks.example.test/path",
        secret_reference="PLIEGOCHECK_WEBHOOK_SECRET_TEST",
    )
    assert value.secret_reference == "PLIEGOCHECK_WEBHOOK_SECRET_TEST"


def test_quiet_hours_contract():
    assert NotificationQuietHours(start="20:00", end="07:00").critical_bypass is True
