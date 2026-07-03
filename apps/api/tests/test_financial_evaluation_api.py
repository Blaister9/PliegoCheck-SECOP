# mypy: ignore-errors
"""Pruebas API de evaluacion financiera inicial."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from pliegocheck_api.db import get_sessionmaker
from pliegocheck_api.models import (
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
    NormalizationProvider,
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
from pliegocheck_worker.financial.orchestrator import financial_run_once


def test_financial_evaluation_api_flow(client: TestClient) -> None:
    process = _create_process(client)
    run_id = _create_completed_financial_requirement(UUID(process["id"]))
    company, snapshot = _create_company_snapshot(client)

    queued = client.post(
        f"/processes/{process['id']}/financial-evaluations",
        json={
            "normalization_run_id": str(run_id),
            "company_id": company["id"],
            "company_profile_snapshot_id": snapshot["id"],
            "force": False,
        },
    )
    assert queued.status_code == 202, queued.text
    queued_payload = queued.json()
    assert queued_payload["run"]["status"] == "PENDING"

    worker = financial_run_once(worker_id="api-financial-worker")
    assert worker["processed"] == 1
    assert worker["run_status"] in {"COMPLETED", "COMPLETED_WITH_WARNINGS"}

    evaluations = client.get(f"/processes/{process['id']}/financial-evaluations")
    assert evaluations.status_code == 200
    evaluation_id = evaluations.json()["items"][0]["id"]
    detail = client.get(f"/processes/{process['id']}/financial-evaluations/{evaluation_id}")
    assert detail.status_code == 200
    assert detail.json()["requirement_count"] == 1
    assert "GO" not in str(detail.json())

    results = client.get(
        f"/processes/{process['id']}/financial-evaluations/{evaluation_id}/results"
    )
    assert results.status_code == 200
    result = results.json()["items"][0]
    assert result["status"] == "COMPLIES"
    assert result["actual_value"] == "1.75000000"
    assert result["requires_human_review"] is True

    reviewed = client.post(
        (
            f"/processes/{process['id']}/financial-evaluations/{evaluation_id}"
            f"/results/{result['id']}/review"
        ),
        json={
            "review_status": "OVERRIDDEN",
            "override_result": "DOES_NOT_COMPLY",
            "override_reason": "La evidencia debe ser revisada por analista financiero.",
        },
    )
    assert reviewed.status_code == 200, reviewed.text
    reviewed_payload = reviewed.json()
    assert reviewed_payload["status"] == "COMPLIES"
    assert reviewed_payload["reviewed_status"] == "DOES_NOT_COMPLY"
    assert reviewed_payload["reviews"][0]["original_status"] == "COMPLIES"


def test_financial_evaluation_requires_published_snapshot(client: TestClient) -> None:
    process = _create_process(client, title="Proceso snapshot no publicado")
    run_id = _create_completed_financial_requirement(UUID(process["id"]))
    company = client.post("/companies", json={"legal_name": "Sin Snapshot SAS"}).json()
    draft = client.post(
        f"/companies/{company['id']}/snapshots",
        json={"allow_incomplete": True, "notes": "draft"},
    ).json()

    response = client.post(
        f"/processes/{process['id']}/financial-evaluations",
        json={
            "normalization_run_id": str(run_id),
            "company_id": company["id"],
            "company_profile_snapshot_id": draft["id"],
            "force": False,
        },
    )

    assert response.status_code == 409
    assert response.json()["code"] == "COMPANY_SNAPSHOT_NOT_PUBLISHED"


def _create_process(client: TestClient, title: str = "Proceso financiero") -> dict[str, Any]:
    response = client.post(
        "/processes",
        json={
            "title": title,
            "contracting_entity": "Entidad de prueba",
            "closing_at": "2026-12-31T23:59:00Z",
        },
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json())


def _create_completed_financial_requirement(process_id: UUID) -> UUID:
    now = datetime.now(UTC)
    with get_sessionmaker()() as session:
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
            input_manifest={"documents": [], "warnings": []},
            input_digest="a" * 64,
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
        session.add(run)
        session.flush()
        job.run_id = run.id
        session.add(
            Requirement(
                id=uuid4(),
                process_id=process_id,
                normalization_run_id=run.id,
                stable_key="b" * 64,
                category=RequirementCategory.FINANCIAL.value,
                scope=RequirementScope.HABILITATING.value,
                modality=RequirementModality.MANDATORY.value,
                description="El proponente debe acreditar indice de liquidez minimo de 1.2.",
                condition_text=None,
                expected_value={"value": "1.2", "unit": "ratio", "raw_text": "minimo 1.2"},
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
        session.commit()
        return run.id


def _create_company_snapshot(client: TestClient) -> tuple[dict[str, Any], dict[str, Any]]:
    company = client.post(
        "/companies",
        json={"legal_name": "Empresa Financiera SAS", "tax_id": "901234567", "tax_id_type": "NIT"},
    ).json()
    period = client.post(
        f"/companies/{company['id']}/financial-periods",
        json={
            "period_start": "2025-01-01",
            "period_end": "2025-12-31",
            "currency": "COP",
            "source_type": "FINANCIAL_STATEMENT",
            "status": "SUPPORTED",
        },
    ).json()
    metric = client.post(
        f"/companies/{company['id']}/financial-periods/{period['id']}/metrics",
        json={
            "metric_type": "LIQUIDITY_RATIO",
            "value": "1.75",
            "unit": "ratio",
            "source_value": "1.75",
            "status": "SUPPORTED",
        },
    )
    assert metric.status_code == 200, metric.text
    snapshot = client.post(
        f"/companies/{company['id']}/snapshots",
        json={"allow_incomplete": True, "notes": "Snapshot financiero sintetico"},
    ).json()
    published = client.post(f"/companies/{company['id']}/snapshots/{snapshot['id']}/publish").json()
    assert published["status"] == "PUBLISHED"
    with get_sessionmaker()() as session:
        requirement = session.scalar(select(Requirement))
        assert requirement is not None
    return cast(dict[str, Any], company), cast(dict[str, Any], published)
