"""Autenticacion local, permisos y auditoria operacional."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from fastapi import Request
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from pliegocheck_api.config import Settings, get_settings
from pliegocheck_api.models import (
    AuthLoginEvent,
    AuthRole,
    AuthSession,
    AuthUser,
    AuthUserRole,
    OperationalAuditEvent,
)
from pliegocheck_schemas import (
    AuthPermission,
    AuthRoleName,
    AuthUserStatus,
    AuthUserSummary,
    OperationalAuditEventType,
)

PBKDF2_ALGORITHM = "pbkdf2_sha256"
PBKDF2_ITERATIONS = 390_000
ROLE_DESCRIPTIONS = {
    AuthRoleName.ADMIN: "Gestion operativa, usuarios, auditoria y configuracion.",
    AuthRoleName.ANALYST: "Crea procesos, empresas, evaluaciones, decisiones y reportes.",
    AuthRoleName.REVIEWER: "Revisa decisiones, overrides y descarga reportes.",
    AuthRoleName.VIEWER: "Lectura y descarga limitada.",
}
ROLE_PERMISSIONS: dict[AuthRoleName, set[AuthPermission]] = {
    AuthRoleName.ADMIN: set(AuthPermission),
    AuthRoleName.ANALYST: {
        AuthPermission.PROCESS_READ,
        AuthPermission.PROCESS_WRITE,
        AuthPermission.DOCUMENT_WRITE,
        AuthPermission.NORMALIZATION_RUN,
        AuthPermission.COMPANY_READ,
        AuthPermission.COMPANY_WRITE,
        AuthPermission.EVALUATION_RUN,
        AuthPermission.DECISION_RUN,
        AuthPermission.REPORT_GENERATE,
        AuthPermission.REPORT_DOWNLOAD,
        AuthPermission.EXTERNAL_SEARCH,
        AuthPermission.EXTERNAL_IMPORT,
    },
    AuthRoleName.REVIEWER: {
        AuthPermission.PROCESS_READ,
        AuthPermission.COMPANY_READ,
        AuthPermission.DECISION_REVIEW,
        AuthPermission.REPORT_DOWNLOAD,
    },
    AuthRoleName.VIEWER: {
        AuthPermission.PROCESS_READ,
        AuthPermission.COMPANY_READ,
        AuthPermission.REPORT_DOWNLOAD,
    },
}


@dataclass(frozen=True)
class CurrentUser:
    id: UUID
    email: str
    display_name: str
    status: AuthUserStatus
    roles: tuple[AuthRoleName, ...]
    permissions: frozenset[AuthPermission]
    session_id: UUID | None = None


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def hash_optional(value: str | None) -> str | None:
    if not value:
        return None
    return hash_secret(value[:500])


def request_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    return request.client.host if request.client else None


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return (
        f"{PBKDF2_ALGORITHM}${PBKDF2_ITERATIONS}$"
        f"{base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt_text, digest_text = stored_hash.split("$", 3)
        if algorithm != PBKDF2_ALGORITHM:
            return False
        iterations = int(iterations_text)
        salt = base64.b64decode(salt_text.encode())
        expected = base64.b64decode(digest_text.encode())
    except (ValueError, TypeError):
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


def validate_password_strength(password: str, settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    if len(password) < settings.auth_password_min_length:
        raise ValueError("password too short")


def ensure_roles(session: Session) -> None:
    existing = {row[0] for row in session.execute(select(AuthRole.name)).all()}
    for role in AuthRoleName:
        if role.value not in existing:
            session.add(
                AuthRole(
                    id=uuid4(),
                    name=role.value,
                    description=ROLE_DESCRIPTIONS[role],
                )
            )
    session.flush()


def role_names_for_user(session: Session, user_id: UUID) -> list[AuthRoleName]:
    rows = session.execute(
        select(AuthRole.name)
        .join(AuthUserRole, AuthUserRole.role_id == AuthRole.id)
        .where(AuthUserRole.user_id == user_id)
        .order_by(AuthRole.name)
    ).scalars()
    return [AuthRoleName(row) for row in rows]


def permissions_for_roles(
    roles: list[AuthRoleName] | tuple[AuthRoleName, ...],
) -> set[AuthPermission]:
    permissions: set[AuthPermission] = set()
    for role in roles:
        permissions.update(ROLE_PERMISSIONS[role])
    return permissions


def user_summary(session: Session, user: AuthUser) -> AuthUserSummary:
    roles = role_names_for_user(session, user.id)
    permissions = sorted(permissions_for_roles(roles), key=lambda item: item.value)
    return AuthUserSummary(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        status=AuthUserStatus(user.status),
        roles=roles,
        permissions=permissions,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def create_user(
    session: Session,
    *,
    email: str,
    display_name: str,
    password: str,
    roles: list[AuthRoleName],
    settings: Settings | None = None,
) -> AuthUser:
    settings = settings or get_settings()
    validate_password_strength(password, settings)
    ensure_roles(session)
    normalized = normalize_email(email)
    existing = session.execute(
        select(AuthUser).where(AuthUser.email == normalized)
    ).scalar_one_or_none()
    if existing is not None:
        raise ValueError("email already exists")
    user = AuthUser(
        id=uuid4(),
        email=normalized,
        display_name=display_name.strip(),
        password_hash=hash_password(password),
        status=AuthUserStatus.ACTIVE.value,
        failed_login_attempts=0,
    )
    session.add(user)
    session.flush()
    set_user_roles(session, user.id, roles)
    audit_event(
        session,
        event_type=OperationalAuditEventType.AUTH_USER_CREATED,
        action="auth.user.create",
        status="SUCCESS",
        entity_type="auth_user",
        entity_id=user.id,
        metadata={"roles": [role.value for role in roles]},
    )
    return user


def set_user_roles(session: Session, user_id: UUID, roles: list[AuthRoleName]) -> None:
    ensure_roles(session)
    session.execute(delete(AuthUserRole).where(AuthUserRole.user_id == user_id))
    role_rows = session.execute(
        select(AuthRole).where(AuthRole.name.in_([role.value for role in roles]))
    ).scalars()
    for role in role_rows:
        session.add(AuthUserRole(id=uuid4(), user_id=user_id, role_id=role.id))
    session.flush()


def create_session(
    session: Session,
    user: AuthUser,
    *,
    request: Request | None = None,
    settings: Settings | None = None,
) -> tuple[str, AuthSession]:
    settings = settings or get_settings()
    token = secrets.token_urlsafe(48)
    now = datetime.now(UTC)
    record = AuthSession(
        id=uuid4(),
        user_id=user.id,
        session_token_hash=hash_secret(token),
        expires_at=now + timedelta(minutes=settings.auth_session_ttl_minutes),
        last_seen_at=now,
        ip_hash=hash_optional(request_ip(request)) if request else None,
        user_agent_hash=hash_optional(request.headers.get("user-agent")) if request else None,
    )
    session.add(record)
    session.flush()
    return token, record


def authenticate_session(session: Session, token: str) -> CurrentUser | None:
    now = datetime.now(UTC)
    record = session.execute(
        select(AuthSession).where(AuthSession.session_token_hash == hash_secret(token))
    ).scalar_one_or_none()
    if record is None or record.revoked_at is not None or record.expires_at <= now:
        return None
    user = session.get(AuthUser, record.user_id)
    if user is None or user.status != AuthUserStatus.ACTIVE.value:
        return None
    record.last_seen_at = now
    roles = tuple(role_names_for_user(session, user.id))
    return CurrentUser(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        status=AuthUserStatus(user.status),
        roles=roles,
        permissions=frozenset(permissions_for_roles(roles)),
        session_id=record.id,
    )


def revoke_session(session: Session, token: str | None) -> None:
    if not token:
        return
    record = session.execute(
        select(AuthSession).where(AuthSession.session_token_hash == hash_secret(token))
    ).scalar_one_or_none()
    if record is not None and record.revoked_at is None:
        record.revoked_at = datetime.now(UTC)


def record_login_event(
    session: Session,
    *,
    email: str,
    success: bool,
    request: Request,
    user_id: UUID | None = None,
    failure_reason: str | None = None,
) -> None:
    session.add(
        AuthLoginEvent(
            id=uuid4(),
            user_id=user_id,
            email_hash=hash_secret(normalize_email(email)),
            success=success,
            failure_reason=failure_reason,
            ip_hash=hash_optional(request_ip(request)),
            user_agent_hash=hash_optional(request.headers.get("user-agent")),
        )
    )


def audit_event(
    session: Session,
    *,
    event_type: OperationalAuditEventType,
    action: str,
    status: str,
    actor: CurrentUser | None = None,
    request: Request | None = None,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    clean_metadata = {
        key: str(value)[:300]
        for key, value in (metadata or {}).items()
        if key.lower() not in {"password", "token", "cookie", "secret", "password_hash"}
    }
    session.add(
        OperationalAuditEvent(
            id=uuid4(),
            actor_user_id=actor.id if actor else None,
            actor_email_hash=hash_secret(actor.email) if actor else None,
            event_type=event_type.value,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            status=status,
            ip_hash=hash_optional(request_ip(request)) if request else None,
            user_agent_hash=hash_optional(request.headers.get("user-agent")) if request else None,
            event_metadata=clean_metadata,
        )
    )


def count_users(session: Session) -> int:
    return int(session.execute(select(func.count()).select_from(AuthUser)).scalar_one())
