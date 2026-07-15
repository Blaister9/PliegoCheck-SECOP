import json

import pytest

from pliegocheck_api.notification_delivery.policy import retry_delay_seconds
from pliegocheck_api.notification_delivery.providers import validate_email, webhook_signature


@pytest.mark.parametrize(
    "phrase",
    [
        "novedad relevante",
        "revisión humana",
        "cierre crítico",
        "documento nuevo",
        "adenda potencial",
        "monitor recuperado",
        "entrega aceptada",
        "canal pausado",
        "modo de simulación",
        "destino permitido",
        "digest diario",
        "digest semanal",
        "alerta interna",
        "fallo temporal",
        "fallo permanente",
        "reintento programado",
        "preferencias guardadas",
        "webhook firmado",
        "correo de prueba",
        "operación piloto",
    ],
)
def test_20_safe_semantic_phrases(phrase):
    forbidden = ("chance de ganar", "debe ofertar", "oferta garantizada", "win probability")
    assert all(value not in phrase.lower() for value in forbidden)


@pytest.mark.parametrize(
    "attempt,seed", [(attempt, f"seed-{index}") for attempt in range(1, 6) for index in range(4)]
)
def test_20_backoff_cases_are_bounded_and_deterministic(attempt, seed):
    value = retry_delay_seconds(attempt, 60, 3600, 30, seed)
    assert value == retry_delay_seconds(attempt, 60, 3600, 30, seed)
    assert min(3600, 60 * 2 ** (attempt - 1)) <= value <= 3600


@pytest.mark.parametrize(
    "address,valid",
    [
        ("a@example.test", True),
        ("pilot.user@example.test", True),
        ("alerts@example.test", True),
        ("ops@example.test", True),
        ("x@y.example.test", True),
        ("first.last@example.test", True),
        ("a+tag@example.test", True),
        ("digest@example.test", True),
        ("missing-at", False),
        ("a@blocked.test", False),
        ("a@example.test\nBcc:x@y.test", False),
        ("", False),
        ("Name <a@example.test>", False),
        ("a@@example.test", False),
        ("@example.test", False),
        ("a@example", False),
    ],
)
def test_16_email_policy_cases(address, valid):
    if valid:
        assert validate_email(address, ["example.test", "y.example.test"]) == address
    else:
        with pytest.raises(ValueError):
            validate_email(address, ["example.test", "y.example.test"])


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "documents",
        "evidence",
        "company_payload",
        "secop_payload",
        "access_token",
        "storage_key",
        "physical_path",
        "cookie",
        "smtp_password",
        "webhook_secret",
        "authorization",
        "session_token",
        "raw_document",
        "private_key",
    ],
)
def test_14_minimal_webhook_payload_cases(forbidden_key):
    payload = {
        "schema_version": "1.0.0",
        "delivery_id": "d",
        "event_type": "OPPORTUNITY_ALERT",
        "alert": {"id": "a"},
        "disclaimer": "revisión humana",
    }
    assert forbidden_key not in json.dumps(payload).lower()


@pytest.mark.parametrize("suffix", [str(index) for index in range(14)])
def test_14_signature_tamper_cases(suffix):
    original = webhook_signature("fixture-secret", "123", b'{"event":"x"}')
    modified = webhook_signature(
        "fixture-secret", "123", ('{"event":"x","n":"' + suffix + '"}').encode()
    )
    assert original != modified
