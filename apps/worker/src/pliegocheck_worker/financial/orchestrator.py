# mypy: ignore-errors
"""Orquestador PostgreSQL de evaluacion financiera deterministica."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from pliegocheck_api.db import get_sessionmaker
from pliegocheck_api.financial import evaluate_financial_requirement
from pliegocheck_api.models import (
    CompanyProfileSnapshot,
    FinancialEvaluationEvent,
    FinancialEvaluationJob,
    FinancialEvaluationResult,
    FinancialEvaluationRun,
    FinancialMetricCalculation,
    FinancialRequirementRule,
    Process,
    Requirement,
)
from pliegocheck_schemas import (
    FinancialErrorCode,
    FinancialEvaluationJobStatus,
    FinancialEvaluationResultStatus,
    FinancialEvaluationRunStatus,
)


def financial_queue_connected() -> bool:
    try:
        sessionmaker = get_sessionmaker()
        with sessionmaker() as session:
            session.execute(select(1))
        return True
    except SQLAlchemyError:
        return False


def financial_run_once(*, worker_id: str | None = None) -> dict[str, Any]:
    worker = worker_id or "financial-worker"
    sessionmaker = get_sessionmaker()
    with sessionmaker() as session:
        job = claim_next_financial_job(session, worker)
        if job is None:
            return {"status": "idle", "processed": 0, "worker_id": worker}
        result = process_claimed_financial_job(session, job.id, worker_id=worker)
        result["worker_id"] = worker
        return result


def financial_drain(*, max_jobs: int = 100, worker_id: str | None = None) -> dict[str, Any]:
    processed = 0
    completed = 0
    failed = 0
    last: dict[str, Any] | None = None
    for _ in range(max_jobs):
        result = financial_run_once(worker_id=worker_id)
        last = result
        if result.get("processed") == 0:
            break
        processed += 1
        if result.get("job_status") in {
            FinancialEvaluationJobStatus.COMPLETED.value,
            FinancialEvaluationJobStatus.COMPLETED_WITH_WARNINGS.value,
        }:
            completed += 1
        if result.get("job_status") == FinancialEvaluationJobStatus.FAILED.value:
            failed += 1
    return {
        "status": "ok",
        "processed": processed,
        "completed": completed,
        "failed": failed,
        "last": last,
    }


def claim_next_financial_job(
    session: Session,
    worker_id: str,
) -> FinancialEvaluationJob | None:
    now = datetime.now(UTC)
    with session.begin():
        job = session.scalar(
            select(FinancialEvaluationJob)
            .where(
                FinancialEvaluationJob.status == FinancialEvaluationJobStatus.PENDING.value,
                FinancialEvaluationJob.available_at <= now,
            )
            .order_by(
                FinancialEvaluationJob.priority.asc(),
                FinancialEvaluationJob.created_at.asc(),
            )
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if job is None:
            return None
        run = _run_for_job(session, job)
        job.status = FinancialEvaluationJobStatus.PROCESSING.value
        job.locked_by = worker_id
        job.locked_at = now
        job.started_at = now
        job.finished_at = None
        job.attempt_count += 1
        if run is not None:
            run.status = FinancialEvaluationRunStatus.PROCESSING.value
            run.started_at = run.started_at or now
            run.error_code = None
            run.error_message = None
        _add_event(
            session,
            job=job,
            run=run,
            event_type="FINANCIAL_EVALUATION_STARTED",
            summary="Evaluacion financiera iniciada.",
            details={"worker_id": worker_id},
        )
    return job


def process_claimed_financial_job(
    session: Session,
    job_id: UUID,
    *,
    worker_id: str,
) -> dict[str, Any]:
    job = session.get(FinancialEvaluationJob, job_id)
    if job is None:
        return {"status": "error", "processed": 0, "error_code": "FINANCIAL_JOB_NOT_FOUND"}
    run = _run_for_job(session, job)
    if run is None:
        return _fail_job(
            session,
            job,
            None,
            FinancialErrorCode.FINANCIAL_EVALUATION_NOT_FOUND.value,
            "El trabajo no tiene una ejecucion financiera asociada.",
        )
    try:
        _process_run(session, job, run, worker_id=worker_id)
        return {
            "status": "ok",
            "processed": 1,
            "job_id": str(job.id),
            "run_id": str(run.id),
            "job_status": job.status,
            "run_status": run.status,
            "evaluated_count": run.evaluated_count,
            "unknown_count": run.unknown_count,
            "conflicting_count": run.conflicting_count,
        }
    except Exception:
        return _fail_job(
            session,
            job,
            run,
            FinancialErrorCode.FINANCIAL_EVALUATION_FAILED.value,
            "No fue posible completar la evaluacion financiera.",
        )


def _process_run(
    session: Session,
    job: FinancialEvaluationJob,
    run: FinancialEvaluationRun,
    *,
    worker_id: str,
) -> None:
    process = session.get(Process, run.process_id)
    snapshot = session.get(CompanyProfileSnapshot, run.company_profile_snapshot_id)
    if process is None or snapshot is None:
        raise RuntimeError("financial inputs missing")
    _clear_previous_outputs(session, run.id)
    requirements = _requirements_for_run(session, run)
    rules = _rules_for_run(session, run)
    rules_by_requirement = {rule.requirement_id: rule for rule in rules}
    counts = {
        FinancialEvaluationResultStatus.COMPLIES.value: 0,
        FinancialEvaluationResultStatus.DOES_NOT_COMPLY.value: 0,
        FinancialEvaluationResultStatus.PARTIAL.value: 0,
        FinancialEvaluationResultStatus.UNKNOWN.value: 0,
        FinancialEvaluationResultStatus.NOT_APPLICABLE.value: 0,
        FinancialEvaluationResultStatus.CONFLICTING_EVIDENCE.value: 0,
    }
    warning_count = 0
    for requirement in requirements:
        rule = rules_by_requirement.get(requirement.id)
        if rule is None:
            warning_count += 1
            continue
        outcome = evaluate_financial_requirement(
            requirement=requirement,
            rule=rule,
            snapshot_payload=snapshot.payload,
            process_closing_at=process.closing_at,
        )
        calculation_id = _persist_calculation(session, run.id, outcome.get("calculation"))
        result = FinancialEvaluationResult(
            id=uuid4(),
            run_id=run.id,
            requirement_id=requirement.id,
            financial_rule_id=rule.id,
            status=outcome["status"],
            metric_type=outcome.get("metric_type"),
            operator=outcome.get("operator"),
            required_value=outcome.get("required_value"),
            required_min_value=outcome.get("required_min_value"),
            required_max_value=outcome.get("required_max_value"),
            required_unit=outcome.get("required_unit"),
            actual_value=outcome.get("actual_value"),
            actual_unit=outcome.get("actual_unit"),
            currency=outcome.get("currency"),
            financial_period_id=outcome.get("financial_period_id"),
            calculation_id=calculation_id,
            explanation_code=outcome["explanation_code"],
            explanation_parameters=outcome["explanation_parameters"],
            metric_inputs=_json_safe(outcome["metric_inputs"]),
            evidence_refs=_json_safe(outcome["evidence_refs"]),
            requires_human_review=outcome["requires_human_review"],
            review_status="PENDING",
        )
        session.add(result)
        counts[outcome["status"]] += 1
        if outcome["requires_human_review"] or outcome.get("calculation", {}).get("warning_codes"):
            warning_count += 1
    now = datetime.now(UTC)
    run.evaluated_count = sum(counts.values())
    run.complies_count = counts[FinancialEvaluationResultStatus.COMPLIES.value]
    run.does_not_comply_count = counts[FinancialEvaluationResultStatus.DOES_NOT_COMPLY.value]
    run.partial_count = counts[FinancialEvaluationResultStatus.PARTIAL.value]
    run.unknown_count = counts[FinancialEvaluationResultStatus.UNKNOWN.value]
    run.not_applicable_count = counts[FinancialEvaluationResultStatus.NOT_APPLICABLE.value]
    run.conflicting_count = counts[FinancialEvaluationResultStatus.CONFLICTING_EVIDENCE.value]
    run.warning_count = warning_count
    completed_status = (
        FinancialEvaluationRunStatus.COMPLETED_WITH_WARNINGS.value
        if warning_count
        else FinancialEvaluationRunStatus.COMPLETED.value
    )
    run.status = completed_status
    run.finished_at = now
    run.error_code = None
    run.error_message = None
    job.status = completed_status
    job.finished_at = now
    job.locked_by = None
    job.locked_at = None
    job.last_error_code = None
    job.last_error_message = None
    _add_event(
        session,
        job=job,
        run=run,
        event_type="FINANCIAL_EVALUATION_COMPLETED",
        summary="Evaluacion financiera completada.",
        details={
            "worker_id": worker_id,
            "evaluated_count": run.evaluated_count,
            "unknown_count": run.unknown_count,
            "conflicting_count": run.conflicting_count,
            "warning_count": warning_count,
        },
    )
    session.commit()


def _clear_previous_outputs(session: Session, run_id: UUID) -> None:
    session.execute(
        delete(FinancialEvaluationResult).where(FinancialEvaluationResult.run_id == run_id)
    )
    session.execute(
        delete(FinancialMetricCalculation).where(FinancialMetricCalculation.run_id == run_id)
    )


def _requirements_for_run(session: Session, run: FinancialEvaluationRun) -> list[Requirement]:
    ids = [UUID(item) for item in run.input_manifest.get("requirement_ids", [])]
    if not ids:
        return []
    return list(
        session.scalars(
            select(Requirement)
            .where(Requirement.id.in_(ids))
            .order_by(Requirement.created_at.asc(), Requirement.id.asc())
        ).all()
    )


def _rules_for_run(session: Session, run: FinancialEvaluationRun) -> list[FinancialRequirementRule]:
    ids = [
        UUID(item["rule_id"])
        for item in run.input_manifest.get("financial_rule_versions", [])
        if isinstance(item, dict) and item.get("rule_id")
    ]
    if not ids:
        return []
    return list(
        session.scalars(
            select(FinancialRequirementRule)
            .where(FinancialRequirementRule.id.in_(ids))
            .order_by(
                FinancialRequirementRule.requirement_id.asc(),
                FinancialRequirementRule.version.asc(),
            )
        ).all()
    )


def _persist_calculation(
    session: Session, run_id: UUID, payload: dict[str, Any] | None
) -> UUID | None:
    if payload is None:
        return None
    calculation = FinancialMetricCalculation(
        id=uuid4(),
        run_id=run_id,
        financial_period_id=payload.get("financial_period_id"),
        metric_type=payload["metric_type"],
        formula_name=payload["formula_name"],
        formula_version=payload["formula_version"],
        input_values=payload["input_values"],
        raw_result=payload.get("raw_result"),
        rounded_result=payload.get("rounded_result"),
        unit=payload.get("unit"),
        status=payload["status"],
        warning_codes=payload.get("warning_codes", []),
    )
    session.add(calculation)
    session.flush()
    return calculation.id


def _run_for_job(session: Session, job: FinancialEvaluationJob) -> FinancialEvaluationRun | None:
    if job.run_id is not None:
        run = session.get(FinancialEvaluationRun, job.run_id)
        if run is not None:
            return run
    return session.scalar(
        select(FinancialEvaluationRun)
        .where(FinancialEvaluationRun.job_id == job.id)
        .order_by(FinancialEvaluationRun.created_at.desc())
        .limit(1)
    )


def _fail_job(
    session: Session,
    job: FinancialEvaluationJob,
    run: FinancialEvaluationRun | None,
    code: str,
    message: str,
) -> dict[str, Any]:
    now = datetime.now(UTC)
    job.status = FinancialEvaluationJobStatus.FAILED.value
    job.finished_at = now
    job.locked_by = None
    job.locked_at = None
    job.last_error_code = code
    job.last_error_message = message
    if run is not None:
        run.status = FinancialEvaluationRunStatus.FAILED.value
        run.finished_at = now
        run.error_code = code
        run.error_message = message
    _add_event(
        session,
        job=job,
        run=run,
        event_type="FINANCIAL_EVALUATION_FAILED",
        summary=message,
        details={"error_code": code},
    )
    session.commit()
    return {
        "status": "error",
        "processed": 1,
        "job_id": str(job.id),
        "run_id": str(run.id) if run is not None else None,
        "job_status": job.status,
        "run_status": run.status if run is not None else None,
        "error_code": code,
        "error_message": message,
    }


def _add_event(
    session: Session,
    *,
    job: FinancialEvaluationJob,
    run: FinancialEvaluationRun | None,
    event_type: str,
    summary: str,
    details: dict[str, Any],
) -> None:
    session.add(
        FinancialEvaluationEvent(
            id=uuid4(),
            job_id=job.id,
            run_id=run.id if run is not None else None,
            process_id=job.process_id,
            company_id=job.company_id,
            event_type=event_type,
            summary=summary,
            details=details,
        )
    )


def _json_safe(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "as_tuple"):
        return str(value)
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    return value
