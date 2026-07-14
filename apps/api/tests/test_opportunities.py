from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from pliegocheck_api.db import get_sessionmaker
from pliegocheck_api.models import (
    ExternalProcurementSearch,
    ExternalProcurementSearchResult,
    ExternalProcurementSource,
    OperationalAuditEvent,
    OpportunityAssessment,
    OpportunityDiscoveryRun,
    OpportunityReview,
)
from pliegocheck_api.opportunities.policy import load_policy
from pliegocheck_worker.opportunities.orchestrator import opportunity_run_once

EFFECTIVE = datetime(2026, 7, 13, 12, tzinfo=UTC)


def _company_snapshot(client: TestClient) -> tuple[str, str]:
    company = client.post(
        "/companies",
        json={
            "legal_name": "Empresa Oportunidades Sintetica SAS",
            "trade_name": "Oportunidades Sintetica",
            "tax_id": "901999001",
            "tax_id_type": "NIT",
            "country": "CO",
            "department": "Cundinamarca",
            "city": "Bogota",
            "economic_activity_codes": ["interventoria ingenieria"],
        },
    )
    assert company.status_code == 201, company.text
    company_id = company.json()["id"]
    snapshot = client.post(
        f"/companies/{company_id}/snapshots",
        json={"notes": "Fixture offline", "allow_incomplete": True},
    )
    assert snapshot.status_code == 200, snapshot.text
    snapshot_id = snapshot.json()["id"]
    published = client.post(f"/companies/{company_id}/snapshots/{snapshot_id}/publish")
    assert published.status_code == 200, published.text
    return company_id, snapshot_id


def _candidate() -> str:
    with get_sessionmaker()() as session:
        source = ExternalProcurementSource(
            id=uuid4(),
            source_system="SECOP_II",
            provider="datos_abiertos",
            name="SECOP II fixture",
            base_url="https://www.datos.gov.co",
            dataset_id="fixture-opportunities",
            human_url="https://www.datos.gov.co",
            api_url="https://www.datos.gov.co/resource/fixture.json",
            status="AVAILABLE",
            source_metadata={},
        )
        session.add(source)
        session.flush()
        search = ExternalProcurementSearch(
            id=uuid4(),
            source_id=source.id,
            query="interventoria",
            filters={},
            status="COMPLETED",
            result_count=1,
            source_row_count=1,
            page_count=1,
            limit=20,
            offset=0,
            unsupported_filters=[],
            warnings=[],
        )
        session.add(search)
        session.flush()
        raw = {"fixture": True}
        result = ExternalProcurementSearchResult(
            id=uuid4(),
            search_id=search.id,
            source_id=source.id,
            source_system="SECOP_II",
            source_dataset="fixture-opportunities",
            source_process_id="CO1.REQ.OPPORTUNITY-001",
            source_process_reference="OPP-001",
            title="Interventoria de ingenieria civil",
            entity_name="Entidad publica fixture",
            modality="Licitacion publica",
            status="Publicado",
            estimated_value=Decimal("100000000"),
            currency="COP",
            publication_date=EFFECTIVE - timedelta(days=1),
            closing_date=EFFECTIVE + timedelta(days=10),
            department="Cundinamarca",
            municipality="Bogota",
            raw_payload=raw,
            normalized_payload={
                "description": "Supervision de obras de ingenieria",
                "unspsc_codes": ["81101500"],
            },
            raw_payload_hash=sha256(b"fixture").hexdigest(),
            field_statuses={},
            warnings=[],
            source_url="https://www.datos.gov.co",
            documents_url=None,
            documents_status="DOCUMENTS_NOT_AVAILABLE",
            import_status="PENDING",
        )
        session.add(result)
        session.commit()
        return str(result.id)


def test_discovery_worker_inbox_history_review_and_deep_analysis(client: TestClient) -> None:
    company_id, snapshot_id = _company_snapshot(client)
    candidate_id = _candidate()
    request = {
        "company_profile_id": company_id,
        "company_snapshot_id": snapshot_id,
        "candidate_ids": [candidate_id],
        "effective_at": EFFECTIVE.isoformat(),
    }

    created = client.post("/opportunities/discovery-runs", json=request)
    assert created.status_code == 202, created.text
    run_id = created.json()["run"]["id"]
    reused = client.post("/opportunities/discovery-runs", json=request)
    assert reused.status_code == 202 and reused.json()["reused"] is True

    worker = opportunity_run_once("opportunity-test")
    assert worker["processed"] == 1 and worker["status"] in {"COMPLETED", "COMPLETED_WITH_WARNINGS"}
    detail = client.get(f"/opportunities/discovery-runs/{run_id}")
    assert detail.status_code == 200 and detail.json()["assessed_count"] == 1
    opportunity_id = detail.json()["candidates"][0]["id"]
    assert len(detail.json()["candidates"][0]["components"]) == 12

    inbox = client.get(
        "/opportunities", params={"company_snapshot_id": snapshot_id, "sort": "compatibility"}
    )
    assert inbox.status_code == 200 and inbox.json()["total"] == 1
    assert "compatibilidad preliminar" in inbox.json()["disclaimer"]

    review = client.post(
        f"/opportunities/{opportunity_id}/review",
        json={"action": "SHORTLIST", "reason": "Revisar fixture"},
    )
    assert review.status_code == 200 and review.json()["action"] == "SHORTLIST"
    filtered = client.get("/opportunities", params={"review_action": "SHORTLIST"})
    assert filtered.status_code == 200 and filtered.json()["total"] == 1

    deep = client.post(f"/opportunities/{opportunity_id}/request-deep-analysis")
    assert deep.status_code == 200
    assert "document_pipeline" in deep.json()["steps_blocked"]
    assert deep.json()["missing_inputs"]

    imported = client.post(f"/opportunities/{opportunity_id}/import")
    duplicate = client.post(f"/opportunities/{opportunity_id}/import")
    assert imported.status_code == duplicate.status_code == 200
    assert imported.json()["process_id"] == duplicate.json()["process_id"]
    assert duplicate.json()["status"] == "SKIPPED_DUPLICATE"

    reassessed = client.post(f"/opportunities/{opportunity_id}/assess")
    assert reassessed.status_code == 200 and reassessed.json()["id"] != opportunity_id
    forced = client.post("/opportunities/discovery-runs", json={**request, "force": True})
    assert forced.status_code == 202 and forced.json()["run"]["id"] != run_id

    with get_sessionmaker()() as session:
        assert session.scalar(select(func.count()).select_from(OpportunityDiscoveryRun)) == 2
        assert session.scalar(select(func.count()).select_from(OpportunityAssessment)) == 2
        assert session.scalar(select(func.count()).select_from(OpportunityReview)) == 1
        events = set(session.scalars(select(OperationalAuditEvent.event_type)))
        assert {
            "OPPORTUNITY_DISCOVERY_REQUESTED",
            "OPPORTUNITY_DISCOVERY_COMPLETED",
            "OPPORTUNITY_REASSESSED",
            "OPPORTUNITY_SHORTLISTED",
            "OPPORTUNITY_DEEP_ANALYSIS_REQUESTED",
            "OPPORTUNITY_IMPORTED",
        } <= events


def test_snapshot_must_exist_and_be_published(client: TestClient) -> None:
    company_id, _ = _company_snapshot(client)
    response = client.post(
        "/opportunities/discovery-runs",
        json={
            "company_profile_id": company_id,
            "company_snapshot_id": str(uuid4()),
            "candidate_ids": [str(uuid4())],
        },
    )
    assert response.status_code == 422
    assert "COMPANY_SNAPSHOT_REQUIRED" in response.text


def test_policy_hash_and_invalid_policy(tmp_path: Path) -> None:
    policy = load_policy()
    assert len(policy.policy_hash) == 64
    invalid = tmp_path / "policy.json"
    invalid.write_text('{"version":"bad"}', encoding="utf-8")
    try:
        load_policy(invalid)
    except ValueError as exc:
        assert "invalid opportunity policy keys" in str(exc)
    else:
        raise AssertionError("invalid policy accepted")
