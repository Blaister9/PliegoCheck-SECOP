# mypy: ignore-errors
"""Pruebas API del motor deterministico de decision."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from pliegocheck_api.db import get_sessionmaker
from pliegocheck_api.models import (
    DecisionRun,
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
from pliegocheck_worker.decision.orchestrator import decision_run_once
from pliegocheck_worker.financial.orchestrator import financial_run_once


def _create_process(client: TestClient, title: str = "Proceso decision") -> dict[str, Any]:
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


def _add_requirement(
    session: Any,
    process_id: UUID,
    run_id: UUID,
    *,
    category: str,
    description: str,
    stable_key: str,
    modality: str = RequirementModality.MANDATORY.value,
    criticality: str = RequirementCriticality.HIGH.value,
    expected_value: dict[str, Any] | None = None,
) -> UUID:
    requirement = Requirement(
        id=uuid4(),
        process_id=process_id,
        normalization_run_id=run_id,
        stable_key=stable_key,
        category=category,
        scope=RequirementScope.HABILITATING.value,
        modality=modality,
        description=description,
        condition_text=None,
        expected_value=expected_value,
        criticality=criticality,
        criticality_basis=RequirementBasis.EXPLICIT.value,
        subsanability=RequirementSubsanability.UNKNOWN.value,
        subsanability_basis=RequirementBasis.UNKNOWN.value,
        confidence=Decimal("0.950"),
        evidence_status=RequirementEvidenceStatus.VALIDATED.value,
        review_status=RequirementReviewStatus.PENDING.value,
        requires_human_review=False,
        is_active=True,
    )
    session.add(requirement)
    return requirement.id


def _create_normalization_with_requirements(process_id: UUID) -> UUID:
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
            input_digest="c" * 64,
            source_extraction_ids=[],
            segment_count=0,
            batch_count=0,
            candidate_count=2,
            accepted_requirement_count=2,
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
        _add_requirement(
            session,
            process_id,
            run.id,
            category=RequirementCategory.FINANCIAL.value,
            description="El proponente debe acreditar indice de liquidez minimo de 1.2.",
            stable_key="d" * 64,
            expected_value={"value": "1.2", "unit": "ratio", "raw_text": "minimo 1.2"},
        )
        _add_requirement(
            session,
            process_id,
            run.id,
            category=RequirementCategory.LEGAL.value,
            description="El proponente debe aportar certificado de existencia y representacion.",
            stable_key="e" * 64,
        )
        session.commit()
        return run.id


def _create_company_snapshot(client: TestClient) -> tuple[dict[str, Any], dict[str, Any]]:
    company = client.post(
        "/companies",
        json={"legal_name": "Empresa Decision SAS", "tax_id": "901234568", "tax_id_type": "NIT"},
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
        json={"allow_incomplete": True, "notes": "Snapshot decision sintetico"},
    ).json()
    published = client.post(f"/companies/{company['id']}/snapshots/{snapshot['id']}/publish").json()
    assert published["status"] == "PUBLISHED"
    return cast(dict[str, Any], company), cast(dict[str, Any], published)


def _prepare_financial_run(
    client: TestClient,
    process: dict[str, Any],
    normalization_run_id: UUID,
    company: dict[str, Any],
    snapshot: dict[str, Any],
) -> str:
    queued = client.post(
        f"/processes/{process['id']}/financial-evaluations",
        json={
            "normalization_run_id": str(normalization_run_id),
            "company_id": company["id"],
            "company_profile_snapshot_id": snapshot["id"],
            "force": False,
        },
    )
    assert queued.status_code == 202, queued.text
    worker = financial_run_once(worker_id="decision-test-financial")
    assert worker["processed"] == 1, worker
    assert worker["run_status"] in {"COMPLETED", "COMPLETED_WITH_WARNINGS"}
    return cast(str, worker["run_id"])


def _full_pipeline(client: TestClient) -> dict[str, Any]:
    process = _create_process(client)
    normalization_run_id = _create_normalization_with_requirements(UUID(process["id"]))
    company, snapshot = _create_company_snapshot(client)
    financial_run_id = _prepare_financial_run(
        client, process, normalization_run_id, company, snapshot
    )
    return {
        "process": process,
        "normalization_run_id": str(normalization_run_id),
        "company": company,
        "snapshot": snapshot,
        "financial_run_id": financial_run_id,
    }


def test_decision_readiness_reports_missing_adapters(client: TestClient) -> None:
    setup = _full_pipeline(client)
    response = client.get(
        f"/processes/{setup['process']['id']}/decision-readiness",
        params={
            "normalization_run_id": setup["normalization_run_id"],
            "company_profile_snapshot_id": setup["snapshot"]["id"],
            "financial_evaluation_run_id": setup["financial_run_id"],
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["inputs_valid"] is True
    assert payload["available_adapters"] == ["FINANCIAL"]
    assert payload["not_evaluated_mandatory_count"] == 1
    assert payload["go_blocked_by_coverage"] is True
    assert payload["max_possible_outcome"] == "PENDIENTE_INFORMACION"
    assert "ADAPTER_NOT_AVAILABLE:LEGAL" in payload["warnings"]
    assert payload["policy"]["semantic_version"] == "1.0.0"


def test_decision_full_flow_pendiente_informacion(client: TestClient) -> None:
    setup = _full_pipeline(client)
    process_id = setup["process"]["id"]

    queued = client.post(
        f"/processes/{process_id}/decisions",
        json={
            "normalization_run_id": setup["normalization_run_id"],
            "company_id": setup["company"]["id"],
            "company_profile_snapshot_id": setup["snapshot"]["id"],
            "financial_evaluation_run_id": setup["financial_run_id"],
            "force": False,
        },
    )
    assert queued.status_code == 202, queued.text
    run_id = queued.json()["run"]["id"]
    assert queued.json()["run"]["status"] == "PENDING"

    worker = decision_run_once(worker_id="decision-test-worker")
    assert worker["processed"] == 1, worker
    assert worker["engine_outcome"] == "PENDIENTE_INFORMACION"

    detail = client.get(f"/processes/{process_id}/decisions/{run_id}")
    assert detail.status_code == 200, detail.text
    payload = detail.json()
    assert payload["engine_outcome"] == "PENDIENTE_INFORMACION"
    assert payload["effective_outcome"] == "PENDIENTE_INFORMACION"
    assert "MANDATORY_REQUIREMENT_NOT_EVALUATED" in payload["reason_codes"]
    assert payload["policy"]["semantic_version"] == "1.0.0"
    assert payload["coverage"]["mandatory_applicable_total"] == 2
    assert payload["coverage"]["not_evaluated_total"] == 1
    assert len(payload["findings"]) == 2
    outcomes = {finding["outcome"] for finding in payload["findings"]}
    assert outcomes == {"COMPLIES", "NOT_EVALUATED"}
    triggered = [rule for rule in payload["rule_evaluations"] if rule["status"] == "TRIGGERED"]
    assert any(rule["rule_code"] == "MANDATORY_REQUIREMENT_NOT_EVALUATED" for rule in triggered)
    assert payload["actions"], "deben existir acciones deterministicas"
    action_types = {action["action_type"] for action in payload["actions"]}
    assert "COMPLETE_MANDATORY_EVALUATION" in action_types
    assert "ADAPTER_NOT_AVAILABLE:LEGAL" in payload["warnings"]
    assert payload["engine_outcome"] != "GO"
    # sin rutas fisicas ni SQL en la respuesta
    text = detail.text.lower()
    assert "c:\\" not in text
    assert "select " not in text


def test_decision_idempotency_and_force(client: TestClient) -> None:
    setup = _full_pipeline(client)
    process_id = setup["process"]["id"]
    body = {
        "normalization_run_id": setup["normalization_run_id"],
        "company_id": setup["company"]["id"],
        "company_profile_snapshot_id": setup["snapshot"]["id"],
        "financial_evaluation_run_id": setup["financial_run_id"],
        "force": False,
    }
    first = client.post(f"/processes/{process_id}/decisions", json=body)
    assert first.status_code == 202
    first_run = first.json()["run"]["id"]
    decision_run_once(worker_id="decision-idem")

    second = client.post(f"/processes/{process_id}/decisions", json=body)
    assert second.status_code == 202
    assert second.json()["run"]["id"] == first_run
    assert second.json()["reused_existing_run"] is True

    forced = client.post(f"/processes/{process_id}/decisions", json={**body, "force": True})
    assert forced.status_code == 202
    forced_run = forced.json()["run"]["id"]
    assert forced_run != first_run
    decision_run_once(worker_id="decision-force")

    listing = client.get(f"/processes/{process_id}/decisions")
    assert listing.status_code == 200
    assert listing.json()["total"] == 2

    with get_sessionmaker()() as session:
        runs = session.scalars(select(DecisionRun)).all()
        digests = {run.input_digest for run in runs}
        assert len(digests) == 1, "mismos inputs, mismo digest"
        outcomes = {run.engine_outcome for run in runs}
        assert outcomes == {"PENDIENTE_INFORMACION"}, "mismos inputs, misma salida"


def test_decision_review_override_preserves_engine_outcome(client: TestClient) -> None:
    setup = _full_pipeline(client)
    process_id = setup["process"]["id"]
    queued = client.post(
        f"/processes/{process_id}/decisions",
        json={
            "normalization_run_id": setup["normalization_run_id"],
            "company_id": setup["company"]["id"],
            "company_profile_snapshot_id": setup["snapshot"]["id"],
            "financial_evaluation_run_id": setup["financial_run_id"],
            "force": False,
        },
    )
    run_id = queued.json()["run"]["id"]
    decision_run_once(worker_id="decision-review")

    missing_reason = client.post(
        f"/processes/{process_id}/decisions/{run_id}/review",
        json={"action": "OVERRIDE", "reviewed_outcome": "NO_GO", "reason": ""},
    )
    assert missing_reason.status_code == 422

    reviewed = client.post(
        f"/processes/{process_id}/decisions/{run_id}/review",
        json={
            "action": "OVERRIDE",
            "reviewed_outcome": "NO_GO",
            "reason": "El analista confirma un incumplimiento juridico bloqueante.",
        },
    )
    assert reviewed.status_code == 200, reviewed.text
    payload = reviewed.json()
    assert payload["run"]["engine_outcome"] == "PENDIENTE_INFORMACION"
    assert payload["run"]["reviewed_outcome"] == "NO_GO"
    assert payload["run"]["effective_outcome"] == "NO_GO"
    assert payload["review"]["original_outcome"] == "PENDIENTE_INFORMACION"

    detail = client.get(f"/processes/{process_id}/decisions/{run_id}").json()
    assert detail["engine_outcome"] == "PENDIENTE_INFORMACION"
    assert detail["reviews"][0]["action"] == "OVERRIDE"

    # actualizar una accion
    if detail["actions"]:
        action_id = detail["actions"][0]["id"]
        patched = client.patch(
            f"/processes/{process_id}/decisions/{run_id}/actions/{action_id}",
            json={"status": "ACKNOWLEDGED", "note": "En gestion."},
        )
        assert patched.status_code == 200
        assert patched.json()["status"] == "ACKNOWLEDGED"


def test_decision_rejects_mismatched_inputs(client: TestClient) -> None:
    setup = _full_pipeline(client)
    other_process = _create_process(client, title="Proceso ajeno")
    response = client.post(
        f"/processes/{other_process['id']}/decisions",
        json={
            "normalization_run_id": setup["normalization_run_id"],
            "company_id": setup["company"]["id"],
            "company_profile_snapshot_id": setup["snapshot"]["id"],
            "financial_evaluation_run_id": setup["financial_run_id"],
            "force": False,
        },
    )
    assert response.status_code == 409
    assert response.json()["code"] == "DECISION_INPUT_MISMATCH"


def test_decision_requires_published_snapshot(client: TestClient) -> None:
    setup = _full_pipeline(client)
    process_id = setup["process"]["id"]
    draft = client.post(
        f"/companies/{setup['company']['id']}/snapshots",
        json={"allow_incomplete": True, "notes": "draft"},
    ).json()
    response = client.post(
        f"/processes/{process_id}/decisions",
        json={
            "normalization_run_id": setup["normalization_run_id"],
            "company_id": setup["company"]["id"],
            "company_profile_snapshot_id": draft["id"],
            "financial_evaluation_run_id": setup["financial_run_id"],
            "force": False,
        },
    )
    assert response.status_code == 409
    assert response.json()["code"] == "DECISION_COMPANY_SNAPSHOT_NOT_PUBLISHED"


def test_decision_retry_only_for_failed(client: TestClient) -> None:
    setup = _full_pipeline(client)
    process_id = setup["process"]["id"]
    queued = client.post(
        f"/processes/{process_id}/decisions",
        json={
            "normalization_run_id": setup["normalization_run_id"],
            "company_id": setup["company"]["id"],
            "company_profile_snapshot_id": setup["snapshot"]["id"],
            "financial_evaluation_run_id": setup["financial_run_id"],
            "force": False,
        },
    )
    run_id = queued.json()["run"]["id"]
    decision_run_once(worker_id="decision-retry")
    response = client.post(f"/processes/{process_id}/decisions/{run_id}/retry")
    assert response.status_code == 409
    assert response.json()["code"] == "DECISION_ALREADY_COMPLETED"


def test_decision_not_found_is_sanitized(client: TestClient) -> None:
    process = _create_process(client, title="Proceso sin decisiones")
    response = client.get(f"/processes/{process['id']}/decisions/{uuid4()}")
    assert response.status_code == 404
    payload = response.json()
    assert payload["code"] == "DECISION_NOT_FOUND"
    assert set(payload.keys()) == {"code", "message", "details"}


def test_health_endpoints_still_work(client: TestClient) -> None:
    assert client.get("/health/live").status_code == 200
    assert client.get("/health/ready").status_code == 200
    assert client.get("/openapi.json").status_code == 200
