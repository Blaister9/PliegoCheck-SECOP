"""Endpoints de autenticacion local."""

from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from pliegocheck_api.auth import (
    CurrentUser,
    audit_event,
    create_session,
    hash_password,
    record_login_event,
    revoke_session,
    role_names_for_user,
    user_summary,
    validate_password_strength,
    verify_password,
)
from pliegocheck_api.config import get_settings
from pliegocheck_api.db import get_session
from pliegocheck_api.errors import DomainError
from pliegocheck_api.models import AuthSession, AuthUser
from pliegocheck_schemas import (
    AuthChangePasswordRequest,
    AuthCurrentUser,
    AuthErrorCode,
    AuthLoginRequest,
    AuthLoginResponse,
    AuthUserStatus,
    OperationalAuditEventType,
)

router = APIRouter(prefix="/auth", tags=["auth"])
SessionDep = Annotated[Session, Depends(get_session)]


def current_user_from_state(request: Request) -> CurrentUser:
    user = getattr(request.state, "current_user", None)
    if user is None:
        raise DomainError(
            AuthErrorCode.AUTH_REQUIRED,
            "Autenticacion requerida.",
            status_code=HTTPStatus.UNAUTHORIZED,
        )
    return cast(CurrentUser, user)


CurrentUserDep = Annotated[CurrentUser, Depends(current_user_from_state)]


@router.post("/login", response_model=AuthLoginResponse)
def login(
    payload: AuthLoginRequest,
    request: Request,
    response: Response,
    session: SessionDep,
) -> AuthLoginResponse:
    email = payload.email.strip().lower()
    user = session.execute(select(AuthUser).where(AuthUser.email == email)).scalar_one_or_none()
    now = datetime.now(UTC)
    if (
        user is None
        or user.status != AuthUserStatus.ACTIVE.value
        or (user.locked_until is not None and user.locked_until > now)
        or not verify_password(payload.password, user.password_hash)
    ):
        if user is not None:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= get_settings().auth_max_failed_attempts:
                user.locked_until = now + timedelta(minutes=get_settings().auth_lockout_minutes)
                user.status = AuthUserStatus.LOCKED.value
        record_login_event(
            session,
            email=email,
            success=False,
            request=request,
            user_id=user.id if user else None,
            failure_reason="INVALID_CREDENTIALS",
        )
        audit_event(
            session,
            event_type=OperationalAuditEventType.AUTH_LOGIN_FAILED,
            action="auth.login",
            status="FAILED",
            request=request,
        )
        session.commit()
        raise DomainError(
            AuthErrorCode.AUTH_INVALID_CREDENTIALS,
            "Credenciales invalidas.",
            status_code=HTTPStatus.UNAUTHORIZED,
        )
    token, auth_session = create_session(session, user, request=request)
    _ = auth_session
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = now
    if user.status == AuthUserStatus.LOCKED.value:
        user.status = AuthUserStatus.ACTIVE.value
    roles = role_names_for_user(session, user.id)
    current = CurrentUser(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        status=AuthUserStatus(user.status),
        roles=tuple(roles),
        permissions=frozenset(),
    )
    record_login_event(session, email=email, success=True, request=request, user_id=user.id)
    audit_event(
        session,
        event_type=OperationalAuditEventType.AUTH_LOGIN_SUCCEEDED,
        action="auth.login",
        status="SUCCESS",
        actor=current,
        request=request,
    )
    summary = user_summary(session, user)
    session.commit()
    response.set_cookie(
        get_settings().auth_cookie_name,
        token,
        httponly=True,
        secure=get_settings().auth_cookie_secure,
        samesite=cast(Literal["lax", "strict", "none"], get_settings().auth_cookie_samesite),
        max_age=get_settings().auth_session_ttl_minutes * 60,
        path="/",
    )
    return AuthLoginResponse(user=summary, roles=summary.roles, permissions=summary.permissions)


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    session: SessionDep,
) -> dict[str, str]:
    token = request.cookies.get(get_settings().auth_cookie_name)
    actor = getattr(request.state, "current_user", None)
    revoke_session(session, token)
    audit_event(
        session,
        event_type=OperationalAuditEventType.AUTH_LOGOUT,
        action="auth.logout",
        status="SUCCESS",
        actor=actor,
        request=request,
    )
    session.commit()
    response.delete_cookie(get_settings().auth_cookie_name, path="/")
    return {"status": "ok"}


@router.get("/me", response_model=AuthCurrentUser)
def me(
    current_user: CurrentUserDep,
    session: SessionDep,
) -> AuthCurrentUser:
    user = session.get(AuthUser, current_user.id)
    if user is None:
        raise DomainError(
            AuthErrorCode.AUTH_USER_NOT_FOUND, "Usuario no encontrado.", status_code=404
        )
    summary = user_summary(session, user)
    return AuthCurrentUser(
        user=summary,
        roles=summary.roles,
        permissions=summary.permissions,
        auth_enabled=get_settings().auth_enabled,
    )


@router.post("/change-password")
def change_password(
    payload: AuthChangePasswordRequest,
    request: Request,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> dict[str, str]:
    user = session.get(AuthUser, current_user.id)
    if user is None or not verify_password(payload.current_password, user.password_hash):
        raise DomainError(
            AuthErrorCode.AUTH_INVALID_CURRENT_PASSWORD,
            "Password actual invalido.",
            status_code=HTTPStatus.BAD_REQUEST,
        )
    try:
        validate_password_strength(payload.new_password)
    except ValueError as exc:
        raise DomainError(
            AuthErrorCode.AUTH_PASSWORD_TOO_SHORT,
            "Password nuevo demasiado corto.",
            status_code=HTTPStatus.BAD_REQUEST,
        ) from exc
    user.password_hash = hash_password(payload.new_password)
    session.execute(
        update(AuthSession)
        .where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
    audit_event(
        session,
        event_type=OperationalAuditEventType.AUTH_PASSWORD_CHANGED,
        action="auth.password.change",
        status="SUCCESS",
        actor=current_user,
        request=request,
    )
    session.commit()
    return {"status": "ok"}
