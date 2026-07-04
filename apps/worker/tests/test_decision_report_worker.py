# mypy: ignore-errors
"""Pruebas del worker de reportes."""

from datetime import UTC, datetime
from uuid import uuid4

from pliegocheck_api.db import get_sessionmaker
from pliegocheck_api.models import DecisionJob, DecisionReportJob, DecisionReportPackage
from pliegocheck_schemas import DecisionReportJobStatus, DecisionReportPackageStatus
from pliegocheck_worker.reports.orchestrator import claim_next_report_job, report_drain

from .test_decision_worker import _create_decision_job


def test_report_claim_uses_skip_locked_shape() -> None:
    decision_job_id = _create_decision_job()
    with get_sessionmaker()() as session:
        decision_job = session.get(DecisionJob, decision_job_id)
        job = DecisionReportJob(
            id=uuid4(),
            process_id=decision_job.process_id,
            decision_run_id=decision_job.run_id,
            status=DecisionReportJobStatus.PENDING.value,
            available_at=datetime.now(UTC),
            force=False,
        )
        session.add(job)
        session.commit()
        claimed = claim_next_report_job(session, "report-worker-test")
        assert claimed is not None
        assert claimed.status == DecisionReportJobStatus.PROCESSING.value
        assert claimed.locked_by == "report-worker-test"


def test_report_drain_idle() -> None:
    result = report_drain(max_jobs=1, worker_id="report-idle")
    assert result["status"] == "ok"
    assert result["processed"] == 0


def test_report_package_status_enum_values() -> None:
    assert DecisionReportPackageStatus.COMPLETED.value == "COMPLETED"
    assert DecisionReportPackage.__tablename__ == "decision_report_packages"
