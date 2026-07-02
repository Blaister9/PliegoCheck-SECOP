"""Diagnostico del worker."""

from pliegocheck_worker import SERVICE_NAME, SERVICE_VERSION


def health_status() -> dict[str, str | bool]:
    """Estado del worker. ``queue_connected`` es False: aun no existe cola real."""
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "queue_connected": False,
    }
