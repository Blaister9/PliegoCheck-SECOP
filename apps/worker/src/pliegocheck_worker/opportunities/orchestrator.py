"""Consumidor PostgreSQL para la cola de oportunidades."""

from typing import Any

from pliegocheck_api.config import get_settings
from pliegocheck_api.db import get_sessionmaker
from pliegocheck_api.opportunities.service import process_next_discovery


def opportunity_run_once(worker_id: str | None = None) -> dict[str, Any]:
    worker = worker_id or "opportunity-worker"
    with get_sessionmaker()() as session:
        run = process_next_discovery(session, get_settings(), worker)
        if run is None:
            return {"status": "idle", "processed": 0, "worker_id": worker}
        return {
            "status": run.status,
            "processed": 1,
            "discovery_run_id": str(run.id),
            "worker_id": worker,
        }


def opportunity_drain(max_jobs: int = 100, worker_id: str | None = None) -> dict[str, Any]:
    processed = 0
    last: dict[str, Any] | None = None
    for _ in range(max_jobs):
        last = opportunity_run_once(worker_id)
        if not last["processed"]:
            break
        processed += 1
    return {"status": "ok", "processed": processed, "last": last}
