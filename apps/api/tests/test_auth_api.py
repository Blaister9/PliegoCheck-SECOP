"""Pruebas de autenticacion local y permisos."""

from collections.abc import Generator
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from pliegocheck_api.auth import create_user
from pliegocheck_api.config import get_settings
from pliegocheck_api.db import get_sessionmaker
from pliegocheck_api.models import OperationalAuditEvent
from pliegocheck_schemas import AuthRoleName


@pytest.fixture(autouse=True)
def clear_settings_after() -> Generator[None, None, None]:
    yield
    get_settings.cache_clear()


def _enable_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLIEGOCHECK_AUTH_ENABLED", "true")
    monkeypatch.setenv("PLIEGOCHECK_ENVIRONMENT", "test")
    monkeypatch.setenv("PLIEGOCHECK_AUTH_SECRET_KEY", "test-secret-not-real")
    get_settings.cache_clear()


def _create_user(email: str, password: str, roles: list[AuthRoleName]) -> None:
    session_factory = get_sessionmaker()
    with session_factory() as session:
        create_user(
            session,
            email=email,
            display_name=email.split("@", 1)[0],
            password=password,
            roles=roles,
        )
        session.commit()


def test_login_me_logout_and_cookie(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    _enable_auth(monkeypatch)
    _create_user("admin@example.com", "very-long-password", [AuthRoleName.ADMIN])

    response = client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "very-long-password"},
    )
    assert response.status_code == HTTPStatus.OK
    assert "httponly" in response.headers["set-cookie"].lower()
    assert response.json()["roles"] == ["ADMIN"]

    me = client.get("/auth/me")
    assert me.status_code == HTTPStatus.OK
    assert me.json()["user"]["email"] == "admin@example.com"

    logout = client.post("/auth/logout")
    assert logout.status_code == HTTPStatus.OK
    assert client.get("/auth/me").status_code == HTTPStatus.UNAUTHORIZED


def test_protected_endpoint_requires_session(
    monkeypatch: pytest.MonkeyPatch, client: TestClient
) -> None:
    _enable_auth(monkeypatch)
    response = client.get("/processes")
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()["code"] == "AUTH_REQUIRED"


def test_permission_denied_is_audited(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    _enable_auth(monkeypatch)
    _create_user("viewer@example.com", "very-long-password", [AuthRoleName.VIEWER])
    assert (
        client.post(
            "/auth/login",
            json={"email": "viewer@example.com", "password": "very-long-password"},
        ).status_code
        == HTTPStatus.OK
    )
    response = client.get("/admin/users")
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()["code"] == "AUTH_PERMISSION_DENIED"

    session_factory = get_sessionmaker()
    with session_factory() as session:
        event = session.execute(
            select(OperationalAuditEvent).where(
                OperationalAuditEvent.event_type == "PERMISSION_DENIED"
            )
        ).scalar_one()
        assert event.event_metadata["permission"] == "admin:users"


def test_admin_can_list_users_and_system_config(
    monkeypatch: pytest.MonkeyPatch, client: TestClient
) -> None:
    _enable_auth(monkeypatch)
    _create_user("admin@example.com", "very-long-password", [AuthRoleName.ADMIN])
    assert (
        client.post(
            "/auth/login",
            json={"email": "admin@example.com", "password": "very-long-password"},
        ).status_code
        == HTTPStatus.OK
    )
    users = client.get("/admin/users")
    assert users.status_code == HTTPStatus.OK
    assert users.json()["items"][0]["email"] == "admin@example.com"
    config = client.get("/admin/system-config")
    assert config.status_code == HTTPStatus.OK
    assert config.json()["redacted"]["auth_secret_key"] == "SET"


def test_change_password_revokes_sessions(
    monkeypatch: pytest.MonkeyPatch, client: TestClient
) -> None:
    _enable_auth(monkeypatch)
    _create_user("analyst@example.com", "very-long-password", [AuthRoleName.ANALYST])
    assert (
        client.post(
            "/auth/login",
            json={"email": "analyst@example.com", "password": "very-long-password"},
        ).status_code
        == HTTPStatus.OK
    )

    response = client.post(
        "/auth/change-password",
        json={
            "current_password": "very-long-password",
            "new_password": "another-long-password",
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert client.get("/auth/me").status_code == HTTPStatus.UNAUTHORIZED
    assert (
        client.post(
            "/auth/login",
            json={"email": "analyst@example.com", "password": "very-long-password"},
        ).status_code
        == HTTPStatus.UNAUTHORIZED
    )
    assert (
        client.post(
            "/auth/login",
            json={"email": "analyst@example.com", "password": "another-long-password"},
        ).status_code
        == HTTPStatus.OK
    )
