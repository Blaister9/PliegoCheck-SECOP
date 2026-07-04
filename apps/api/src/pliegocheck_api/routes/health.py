"""Endpoints de salud del servicio."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from pliegocheck_api.config import settings
from pliegocheck_api.db import get_engine

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    """Respuesta tipada de los endpoints de salud."""

    status: Literal["ok"]
    service: str
    version: str


class ReadyResponse(HealthResponse):
    checks: dict[str, str]


@router.get(
    "/live", response_model=HealthResponse, summary="Liveness: confirma que el proceso esta vivo"
)
def live() -> HealthResponse:
    return HealthResponse(status="ok", service=settings.service_name, version=settings.version)


@router.get(
    "/ready",
    response_model=ReadyResponse,
    summary="Readiness: confirma que la API esta lista",
)
def ready() -> ReadyResponse:
    checks: dict[str, str] = {}
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"
    try:
        settings.storage_path.mkdir(parents=True, exist_ok=True)
        probe = settings.storage_path / ".ready-probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        checks["storage"] = "ok"
    except Exception:
        checks["storage"] = "error"
    checks["auth_config"] = (
        "ok"
        if not settings.auth_enabled
        or settings.auth_secret_key
        or settings.environment in {"development", "test"}
        else "error"
    )
    checks["cors"] = "ok" if settings.effective_cors_origins else "error"
    return ReadyResponse(
        status="ok",
        service=settings.service_name,
        version=settings.version,
        checks=checks,
    )
