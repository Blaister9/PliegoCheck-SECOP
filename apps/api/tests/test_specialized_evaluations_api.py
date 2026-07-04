# mypy: ignore-errors
"""Pruebas API de evaluaciones especializadas."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from pliegocheck_api.db import get_sessionmaker
from pliegocheck_api.models import (
    CompanyProfile,
    CompanyProfileSnapshot,
    Process,
    Requirement,
    RequirementNormalizationJob,
    RequirementNormalizationRun,
)
from pliegocheck_api.prompt_registry import (
    CONSOLIDATION_PROMPT,
    NORMALIZATION_PROMPT,
    ensure_prompt_version,
)
from pliegocheck_schemas import (
    CompanyProfileStatus,
    CompanySnapshotStatus,
    NormalizationProvider,
    ProcessSource,
    ProcessStatus,
    RequirementBasis,
    RequirementCategory,
    RequirementCriticality,
    RequirementEvidenceStatus,
    RequirementModality,
    RequirementNormalizationStatus,
    RequirementReviewStatus,
    RequirementScope,
    RequirementSubsanability,
)
from pliegocheck_worker.specialized.orchestrator import specialized_run_once


def test_specialized_evaluation_api_flow(client: TestClient) -> None:
    ids = _create_inputs()
    readiness = client.get(
        f"/processes/{ids['process_id']}/specialized-evaluations/readiness",
        params={
            "normalization_run_id": str(ids["normalization_run_id"]),
            "company_profile_snapshot_id": str(ids["snapshot_id"]),
            "domain": "LEGAL",
        },
    )
    assert readiness.status_code == 200, readiness.text
    assert readiness.json()["requirement_count"] == 1

    queued = client.post(
        f"/processes/{ids['process_id']}/specialized-evaluations",
        json={
            "normalization_run_id": str(ids["normalization_run_id"]),
            "company_id": str(ids["company_id"]),
            "company_profile_snapshot_id": str(ids["snapshot_id"]),
            "domain": "LEGAL",
            "force": False,
        },
    )
    assert queued.status_code == 202, queued.text
    run_id = queued.json()["run"]["id"]

    worker = specialized_run_once(worker_id="api-specialized-worker")
    assert worker["processed"] == 1

    detail = client.get(f"/processes/{ids['process_id']}/specialized-evaluations/{run_id}")
    assert detail.status_code == 200
    assert detail.json()["domain"] == "LEGAL"

    results = client.get(f"/processes/{ids['process_id']}/specialized-evaluations/{run_id}/results")
    assert results.status_code == 200
    result = results.json()["items"][0]
    assert result["status"] == "COMPLIES"

    reviewed = client.post(
        (
            f"/processes/{ids['process_id']}/specialized-evaluations/{run_id}"
            f"/results/{result['id']}/review"
        ),
        json={
            "review_status": "OVERRIDDEN",
            "override_result": "UNKNOWN",
            "override_reason": "Revision juridica pendiente.",
        },
    )
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["reviewed_status"] == "UNKNOWN"


def _create_inputs() -> dict[str, UUID]:
    now = datetime.now(UTC)
    process_id = uuid4()
    system_process_id = uuid4()
    company_id = uuid4()
    snapshot_id = uuid4()
    with get_sessionmaker()() as session:
        process = Process(
            id=process_id,
            internal_reference=f"SPECAPI-{process_id.hex[:8]}",
            title="Proceso especializado API",
            contracting_entity="Entidad",
            closing_at=datetime(2026, 12, 31, tzinfo=UTC),
            status=ProcessStatus.READY_FOR_INVENTORY.value,
            source=ProcessSource.MANUAL.value,
        )
        system_process = Process(
            id=system_process_id,
            internal_reference=f"CPDOC-{company_id.hex[:8]}",
            title="Documentos de empresa",
            contracting_entity="Empresa",
            status=ProcessStatus.DRAFT.value,
            source=ProcessSource.MANUAL.value,
            is_system=True,
        )
        company = CompanyProfile(
            id=company_id,
            system_process_id=system_process_id,
            internal_reference=f"CP-{company_id.hex[:8]}",
            legal_name="Empresa Especializada API SAS",
            status=CompanyProfileStatus.READY_FOR_REVIEW.value,
            economic_activity_codes=[],
        )
        session.add_all([process, system_process, company])
        normalization_prompt = ensure_prompt_version(session, NORMALIZATION_PROMPT)
        consolidation_prompt = ensure_prompt_version(session, CONSOLIDATION_PROMPT)
        job = RequirementNormalizationJob(
            id=uuid4(),
            process_id=process_id,
            status=RequirementNormalizationStatus.COMPLETED.value,
            force=False,
            available_at=now,
            started_at=now,
            finished_at=now,
        )
        session.add(job)
        session.flush()
        run = RequirementNormalizationRun(
            id=uuid4(),
            job_id=job.id,
            process_id=process_id,
            status=RequirementNormalizationStatus.COMPLETED.value,
            provider=NormalizationProvider.FAKE.value,
            model="fake",
            reasoning_effort="none",
            prompt_version_id=normalization_prompt.id,
            consolidation_prompt_version_id=consolidation_prompt.id,
            input_manifest={"documents": []},
            input_digest="f" * 64,
            source_extraction_ids=[],
            segment_count=0,
            batch_count=0,
            candidate_count=1,
            accepted_requirement_count=1,
            rejected_candidate_count=0,
            warning_count=0,
            input_tokens=0,
            output_tokens=0,
            reasoning_tokens=0,
            provider_response_ids=[],
            started_at=now,
            finished_at=now,
        )
        normalization_run_id = run.id
        session.add(run)
        session.flush()
        job.run_id = run.id
        session.add(
            Requirement(
                id=uuid4(),
                process_id=process_id,
                normalization_run_id=run.id,
                stable_key="f" * 64,
                category=RequirementCategory.LEGAL.value,
                scope=RequirementScope.HABILITATING.value,
                modality=RequirementModality.MANDATORY.value,
                description="Debe aportar RUP vigente.",
                expected_value={},
                criticality=RequirementCriticality.HIGH.value,
                criticality_basis=RequirementBasis.EXPLICIT.value,
                subsanability=RequirementSubsanability.UNKNOWN.value,
                subsanability_basis=RequirementBasis.UNKNOWN.value,
                confidence=Decimal("0.950"),
                evidence_status=RequirementEvidenceStatus.VALIDATED.value,
                review_status=RequirementReviewStatus.PENDING.value,
                requires_human_review=True,
                is_active=True,
            )
        )
        snapshot = CompanyProfileSnapshot(
            id=snapshot_id,
            company_id=company_id,
            version=1,
            status=CompanySnapshotStatus.PUBLISHED.value,
            digest="a" * 64,
            payload={
                "rup_snapshots": [
                    {
                        "id": str(uuid4()),
                        "status": "SUPPORTED",
                        "valid_until": "2027-01-01",
                    }
                ],
                "evidence_links": [],
            },
            completeness_status="READY_FOR_REVIEW",
            published_at=now,
        )
        session.add(snapshot)
        session.commit()
    return {
        "process_id": process_id,
        "normalization_run_id": normalization_run_id,
        "company_id": company_id,
        "snapshot_id": snapshot_id,
    }
