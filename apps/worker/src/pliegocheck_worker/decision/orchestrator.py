# mypy: ignore-errors
"""Orquestador PostgreSQL del motor deterministico de decision.

No llama OpenAI ni ningun modelo: carga snapshots, ejecuta adaptadores,
completa NOT_EVALUATED, mide cobertura, aplica reglas y persiste el resultado.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from pliegocheck_api.db import get_sessionmaker
from pliegocheck_api.decision.actions import build_action_payloads
from pliegocheck_api.decision.coverage import DecisionCoverageAnalyzer
from pliegocheck_api.decision.engine import DecisionContext, DeterministicDecisionEngine
from pliegocheck_api.decision.findings import DEFAULT_ADAPTER_REGISTRY
from pliegocheck_api.decision.policy import DecisionPolicy
from pliegocheck_api.models import (
    CompanyProfileSnapshot,
    DecisionActionItemRecord,
    DecisionEvent,
    DecisionInputFindingSnapshot,
    DecisionJob,
    DecisionPolicyVersion,
    DecisionRuleEvaluationRecord,
    DecisionRun,
    FinancialEvaluationResult,
    FinancialEvaluationRun,
    Process,
    Requirement,
    SpecializedEvaluationResult,
    SpecializedEvaluationRun,
)
from pliegocheck_schemas import (
    DecisionErrorCode,
    DecisionJobStatus,
    DecisionRunStatus,
    FinancialEvaluationRunStatus,
    SpecializedEvaluationRunStatus,
)


def decision_queue_connected() -> bool:
    try:
        sessionmaker = get_sessionmaker()
        with sessionmaker() as session:
            session.execute(select(1))
        return True
    except SQLAlchemyError:
        return False


def decision_run_once(*, worker_id: str | None = None) -> dict[str, Any]:
    worker = worker_id or "decision-worker"
    sessionmaker = get_sessionmaker()
    with sessionmaker() as session:
        job = claim_next_decision_job(session, worker)
        if job is None:
            return {"status": "idle", "processed": 0, "worker_id": worker}
        result = process_claimed_decision_job(session, job.id, worker_id=worker)
        result["worker_id"] = worker
        return result


def decision_drain(*, max_jobs: int = 100, worker_id: str | None = None) -> dict[str, Any]:
    processed = 0
    completed = 0
    failed = 0
    last: dict[str, Any] | None = None
    for _ in range(max_jobs):
        result = decision_run_once(worker_id=worker_id)
        last = result
        if result.get("processed") == 0:
            break
        processed += 1
        if result.get("job_status") in {
            DecisionJobStatus.COMPLETED.value,
            DecisionJobStatus.COMPLETED_WITH_WARNINGS.value,
        }:
            completed += 1
        if result.get("job_status") == DecisionJobStatus.FAILED.value:
            failed += 1
    return {
        "status": "ok",
        "processed": processed,
        "completed": completed,
        "failed": failed,
        "last": last,
    }


def claim_next_decision_job(session: Session, worker_id: str) -> DecisionJob | None:
    now = datetime.now(UTC)
    with session.begin():
        job = session.scalar(
            select(DecisionJob)
            .where(
                DecisionJob.status == DecisionJobStatus.PENDING.value,
                DecisionJob.available_at <= now,
            )
            .order_by(DecisionJob.priority.asc(), DecisionJob.created_at.asc())
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if job is None:
            return None
        run = _run_for_job(session, job)
        job.status = DecisionJobStatus.PROCESSING.value
        job.locked_by = worker_id
        job.locked_at = now
        job.started_at = now
        job.finished_at = None
        job.attempt_count += 1
        if run is not None:
            run.status = DecisionRunStatus.PROCESSING.value
            run.started_at = run.started_at or now
            run.error_code = None
            run.error_message = None
        _add_event(
            session,
            job=job,
            run=run,
            event_type="DECISION_STARTED",
            summary="Decision preliminar iniciada.",
            details={"worker_id": worker_id},
        )
    return job


def process_claimed_decision_job(
    session: Session, job_id: UUID, *, worker_id: str
) -> dict[str, Any]:
    job = session.get(DecisionJob, job_id)
    if job is None:
        return {"status": "error", "processed": 0, "error_code": "DECISION_JOB_NOT_FOUND"}
    run = _run_for_job(session, job)
    if run is None:
        return _fail_job(
            session,
            job,
            None,
            DecisionErrorCode.DECISION_NOT_FOUND.value,
            "El trabajo no tiene una ejecucion de decision asociada.",
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
            "engine_outcome": run.engine_outcome,
            "effective_outcome": run.effective_outcome,
            "finding_count": run.finding_count,
            "action_count": run.action_count,
        }
    except Exception:
        session.rollback()
        return _fail_job(
            session,
            job,
            run,
            DecisionErrorCode.DECISION_ENGINE_FAILED.value,
            "No fue posible completar la decision preliminar.",
        )


def _process_run(session: Session, job: DecisionJob, run: DecisionRun, *, worker_id: str) -> None:
    process = session.get(Process, run.process_id)
    snapshot = session.get(CompanyProfileSnapshot, run.company_profile_snapshot_id)
    financial_run = session.get(FinancialEvaluationRun, run.financial_evaluation_run_id)
    policy_version = session.get(DecisionPolicyVersion, run.policy_version_id)
    if process is None or snapshot is None or financial_run is None or policy_version is None:
        raise RuntimeError("decision inputs missing")
    if financial_run.status not in {
        FinancialEvaluationRunStatus.COMPLETED.value,
        FinancialEvaluationRunStatus.COMPLETED_WITH_WARNINGS.value,
    }:
        _fail_job(
            session,
            job,
            run,
            DecisionErrorCode.DECISION_FINANCIAL_EVALUATION_NOT_COMPLETED.value,
            "La evaluacion financiera referenciada no esta completada.",
            retryable=False,
        )
        return

    policy = DecisionPolicy.model_validate(policy_version.policy_payload)
    _clear_previous_outputs(session, run.id)

    requirements = _requirements_for_run(session, run)
    financial_results = list(
        session.scalars(
            select(FinancialEvaluationResult)
            .where(FinancialEvaluationResult.run_id == financial_run.id)
            .order_by(FinancialEvaluationResult.requirement_id.asc())
        ).all()
    )
    specialized_runs = list(
        session.scalars(
            select(SpecializedEvaluationRun).where(
                SpecializedEvaluationRun.process_id == run.process_id,
                SpecializedEvaluationRun.normalization_run_id == run.normalization_run_id,
                SpecializedEvaluationRun.company_id == run.company_id,
                SpecializedEvaluationRun.company_profile_snapshot_id
                == run.company_profile_snapshot_id,
                SpecializedEvaluationRun.status.in_(
                    [
                        SpecializedEvaluationRunStatus.COMPLETED.value,
                        SpecializedEvaluationRunStatus.COMPLETED_WITH_WARNINGS.value,
                    ]
                ),
            )
        ).all()
    )
    specialized_results: list[SpecializedEvaluationResult] = []
    if specialized_runs:
        specialized_results = list(
            session.scalars(
                select(SpecializedEvaluationResult)
                .where(
                    SpecializedEvaluationResult.run_id.in_(
                        [specialized_run.id for specialized_run in specialized_runs]
                    )
                )
                .order_by(SpecializedEvaluationResult.requirement_id.asc())
            ).all()
        )
    context = {
        "financial_results_by_requirement": {
            result.requirement_id: result for result in financial_results
        },
        "financial_evaluation_run_id": financial_run.id,
        "specialized_results_by_requirement": {
            result.requirement_id: result for result in specialized_results
        },
    }
    findings = DEFAULT_ADAPTER_REGISTRY.collect_all_findings(
        requirements=requirements, context=context
    )
    _add_event(
        session,
        job=job,
        run=run,
        event_type="DECISION_FINDINGS_COLLECTED",
        summary="Hallazgos canonicos construidos.",
        details={"finding_count": len(findings), "requirement_count": len(requirements)},
    )

    analyzer = DecisionCoverageAnalyzer(DEFAULT_ADAPTER_REGISTRY.available_domains())
    coverage = analyzer.analyze(findings)
    _add_event(
        session,
        job=job,
        run=run,
        event_type="DECISION_COVERAGE_ANALYZED",
        summary="Cobertura analizada.",
        details={
            "mandatory_applicable_total": coverage.mandatory_applicable_total,
            "not_evaluated_total": coverage.not_evaluated_total,
        },
    )

    effective_at = (
        run.effective_at if run.effective_at.tzinfo else run.effective_at.replace(tzinfo=UTC)
    )
    engine = DeterministicDecisionEngine()
    output = engine.decide(
        DecisionContext(
            policy=policy,
            findings=findings,
            coverage=coverage,
            effective_at=effective_at,
            process_closing_at=process.closing_at,
        )
    )

    findings_by_id = {finding.id: finding for finding in findings}
    for finding in findings:
        session.add(
            DecisionInputFindingSnapshot(
                id=finding.id,
                decision_run_id=run.id,
                source_finding_key=(
                    f"{finding.requirement_id}:{finding.source_type.value}:"
                    f"{finding.source_result_id or 'none'}"
                ),
                requirement_id=finding.requirement_id,
                category=finding.category,
                scope=finding.scope,
                modality=finding.modality,
                criticality=finding.criticality,
                criticality_basis=finding.criticality_basis,
                subsanability=finding.subsanability,
                subsanability_basis=finding.subsanability_basis,
                evaluation_domain=finding.evaluation_domain.value,
                source_type=finding.source_type.value,
                source_run_id=finding.source_run_id,
                source_result_id=finding.source_result_id,
                outcome=finding.outcome.value,
                applicability=finding.applicability.value,
                evidence_quality=finding.evidence_quality,
                review_status=finding.review_status,
                requires_human_review=finding.requires_human_review,
                is_blocking=finding.is_blocking,
                is_remediable=finding.is_remediable,
                partner_solvable=finding.partner_solvable,
                submission_blocker=finding.submission_blocker,
                condition_codes=list(finding.condition_codes),
                warning_codes=list(finding.warning_codes),
                evidence_references=list(finding.evidence_references),
            )
        )

    for evaluation in output.rule_evaluations:
        session.add(
            DecisionRuleEvaluationRecord(
                id=uuid4(),
                decision_run_id=run.id,
                rule_code=evaluation.rule_code,
                rule_version=evaluation.rule_version,
                priority=evaluation.priority,
                status=evaluation.status.value,
                suggested_outcome=(
                    evaluation.suggested_outcome.value if evaluation.suggested_outcome else None
                ),
                fact_payload=dict(evaluation.fact_payload),
                requirement_ids=[str(item) for item in evaluation.requirement_ids],
                finding_ids=[str(item) for item in evaluation.finding_ids],
                reason_code=evaluation.reason_code.value if evaluation.reason_code else None,
            )
        )
        if evaluation.status.value == "TRIGGERED":
            _add_event(
                session,
                job=job,
                run=run,
                event_type="DECISION_RULE_TRIGGERED",
                summary=f"Regla disparada: {evaluation.rule_code}.",
                details={
                    "rule_code": evaluation.rule_code,
                    "suggested_outcome": (
                        evaluation.suggested_outcome.value if evaluation.suggested_outcome else None
                    ),
                    "matched_count": evaluation.fact_payload.get("matched_count", 0),
                },
            )

    action_payloads = build_action_payloads(output, findings_by_id)
    for payload in action_payloads:
        session.add(
            DecisionActionItemRecord(
                id=uuid4(),
                decision_run_id=run.id,
                action_type=payload["action_type"],
                priority=payload["priority"],
                title_code=payload["title_code"],
                description_code=payload["description_code"],
                parameters=payload["parameters"],
                requirement_ids=payload["requirement_ids"],
                finding_ids=payload["finding_ids"],
                due_at=payload["due_at"],
            )
        )

    now = datetime.now(UTC)
    warning_count = len(output.warnings)
    run.engine_outcome = output.engine_outcome.value
    run.effective_outcome = output.engine_outcome.value
    run.reason_codes = [code.value for code in output.reason_codes]
    run.coverage_summary = coverage.model_dump(mode="json")
    run.requirement_count = len(requirements)
    run.finding_count = len(findings)
    run.action_count = len(action_payloads)
    run.warning_count = warning_count
    run.warnings = list(output.warnings)
    run.requires_human_review = output.requires_human_review
    completed_status = (
        DecisionRunStatus.COMPLETED_WITH_WARNINGS.value
        if warning_count
        else DecisionRunStatus.COMPLETED.value
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
        event_type=("DECISION_COMPLETED_WITH_WARNINGS" if warning_count else "DECISION_COMPLETED"),
        summary="Decision preliminar completada.",
        details={
            "worker_id": worker_id,
            "engine_outcome": run.engine_outcome,
            "reason_codes": run.reason_codes,
            "warning_count": warning_count,
            "action_count": run.action_count,
        },
    )
    session.commit()


def _clear_previous_outputs(session: Session, run_id: UUID) -> None:
    session.execute(
        delete(DecisionActionItemRecord).where(DecisionActionItemRecord.decision_run_id == run_id)
    )
    session.execute(
        delete(DecisionRuleEvaluationRecord).where(
            DecisionRuleEvaluationRecord.decision_run_id == run_id
        )
    )
    session.execute(
        delete(DecisionInputFindingSnapshot).where(
            DecisionInputFindingSnapshot.decision_run_id == run_id
        )
    )


def _requirements_for_run(session: Session, run: DecisionRun) -> list[Requirement]:
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


def _run_for_job(session: Session, job: DecisionJob) -> DecisionRun | None:
    if job.run_id is not None:
        run = session.get(DecisionRun, job.run_id)
        if run is not None:
            return run
    return session.scalar(
        select(DecisionRun)
        .where(DecisionRun.job_id == job.id)
        .order_by(DecisionRun.created_at.desc())
        .limit(1)
    )


def _fail_job(
    session: Session,
    job: DecisionJob,
    run: DecisionRun | None,
    code: str,
    message: str,
    *,
    retryable: bool = True,
) -> dict[str, Any]:
    now = datetime.now(UTC)
    can_retry = retryable and job.attempt_count < job.max_attempts
    job.status = DecisionJobStatus.PENDING.value if can_retry else DecisionJobStatus.FAILED.value
    if can_retry:
        job.available_at = now
    job.finished_at = None if can_retry else now
    job.locked_by = None
    job.locked_at = None
    job.last_error_code = code
    job.last_error_message = message
    if run is not None:
        run.status = (
            DecisionRunStatus.PENDING.value if can_retry else DecisionRunStatus.FAILED.value
        )
        run.finished_at = None if can_retry else now
        run.error_code = code
        run.error_message = message
    _add_event(
        session,
        job=job,
        run=run,
        event_type="DECISION_RETRIED" if can_retry else "DECISION_FAILED",
        summary=message,
        details={"error_code": code, "attempt_count": job.attempt_count},
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
    job: DecisionJob,
    run: DecisionRun | None,
    event_type: str,
    summary: str,
    details: dict[str, Any],
) -> None:
    session.add(
        DecisionEvent(
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
