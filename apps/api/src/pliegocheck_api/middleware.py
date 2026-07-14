"""Middleware de seguridad operacional."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from http import HTTPStatus
from uuid import uuid4

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from pliegocheck_api.auth import audit_event, authenticate_session
from pliegocheck_api.config import get_settings
from pliegocheck_api.db import get_sessionmaker
from pliegocheck_schemas import ApiError, AuthErrorCode, AuthPermission, OperationalAuditEventType

PUBLIC_PATHS = {
    ("GET", "/health/live"),
    ("GET", "/health/ready"),
    ("POST", "/auth/login"),
}
logger = logging.getLogger(__name__)


def required_permission(method: str, path: str) -> AuthPermission | None:
    if path.startswith("/opportunities/discovery-runs") and method == "POST":
        return AuthPermission.OPPORTUNITY_DISCOVER
    if path.startswith("/opportunities/") and path.endswith("/assess") and method == "POST":
        return AuthPermission.OPPORTUNITY_ASSESS
    if path.startswith("/opportunities/") and path.endswith("/review") and method == "POST":
        return AuthPermission.OPPORTUNITY_REVIEW
    if path.startswith("/opportunities/") and path.endswith("/import") and method == "POST":
        return AuthPermission.OPPORTUNITY_IMPORT
    if path.startswith("/opportunities/") and path.endswith("/request-deep-analysis"):
        return AuthPermission.OPPORTUNITY_READ
    if path.startswith("/opportunities"):
        return AuthPermission.OPPORTUNITY_READ
    if path.startswith("/processes") and path.endswith("/external-sync") and method == "POST":
        return AuthPermission.EXTERNAL_SYNC
    if "/external-documents/" in path and path.endswith("/download") and method == "POST":
        return AuthPermission.EXTERNAL_DOWNLOAD
    if "/external-documents/" in path and path.endswith("/extract") and method == "POST":
        return AuthPermission.DOCUMENT_WRITE
    if "/external-sync" in path or "/external-documents" in path:
        return AuthPermission.EXTERNAL_READ
    if path.startswith("/external-procurement/results") and method == "POST":
        return AuthPermission.EXTERNAL_IMPORT
    if path.startswith("/external-procurement/searches") and method == "POST":
        return AuthPermission.EXTERNAL_SEARCH
    if path.startswith("/external-procurement"):
        return AuthPermission.PROCESS_READ
    if path.startswith("/admin/audit-events"):
        return AuthPermission.AUDIT_READ
    if path.startswith("/admin/system-config"):
        return AuthPermission.ADMIN_SETTINGS
    if path.startswith("/admin/users"):
        return AuthPermission.ADMIN_USERS
    if path.endswith("/review") or "/review/" in path:
        return AuthPermission.DECISION_REVIEW
    if "/decision-reports" in path and method == "POST":
        return AuthPermission.REPORT_GENERATE
    if "/decision-reports" in path and (path.endswith("/download") or "/artifacts/" in path):
        return AuthPermission.REPORT_DOWNLOAD
    if "/decisions" in path and method == "POST":
        return AuthPermission.DECISION_RUN
    if "evaluations" in path and method == "POST":
        return AuthPermission.EVALUATION_RUN
    if "/requirements/normalizations" in path and method == "POST":
        return AuthPermission.NORMALIZATION_RUN
    if "/documents" in path and method in {"POST", "PATCH"}:
        return AuthPermission.DOCUMENT_WRITE
    if path.startswith("/companies") and method in {"POST", "PATCH"}:
        return AuthPermission.COMPANY_WRITE
    if path.startswith("/processes") and method in {"POST", "PATCH"}:
        return AuthPermission.PROCESS_WRITE
    if path.startswith("/companies"):
        return AuthPermission.COMPANY_READ
    if path.startswith("/processes") or path.startswith("/contracts"):
        return AuthPermission.PROCESS_READ
    return None


async def security_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    settings = get_settings()
    request_id = request.headers.get("x-request-id") or uuid4().hex
    request.state.request_id = request_id
    if settings.auth_enabled and not _is_public(request.method, request.url.path):
        auth_response = _authorize_request(request)
        if auth_response is not None:
            auth_response.headers["X-Request-ID"] = request_id
            _add_security_headers(auth_response)
            return auth_response
    try:
        response = await call_next(request)
    except SQLAlchemyError:
        logger.exception(
            "database_request_error",
            extra={"request_id": request_id, "path": request.url.path},
        )
        response = _error_response(
            AuthErrorCode.AUTH_CONFIG_INVALID,
            "La solicitud no pudo completarse.",
            HTTPStatus.INTERNAL_SERVER_ERROR,
            request_id,
        )
    except Exception:
        logger.exception(
            "unhandled_request_error",
            extra={"request_id": request_id, "path": request.url.path},
        )
        response = _error_response(
            AuthErrorCode.AUTH_CONFIG_INVALID,
            "La solicitud no pudo completarse.",
            HTTPStatus.INTERNAL_SERVER_ERROR,
            request_id,
        )
    response.headers["X-Request-ID"] = request_id
    _add_security_headers(response)
    return response


def _is_public(method: str, path: str) -> bool:
    if method == "OPTIONS":
        return True
    return (method, path.rstrip("/") or "/") in PUBLIC_PATHS


def _authorize_request(request: Request) -> JSONResponse | None:
    settings = get_settings()
    token = request.cookies.get(settings.auth_cookie_name)
    if not token:
        return _error_response(
            AuthErrorCode.AUTH_REQUIRED,
            "Autenticacion requerida.",
            HTTPStatus.UNAUTHORIZED,
            request.state.request_id,
        )
    session_factory = get_sessionmaker()
    with session_factory() as session:
        current_user = authenticate_session(session, token)
        if current_user is None:
            session.commit()
            return _error_response(
                AuthErrorCode.AUTH_SESSION_EXPIRED,
                "Sesion invalida o expirada.",
                HTTPStatus.UNAUTHORIZED,
                request.state.request_id,
            )
        request.state.current_user = current_user
        permission = required_permission(request.method, request.url.path)
        if permission and permission not in current_user.permissions:
            audit_event(
                session,
                event_type=OperationalAuditEventType.PERMISSION_DENIED,
                action="permission.denied",
                status="DENIED",
                actor=current_user,
                request=request,
                metadata={"permission": permission.value, "path": request.url.path},
            )
            session.commit()
            return _error_response(
                AuthErrorCode.AUTH_PERMISSION_DENIED,
                "Permiso insuficiente.",
                HTTPStatus.FORBIDDEN,
                request.state.request_id,
            )
        session.commit()
    return None


def _error_response(
    code: AuthErrorCode,
    message: str,
    status_code: HTTPStatus,
    request_id: str,
    details: dict[str, str] | None = None,
) -> JSONResponse:
    payload = ApiError(
        code=code,
        message=message,
        details={"request_id": request_id, **(details or {})},
    )
    return JSONResponse(status_code=int(status_code), content=payload.model_dump(mode="json"))


def _add_security_headers(response: Response) -> None:
    settings = get_settings()
    if not settings.security_headers_enabled:
        return
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'self'",
    )
