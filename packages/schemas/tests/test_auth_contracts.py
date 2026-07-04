"""Contratos de autenticacion y operacion."""

from uuid import uuid4

from pydantic import ValidationError

from pliegocheck_schemas.auth import (
    AuthLoginRequest,
    AuthPermission,
    AuthRoleName,
    AuthUserCreateRequest,
    AuthUserStatus,
)


def test_auth_enums_cover_initial_roles_and_permissions() -> None:
    assert {role.value for role in AuthRoleName} == {"ADMIN", "ANALYST", "REVIEWER", "VIEWER"}
    assert AuthPermission.ADMIN_USERS.value == "admin:users"
    assert AuthPermission.REPORT_DOWNLOAD.value == "report:download"
    assert AuthUserStatus.ACTIVE.value == "ACTIVE"


def test_login_request_rejects_extra_fields() -> None:
    try:
        AuthLoginRequest(email="admin@example.com", password="x", token="bad")  # type: ignore[call-arg]
    except ValidationError as exc:
        assert "Extra inputs" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("extra field accepted")


def test_user_create_never_contains_password_hash() -> None:
    payload = AuthUserCreateRequest(
        email="admin@example.com",
        display_name="Admin",
        password="very-long-password",
        roles=[AuthRoleName.ADMIN],
    )
    dumped = payload.model_dump()
    assert dumped["password"] == "very-long-password"
    assert "password_hash" not in dumped
    assert str(uuid4()) not in dumped
