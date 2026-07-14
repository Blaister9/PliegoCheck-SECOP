"""Consumidores PostgreSQL para trabajos SECOP documentales."""

from __future__ import annotations

from typing import Any

from pliegocheck_api.config import get_settings
from pliegocheck_api.db import get_sessionmaker
from pliegocheck_api.external_documents.service import (
    claim_download,
    claim_sync,
    execute_download,
    execute_sync,
)


def external_sync_run_once(worker_id: str | None = None) -> dict[str, Any]:
    worker = worker_id or "secop-sync-worker"
    with get_sessionmaker()() as session:
        run = claim_sync(session, worker)
        if run is None:
            return {"status": "idle", "processed": 0, "worker_id": worker}
        result = execute_sync(session, get_settings(), run.id)
        return {
            "status": result.status,
            "processed": 1,
            "sync_run_id": str(result.id),
            "worker_id": worker,
        }


def external_sync_drain(max_jobs: int = 100, worker_id: str | None = None) -> dict[str, Any]:
    return _drain(external_sync_run_once, max_jobs, worker_id)


def external_download_run_once(worker_id: str | None = None) -> dict[str, Any]:
    worker = worker_id or "secop-download-worker"
    with get_sessionmaker()() as session:
        job = claim_download(session, worker)
        if job is None:
            return {"status": "idle", "processed": 0, "worker_id": worker}
        result = execute_download(session, get_settings(), job.id)
        return {
            "status": result.status,
            "processed": 1,
            "download_job_id": str(result.id),
            "worker_id": worker,
        }


def external_download_drain(max_jobs: int = 100, worker_id: str | None = None) -> dict[str, Any]:
    return _drain(external_download_run_once, max_jobs, worker_id)


def _drain(run_once: Any, max_jobs: int, worker_id: str | None) -> dict[str, Any]:
    processed = 0
    last = None
    for _ in range(max_jobs):
        last = run_once(worker_id)
        if not last["processed"]:
            break
        processed += 1
    return {"status": "ok", "processed": processed, "last": last}
