"""Endpoints administrativos protegidos."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from pliegocheck_api.auth import (
    CurrentUser,
    audit_event,
    create_user,
    set_user_roles,
    user_summary,
)
from pliegocheck_api.config import get_settings
from pliegocheck_api.db import get_session
from pliegocheck_api.errors import DomainError
from pliegocheck_api.models import AuthUser, OperationalAuditEvent
from pliegocheck_api.routes.auth import current_user_from_state
from pliegocheck_schemas import (
    AuthErrorCode,
    AuthRoleName,
    AuthUserCreateRequest,
    AuthUserList,
    AuthUserRoleUpdateRequest,
    AuthUserStatus,
    OperationalAuditEventList,
    OperationalAuditEventType,
    SystemConfigSummary,
)
from pliegocheck_schemas import (
    OperationalAuditEvent as OperationalAuditEventSchema,
)

router = APIRouter(prefix="/admin", tags=["admin"])
SessionDep = Annotated[Session, Depends(get_session)]
CurrentUserDep = Annotated[CurrentUser, Depends(current_user_from_state)]


@router.get("/users", response_model=AuthUserList)
def list_users(
    session: SessionDep,
    _current_user: CurrentUserDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> AuthUserList:
    return _list_users(session, limit=limit, offset=offset)


def _list_users(session: Session, *, limit: int = 50, offset: int = 0) -> AuthUserList:
    total = session.execute(select(func.count()).select_from(AuthUser)).scalar_one()
    users = session.execute(
        select(AuthUser).order_by(AuthUser.created_at.desc()).limit(limit).offset(offset)
    ).scalars()
    return AuthUserList(
        items=[user_summary(session, user) for user in users],
        total=int(total),
        limit=limit,
        offset=offset,
    )


@router.post("/users", response_model=AuthUserList)
def create_user_endpoint(
    payload: AuthUserCreateRequest,
    request: Request,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> AuthUserList:
    try:
        user = create_user(
            session,
            email=payload.email,
            display_name=payload.display_name,
            password=payload.password,
            roles=payload.roles,
        )
    except ValueError as exc:
        code = (
            AuthErrorCode.AUTH_EMAIL_ALREADY_EXISTS
            if "exists" in str(exc)
            else AuthErrorCode.AUTH_PASSWORD_TOO_SHORT
        )
        raise DomainError(code, "No fue posible crear el usuario.", status_code=400) from exc
    audit_event(
        session,
        event_type=OperationalAuditEventType.AUTH_USER_CREATED,
        action="admin.user.create",
        status="SUCCESS",
        actor=current_user,
        request=request,
        entity_type="auth_user",
        entity_id=user.id,
        metadata={"roles": ",".join(role.value for role in payload.roles)},
    )
    session.commit()
    return _list_users(session)


@router.post("/users/{user_id}/disable", response_model=AuthUserList)
def disable_user(
    user_id: UUID,
    request: Request,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> AuthUserList:
    user = session.get(AuthUser, user_id)
    if user is None:
        raise DomainError(
            AuthErrorCode.AUTH_USER_NOT_FOUND, "Usuario no encontrado.", status_code=404
        )
    user.status = AuthUserStatus.DISABLED.value
    audit_event(
        session,
        event_type=OperationalAuditEventType.AUTH_USER_DISABLED,
        action="admin.user.disable",
        status="SUCCESS",
        actor=current_user,
        request=request,
        entity_type="auth_user",
        entity_id=user_id,
    )
    session.commit()
    return _list_users(session)


@router.post("/users/{user_id}/enable", response_model=AuthUserList)
def enable_user(
    user_id: UUID,
    request: Request,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> AuthUserList:
    user = session.get(AuthUser, user_id)
    if user is None:
        raise DomainError(
            AuthErrorCode.AUTH_USER_NOT_FOUND, "Usuario no encontrado.", status_code=404
        )
    user.status = AuthUserStatus.ACTIVE.value
    user.failed_login_attempts = 0
    user.locked_until = None
    audit_event(
        session,
        event_type=OperationalAuditEventType.AUTH_USER_ENABLED,
        action="admin.user.enable",
        status="SUCCESS",
        actor=current_user,
        request=request,
        entity_type="auth_user",
        entity_id=user_id,
    )
    session.commit()
    return _list_users(session)


@router.post("/users/{user_id}/roles", response_model=AuthUserList)
def update_roles(
    user_id: UUID,
    payload: AuthUserRoleUpdateRequest,
    request: Request,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> AuthUserList:
    user = session.get(AuthUser, user_id)
    if user is None:
        raise DomainError(
            AuthErrorCode.AUTH_USER_NOT_FOUND, "Usuario no encontrado.", status_code=404
        )
    set_user_roles(session, user_id, payload.roles or [AuthRoleName.VIEWER])
    audit_event(
        session,
        event_type=OperationalAuditEventType.AUTH_ROLES_UPDATED,
        action="admin.user.roles",
        status="SUCCESS",
        actor=current_user,
        request=request,
        entity_type="auth_user",
        entity_id=user_id,
        metadata={"roles": ",".join(role.value for role in payload.roles)},
    )
    session.commit()
    return _list_users(session)


@router.get("/audit-events", response_model=OperationalAuditEventList)
def audit_events(
    session: SessionDep,
    _current_user: CurrentUserDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> OperationalAuditEventList:
    total = session.execute(select(func.count()).select_from(OperationalAuditEvent)).scalar_one()
    rows = session.execute(
        select(OperationalAuditEvent)
        .order_by(OperationalAuditEvent.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).scalars()
    return OperationalAuditEventList(
        items=[
            OperationalAuditEventSchema(
                id=row.id,
                actor_user_id=row.actor_user_id,
                actor_email_hash=row.actor_email_hash,
                event_type=OperationalAuditEventType(row.event_type),
                entity_type=row.entity_type,
                entity_id=row.entity_id,
                action=row.action,
                status=row.status,
                ip_hash=row.ip_hash,
                user_agent_hash=row.user_agent_hash,
                metadata=row.event_metadata,
                created_at=row.created_at,
            )
            for row in rows
        ],
        total=int(total),
        limit=limit,
        offset=offset,
    )


@router.get("/system-config", response_model=SystemConfigSummary)
def system_config(
    _current_user: CurrentUserDep,
) -> SystemConfigSummary:
    settings = get_settings()
    return SystemConfigSummary(
        auth_enabled=settings.auth_enabled,
        pilot_mode=settings.pilot_mode,
        environment=settings.environment,
        storage_mode="local",
        ai_enabled=settings.ai_enabled,
        allowed_origins_count=len(settings.effective_cors_origins),
        upload_max_file_size_mb=settings.max_file_size_mb,
        security_headers_enabled=settings.security_headers_enabled,
        worker_capabilities=[
            "document_processing",
            "normalization",
            "financial",
            "specialized",
            "decision",
            "report",
        ],
        version=settings.version,
        commit=None,
        redacted={
            "database_url": "REDACTED",
            "auth_secret_key": "SET" if settings.auth_secret_key else "EMPTY",
            "openai_api_key": "SET" if settings.openai_api_key else "EMPTY",
        },
    )
