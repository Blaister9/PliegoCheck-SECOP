"""Comandos acotados para outbox, digests y retención."""

from typing import Any

from pliegocheck_api.config import get_settings
from pliegocheck_api.db import get_sessionmaker
from pliegocheck_api.notification_delivery.service import process_next, run_digests, run_retention
from pliegocheck_schemas import NotificationDigestPeriod


def notification_run_once(worker_id: str | None = None) -> dict[str, Any]:
    worker = worker_id or "notification-worker"
    with get_sessionmaker()() as session:
        row = process_next(session, get_settings(), worker)
        return {
            "status": row.status if row else "idle",
            "processed": int(row is not None),
            "delivery_id": str(row.id) if row else None,
            "worker_id": worker,
        }


def notification_drain(max_jobs: int = 100, worker_id: str | None = None) -> dict[str, Any]:
    processed = 0
    for _ in range(max_jobs):
        result = notification_run_once(worker_id)
        if not result["processed"]:
            break
        processed += 1
    return {"status": "ok", "processed": processed}


def notification_digest_run_once(period: str = "DAILY") -> dict[str, Any]:
    with get_sessionmaker()() as session:
        created = run_digests(session, get_settings(), NotificationDigestPeriod(period))
        return {"status": "ok", "created": created, "period": period}


def notification_retention_run_once(dry_run: bool = False) -> dict[str, Any]:
    with get_sessionmaker()() as session:
        payloads, attempts = run_retention(session, get_settings(), dry_run)
        return {
            "status": "ok",
            "dry_run": dry_run,
            "payloads_cleared": payloads,
            "attempts_deleted": attempts,
        }
