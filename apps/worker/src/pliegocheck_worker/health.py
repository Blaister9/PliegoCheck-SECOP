"""Diagnostico del worker."""

from pliegocheck_worker import SERVICE_NAME, SERVICE_VERSION
from pliegocheck_worker.runner import queue_connected


def health_status() -> dict[str, str | bool]:
    """Estado del worker con comprobacion real de la cola PostgreSQL."""
    connected = queue_connected()
    return {
        "status": "ok" if connected else "error",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "queue_connected": connected,
        "document_processing_enabled": connected,
    }
