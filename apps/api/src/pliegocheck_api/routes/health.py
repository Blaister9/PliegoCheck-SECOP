"""Endpoints de salud del servicio."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from pliegocheck_api.config import settings

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    """Respuesta tipada de los endpoints de salud."""

    status: Literal["ok"]
    service: str
    version: str


@router.get("/live", summary="Liveness: confirma que el proceso esta vivo")
def live() -> HealthResponse:
    return HealthResponse(status="ok", service=settings.service_name, version=settings.version)


@router.get("/ready", summary="Readiness: confirma que la API esta lista")
def ready() -> HealthResponse:
    # Sin base de datos ni servicios externos todavia (Microfase 1):
    # la disponibilidad del proceso equivale a estar listo.
    return HealthResponse(status="ok", service=settings.service_name, version=settings.version)
