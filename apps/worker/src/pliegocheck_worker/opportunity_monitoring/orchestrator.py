"""Comandos acotados del scheduler y consumidor PostgreSQL."""

from typing import Any

from pliegocheck_api.config import get_settings
from pliegocheck_api.db import get_sessionmaker
from pliegocheck_api.opportunity_monitoring.service import process_next_monitor_run, scheduler_tick


def monitor_scheduler_run_once() -> dict[str, Any]:
    with get_sessionmaker()() as session:
        runs = scheduler_tick(session, get_settings())
        return {"status": "ok", "queued": len(runs), "run_ids": [str(row.id) for row in runs]}


def monitor_run_once(worker_id: str | None = None) -> dict[str, Any]:
    worker = worker_id or "opportunity-monitor-worker"
    with get_sessionmaker()() as session:
        row = process_next_monitor_run(session, get_settings(), worker)
        return {
            "status": row.status if row else "idle",
            "processed": int(row is not None),
            "monitor_run_id": str(row.id) if row else None,
            "worker_id": worker,
        }


def monitor_drain(max_jobs: int = 100, worker_id: str | None = None) -> dict[str, Any]:
    processed = 0
    for _ in range(max_jobs):
        result = monitor_run_once(worker_id)
        if not result["processed"]:
            break
        processed += 1
    return {"status": "ok", "processed": processed}
