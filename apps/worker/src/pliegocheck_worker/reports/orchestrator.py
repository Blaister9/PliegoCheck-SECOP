# mypy: ignore-errors
"""Orquestador PostgreSQL de reportes de decision."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from pliegocheck_api.db import get_sessionmaker
from pliegocheck_api.models import (
    DecisionReportEvent,
    DecisionReportJob,
    DecisionReportPackage,
)
from pliegocheck_api.reports.service import generate_report_package
from pliegocheck_schemas import (
    DecisionReportErrorCode,
    DecisionReportJobStatus,
    DecisionReportPackageStatus,
)


def report_queue_connected() -> bool:
    try:
        sessionmaker = get_sessionmaker()
        with sessionmaker() as session:
            session.execute(select(1))
        return True
    except SQLAlchemyError:
        return False


def report_run_once(*, worker_id: str | None = None) -> dict[str, Any]:
    worker = worker_id or "report-worker"
    sessionmaker = get_sessionmaker()
    with sessionmaker() as session:
        job = claim_next_report_job(session, worker)
        if job is None:
            return {"status": "idle", "processed": 0, "worker_id": worker}
        result = process_claimed_report_job(session, job.id, worker_id=worker)
        result["worker_id"] = worker
        return result


def report_drain(*, max_jobs: int = 100, worker_id: str | None = None) -> dict[str, Any]:
    processed = 0
    completed = 0
    failed = 0
    last: dict[str, Any] | None = None
    for _ in range(max_jobs):
        result = report_run_once(worker_id=worker_id)
        last = result
        if result.get("processed") == 0:
            break
        processed += 1
        if result.get("job_status") in {
            DecisionReportJobStatus.COMPLETED.value,
            DecisionReportJobStatus.COMPLETED_WITH_WARNINGS.value,
        }:
            completed += 1
        if result.get("job_status") == DecisionReportJobStatus.FAILED.value:
            failed += 1
    return {
        "status": "ok",
        "processed": processed,
        "completed": completed,
        "failed": failed,
        "last": last,
    }


def claim_next_report_job(session: Session, worker_id: str) -> DecisionReportJob | None:
    now = datetime.now(UTC)
    with session.begin():
        job = session.scalar(
            select(DecisionReportJob)
            .where(
                DecisionReportJob.status == DecisionReportJobStatus.PENDING.value,
                DecisionReportJob.available_at <= now,
            )
            .order_by(DecisionReportJob.priority.asc(), DecisionReportJob.created_at.asc())
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if job is None:
            return None
        package = _package_for_job(session, job)
        job.status = DecisionReportJobStatus.PROCESSING.value
        job.locked_by = worker_id
        job.locked_at = now
        job.started_at = now
        job.finished_at = None
        job.attempt_count += 1
        if package is not None:
            package.status = DecisionReportPackageStatus.GENERATING.value
            package.error_code = None
            package.error_message = None
        _add_event(
            session, job, package, "DECISION_REPORT_STARTED", "Generacion de reporte iniciada."
        )
    return job


def process_claimed_report_job(session: Session, job_id: UUID, *, worker_id: str) -> dict[str, Any]:
    job = session.get(DecisionReportJob, job_id)
    if job is None:
        return {"status": "error", "processed": 0, "error_code": "DECISION_REPORT_JOB_NOT_FOUND"}
    package = _package_for_job(session, job)
    if package is None:
        return _fail_job(
            session,
            job,
            None,
            DecisionReportErrorCode.DECISION_REPORT_PACKAGE_NOT_FOUND.value,
            "El trabajo no tiene paquete asociado.",
        )
    try:
        generate_report_package(session, package.id, worker_id)
        job.status = package.status.replace("COMPLETED_WITH_WARNINGS", "COMPLETED_WITH_WARNINGS")
        job.finished_at = datetime.now(UTC)
        job.locked_by = None
        job.locked_at = None
        job.last_error_code = None
        job.last_error_message = None
        _add_event(
            session, job, package, "DECISION_REPORT_COMPLETED", "Paquete de reporte completado."
        )
        session.commit()
        return {
            "status": "ok",
            "processed": 1,
            "job_id": str(job.id),
            "package_id": str(package.id),
            "job_status": job.status,
            "package_status": package.status,
            "artifact_count": package.artifact_count,
        }
    except Exception:
        session.rollback()
        return _fail_job(
            session,
            job,
            package,
            DecisionReportErrorCode.DECISION_REPORT_FAILED.value,
            "No fue posible completar el paquete de reporte.",
        )


def _package_for_job(session: Session, job: DecisionReportJob) -> DecisionReportPackage | None:
    if job.package_id is not None:
        package = session.get(DecisionReportPackage, job.package_id)
        if package is not None:
            return package
    return session.scalar(
        select(DecisionReportPackage)
        .where(DecisionReportPackage.job_id == job.id)
        .order_by(DecisionReportPackage.created_at.desc())
        .limit(1)
    )


def _fail_job(
    session: Session,
    job: DecisionReportJob,
    package: DecisionReportPackage | None,
    code: str,
    message: str,
) -> dict[str, Any]:
    now = datetime.now(UTC)
    can_retry = job.attempt_count < job.max_attempts
    job.status = (
        DecisionReportJobStatus.PENDING.value if can_retry else DecisionReportJobStatus.FAILED.value
    )
    job.available_at = now
    job.finished_at = None if can_retry else now
    job.locked_by = None
    job.locked_at = None
    job.last_error_code = code
    job.last_error_message = message
    if package is not None:
        package.status = (
            DecisionReportPackageStatus.GENERATING.value
            if can_retry
            else DecisionReportPackageStatus.FAILED.value
        )
        package.error_code = code
        package.error_message = message
    _add_event(
        session,
        job,
        package,
        "DECISION_REPORT_RETRIED" if can_retry else "DECISION_REPORT_FAILED",
        message,
    )
    session.commit()
    return {
        "status": "error",
        "processed": 1,
        "job_id": str(job.id),
        "package_id": str(package.id) if package is not None else None,
        "job_status": job.status,
        "package_status": package.status if package is not None else None,
        "error_code": code,
        "error_message": message,
    }


def _add_event(
    session: Session,
    job: DecisionReportJob,
    package: DecisionReportPackage | None,
    event_type: str,
    summary: str,
) -> None:
    session.add(
        DecisionReportEvent(
            job_id=job.id,
            package_id=package.id if package is not None else None,
            process_id=job.process_id,
            decision_run_id=job.decision_run_id,
            event_type=event_type,
            summary=summary,
            details={"attempt_count": job.attempt_count},
        )
    )
