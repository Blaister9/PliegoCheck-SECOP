"""Diagnostico del worker."""

from pliegocheck_api.config import get_settings
from pliegocheck_worker import SERVICE_NAME, SERVICE_VERSION
from pliegocheck_worker.normalization.orchestrator import normalization_queue_connected
from pliegocheck_worker.runner import queue_connected


def health_status() -> dict[str, str | bool]:
    """Estado del worker con comprobacion real de la cola PostgreSQL."""
    settings = get_settings()
    connected = queue_connected()
    normalization_connected = normalization_queue_connected()
    return {
        "status": "ok" if connected else "error",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "queue_connected": connected,
        "document_processing_enabled": connected,
        "requirement_normalization_enabled": (
            normalization_connected
            and (settings.ai_enabled or settings.allow_fake_normalization_provider)
        ),
        "normalization_provider": (
            "fake"
            if settings.allow_fake_normalization_provider and not settings.ai_enabled
            else "openai"
        ),
        "normalization_model": settings.openai_normalization_model,
    }
