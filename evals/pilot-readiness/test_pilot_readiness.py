"""Eval sintetico de preparacion de piloto sin llamadas externas."""

from http import HTTPStatus
from uuid import uuid4

from fastapi.testclient import TestClient

from pliegocheck_api.auth import create_user
from pliegocheck_api.config import get_settings
from pliegocheck_api.db import get_sessionmaker
from pliegocheck_schemas import AuthRoleName


def test_pilot_auth_admin_audit_logout_flow(monkeypatch) -> None:
    monkeypatch.setenv("PLIEGOCHECK_AUTH_ENABLED", "true")
    monkeypatch.setenv("PLIEGOCHECK_ENVIRONMENT", "test")
    monkeypatch.setenv("PLIEGOCHECK_AUTH_SECRET_KEY", "pilot-eval-secret-not-real")
    get_settings.cache_clear()

    from pliegocheck_api.main import app

    session_factory = get_sessionmaker()
    email = f"pilot-admin-{uuid4().hex[:8]}@example.com"
    with session_factory() as session:
        create_user(
            session,
            email=email,
            display_name="Pilot Admin",
            password="very-long-password",
            roles=[AuthRoleName.ADMIN],
        )
        session.commit()

    client = TestClient(app)
    assert client.get("/processes").status_code == HTTPStatus.UNAUTHORIZED
    assert (
        client.post(
            "/auth/login",
            json={"email": email, "password": "very-long-password"},
        ).status_code
        == HTTPStatus.OK
    )
    assert client.get("/admin/system-config").status_code == HTTPStatus.OK
    assert client.get("/admin/audit-events").status_code == HTTPStatus.OK
    assert client.post("/auth/logout").status_code == HTTPStatus.OK
    assert client.get("/processes").status_code == HTTPStatus.UNAUTHORIZED
