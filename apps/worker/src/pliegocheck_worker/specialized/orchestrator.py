# mypy: ignore-errors
"""Orquestador PostgreSQL de evaluaciones especializadas deterministicas."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from pliegocheck_api.db import get_sessionmaker
from pliegocheck_api.models import (
    CompanyProfileSnapshot,
    Process,
    Requirement,
    SpecializedEvaluationEvent,
    SpecializedEvaluationEvidence,
    SpecializedEvaluationJob,
    SpecializedEvaluationResult,
    SpecializedEvaluationRun,
    SpecializedRequirementRule,
)
from pliegocheck_api.specialized_evaluation import evaluate_specialized_requirement
from pliegocheck_schemas import (
    SpecializedErrorCode,
    SpecializedEvaluationJobStatus,
    SpecializedEvaluationResultStatus,
    SpecializedEvaluationRunStatus,
    SpecializedEvidenceValidationStatus,
)


def specialized_queue_connected() -> bool:
    try:
        sessionmaker = get_sessionmaker()
        with sessionmaker() as session:
            session.execute(select(1))
        return True
    except SQLAlchemyError:
        return False


def specialized_run_once(*, worker_id: str | None = None) -> dict[str, Any]:
    worker = worker_id or "specialized-worker"
    sessionmaker = get_sessionmaker()
    with sessionmaker() as session:
        job = claim_next_specialized_job(session, worker)
        if job is None:
            return {"status": "idle", "processed": 0, "worker_id": worker}
        result = process_claimed_specialized_job(session, job.id, worker_id=worker)
        result["worker_id"] = worker
        return result


def specialized_drain(*, max_jobs: int = 100, worker_id: str | None = None) -> dict[str, Any]:
    processed = 0
    completed = 0
    failed = 0
    last: dict[str, Any] | None = None
    for _ in range(max_jobs):
        result = specialized_run_once(worker_id=worker_id)
        last = result
        if result.get("processed") == 0:
            break
        processed += 1
        if result.get("job_status") in {
            SpecializedEvaluationJobStatus.COMPLETED.value,
            SpecializedEvaluationJobStatus.COMPLETED_WITH_WARNINGS.value,
        }:
            completed += 1
        if result.get("job_status") == SpecializedEvaluationJobStatus.FAILED.value:
            failed += 1
    return {
        "status": "ok",
        "processed": processed,
        "completed": completed,
        "failed": failed,
        "last": last,
    }


def claim_next_specialized_job(session: Session, worker_id: str) -> SpecializedEvaluationJob | None:
    now = datetime.now(UTC)
    with session.begin():
        job = session.scalar(
            select(SpecializedEvaluationJob)
            .where(
                SpecializedEvaluationJob.status == SpecializedEvaluationJobStatus.PENDING.value,
                SpecializedEvaluationJob.available_at <= now,
            )
            .order_by(
                SpecializedEvaluationJob.priority.asc(),
                SpecializedEvaluationJob.created_at.asc(),
            )
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if job is None:
            return None
        run = _run_for_job(session, job)
        job.status = SpecializedEvaluationJobStatus.PROCESSING.value
        job.locked_by = worker_id
        job.locked_at = now
        job.started_at = now
        job.finished_at = None
        job.attempt_count += 1
        if run is not None:
            run.status = SpecializedEvaluationRunStatus.PROCESSING.value
            run.started_at = run.started_at or now
            run.error_code = None
            run.error_message = None
        _add_event(
            session,
            job=job,
            run=run,
            event_type="SPECIALIZED_EVALUATION_STARTED",
            summary="Evaluacion especializada iniciada.",
            details={"worker_id": worker_id, "domain": job.domain},
        )
    return job


def process_claimed_specialized_job(
    session: Session, job_id: UUID, *, worker_id: str
) -> dict[str, Any]:
    job = session.get(SpecializedEvaluationJob, job_id)
    if job is None:
        return {"status": "error", "processed": 0, "error_code": "SPECIALIZED_JOB_NOT_FOUND"}
    run = _run_for_job(session, job)
    if run is None:
        return _fail_job(
            session,
            job,
            None,
            SpecializedErrorCode.SPECIALIZED_EVALUATION_NOT_FOUND.value,
            "El trabajo no tiene una ejecucion especializada asociada.",
        )
    try:
        _process_run(session, job, run, worker_id=worker_id)
        return {
            "status": "ok",
            "processed": 1,
            "job_id": str(job.id),
            "run_id": str(run.id),
            "domain": run.domain,
            "job_status": job.status,
            "run_status": run.status,
            "evaluated_count": run.evaluated_count,
            "unknown_count": run.unknown_count,
            "conflicting_count": run.conflicting_count,
        }
    except Exception:
        session.rollback()
        return _fail_job(
            session,
            job,
            run,
            SpecializedErrorCode.SPECIALIZED_EVALUATION_FAILED.value,
            "No fue posible completar la evaluacion especializada.",
        )


def _process_run(
    session: Session,
    job: SpecializedEvaluationJob,
    run: SpecializedEvaluationRun,
    *,
    worker_id: str,
) -> None:
    process = session.get(Process, run.process_id)
    snapshot = session.get(CompanyProfileSnapshot, run.company_profile_snapshot_id)
    if process is None or snapshot is None:
        raise RuntimeError("specialized inputs missing")
    _clear_previous_outputs(session, run.id)
    requirements = _requirements_for_run(session, run)
    rules = _rules_for_run(session, run)
    rules_by_requirement = {rule.requirement_id: rule for rule in rules}
    counts = {status.value: 0 for status in SpecializedEvaluationResultStatus}
    warning_count = 0
    effective_at = _effective_at_for_run(run)
    for requirement in requirements:
        rule = rules_by_requirement.get(requirement.id)
        if rule is None:
            warning_count += 1
            continue
        outcome = evaluate_specialized_requirement(
            requirement=requirement,
            rule=rule,
            snapshot_payload=snapshot.payload,
            effective_at=effective_at,
        )
        result = SpecializedEvaluationResult(
            id=uuid4(),
            run_id=run.id,
            requirement_id=requirement.id,
            specialized_rule_id=rule.id,
            domain=outcome["domain"],
            status=outcome["status"],
            rule_type=outcome["rule_type"],
            subject=outcome["subject"],
            operator=outcome["operator"],
            expected_value=outcome["expected_value"],
            actual_value=outcome["actual_value"],
            unit=outcome["unit"],
            source_record_type=outcome["source_record_type"],
            source_record_id=outcome["source_record_id"],
            explanation_code=outcome["explanation_code"],
            explanation_parameters=outcome["explanation_parameters"],
            evidence_refs=outcome["evidence_refs"],
            requires_human_review=outcome["requires_human_review"],
            review_status="PENDING",
        )
        session.add(result)
        session.flush()
        _persist_evidence(session, result.id, outcome["evidence_refs"])
        counts[outcome["status"]] += 1
        if outcome["requires_human_review"]:
            warning_count += 1
        _add_event(
            session,
            job=job,
            run=run,
            event_type="SPECIALIZED_REQUIREMENT_EVALUATED",
            summary="Requisito especializado evaluado.",
            details={
                "requirement_id": str(requirement.id),
                "result_id": str(result.id),
                "status": result.status,
            },
        )
    now = datetime.now(UTC)
    run.evaluated_count = sum(counts.values())
    run.complies_count = counts[SpecializedEvaluationResultStatus.COMPLIES.value]
    run.does_not_comply_count = counts[SpecializedEvaluationResultStatus.DOES_NOT_COMPLY.value]
    run.partial_count = counts[SpecializedEvaluationResultStatus.PARTIAL.value]
    run.unknown_count = counts[SpecializedEvaluationResultStatus.UNKNOWN.value]
    run.not_applicable_count = counts[SpecializedEvaluationResultStatus.NOT_APPLICABLE.value]
    run.conflicting_count = counts[SpecializedEvaluationResultStatus.CONFLICTING_EVIDENCE.value]
    run.warning_count = warning_count
    completed_status = (
        SpecializedEvaluationRunStatus.COMPLETED_WITH_WARNINGS.value
        if warning_count
        else SpecializedEvaluationRunStatus.COMPLETED.value
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
        event_type=(
            "SPECIALIZED_EVALUATION_COMPLETED_WITH_WARNINGS"
            if warning_count
            else "SPECIALIZED_EVALUATION_COMPLETED"
        ),
        summary="Evaluacion especializada completada.",
        details={
            "worker_id": worker_id,
            "domain": run.domain,
            "evaluated_count": run.evaluated_count,
            "warning_count": warning_count,
        },
    )
    session.commit()


def _persist_evidence(session: Session, result_id: UUID, evidence_refs: dict[str, Any]) -> None:
    for link in evidence_refs.get("links", []):
        if not isinstance(link, dict):
            continue
        session.add(
            SpecializedEvaluationEvidence(
                id=uuid4(),
                result_id=result_id,
                evidence_type="COMPANY_EVIDENCE_LINK",
                company_evidence_link_id=_uuid_or_none(link.get("id")),
                company_evidence_document_id=_uuid_or_none(link.get("document_id")),
                extracted_segment_id=_uuid_or_none(link.get("segment_id")),
                quoted_text=link.get("quoted_text"),
                source_location=link.get("source_location") or {},
                validation_status=_validation_status(link),
            )
        )


def _validation_status(link: dict[str, Any]) -> str:
    role = link.get("evidence_role")
    review = link.get("review_status")
    if role == "CONFLICTING":
        return SpecializedEvidenceValidationStatus.CONFLICTING.value
    if review == "VERIFIED":
        return SpecializedEvidenceValidationStatus.VERIFIED.value
    if review == "SUPPORTED":
        return SpecializedEvidenceValidationStatus.SUPPORTED.value
    if review == "REJECTED":
        return SpecializedEvidenceValidationStatus.REJECTED.value
    return SpecializedEvidenceValidationStatus.DECLARED_ONLY.value


def _clear_previous_outputs(session: Session, run_id: UUID) -> None:
    result_ids = [
        item
        for item in session.scalars(
            select(SpecializedEvaluationResult.id).where(
                SpecializedEvaluationResult.run_id == run_id
            )
        ).all()
    ]
    if result_ids:
        session.execute(
            delete(SpecializedEvaluationEvidence).where(
                SpecializedEvaluationEvidence.result_id.in_(result_ids)
            )
        )
    session.execute(
        delete(SpecializedEvaluationResult).where(SpecializedEvaluationResult.run_id == run_id)
    )


def _requirements_for_run(session: Session, run: SpecializedEvaluationRun) -> list[Requirement]:
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


def _effective_at_for_run(run: SpecializedEvaluationRun) -> datetime:
    raw_value = (run.input_manifest or {}).get("effective_at")
    if isinstance(raw_value, str) and raw_value:
        return datetime.fromisoformat(raw_value).replace(tzinfo=UTC)
    return datetime.now(UTC)


def _rules_for_run(
    session: Session, run: SpecializedEvaluationRun
) -> list[SpecializedRequirementRule]:
    ids = [
        UUID(item["rule_id"])
        for item in run.input_manifest.get("specialized_rule_versions", [])
        if isinstance(item, dict) and item.get("rule_id")
    ]
    if not ids:
        return []
    return list(
        session.scalars(
            select(SpecializedRequirementRule)
            .where(SpecializedRequirementRule.id.in_(ids))
            .order_by(SpecializedRequirementRule.requirement_id.asc())
        ).all()
    )


def _run_for_job(
    session: Session, job: SpecializedEvaluationJob
) -> SpecializedEvaluationRun | None:
    if job.run_id is not None:
        run = session.get(SpecializedEvaluationRun, job.run_id)
        if run is not None:
            return run
    return session.scalar(
        select(SpecializedEvaluationRun)
        .where(SpecializedEvaluationRun.job_id == job.id)
        .order_by(SpecializedEvaluationRun.created_at.desc())
        .limit(1)
    )


def _fail_job(
    session: Session,
    job: SpecializedEvaluationJob,
    run: SpecializedEvaluationRun | None,
    code: str,
    message: str,
) -> dict[str, Any]:
    now = datetime.now(UTC)
    can_retry = job.attempt_count < job.max_attempts
    job.status = (
        SpecializedEvaluationJobStatus.PENDING.value
        if can_retry
        else SpecializedEvaluationJobStatus.FAILED.value
    )
    job.available_at = now
    job.finished_at = None if can_retry else now
    job.locked_by = None
    job.locked_at = None
    job.last_error_code = code
    job.last_error_message = message
    if run is not None:
        run.status = (
            SpecializedEvaluationRunStatus.PENDING.value
            if can_retry
            else SpecializedEvaluationRunStatus.FAILED.value
        )
        run.finished_at = None if can_retry else now
        run.error_code = code
        run.error_message = message
    _add_event(
        session,
        job=job,
        run=run,
        event_type="SPECIALIZED_EVALUATION_RETRIED"
        if can_retry
        else "SPECIALIZED_EVALUATION_FAILED",
        summary=message,
        details={"error_code": code, "attempt_count": job.attempt_count},
    )
    session.commit()
    return {
        "status": "error",
        "processed": 1,
        "job_id": str(job.id),
        "run_id": str(run.id) if run is not None else None,
        "domain": job.domain,
        "job_status": job.status,
        "run_status": run.status if run is not None else None,
        "error_code": code,
        "error_message": message,
    }


def _add_event(
    session: Session,
    *,
    job: SpecializedEvaluationJob,
    run: SpecializedEvaluationRun | None,
    event_type: str,
    summary: str,
    details: dict[str, Any],
) -> None:
    session.add(
        SpecializedEvaluationEvent(
            id=uuid4(),
            job_id=job.id,
            run_id=run.id if run is not None else None,
            process_id=job.process_id,
            company_id=job.company_id,
            domain=job.domain,
            event_type=event_type,
            summary=summary,
            details=details,
        )
    )


def _uuid_or_none(value: Any) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    return UUID(str(value))
