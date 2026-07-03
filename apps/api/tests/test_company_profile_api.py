"""Pruebas de perfiles de empresa, evidencias y snapshots."""

from typing import Any, cast

from fastapi.testclient import TestClient

from pliegocheck_api.config import get_settings
from pliegocheck_api.db import get_engine, get_sessionmaker
from pliegocheck_worker.runner import run_once


def _create_company(client: TestClient) -> dict[str, Any]:
    response = client.post(
        "/companies",
        json={
            "legal_name": "Empresa Sintetica SAS",
            "trade_name": "Sintetica",
            "tax_id": "900 123 456",
            "tax_id_type": "NIT",
            "country": "CO",
            "department": "Cundinamarca",
            "city": "Bogota",
            "primary_email": "licitaciones@example.test",
        },
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json())


def test_company_profile_complete_flow(client: TestClient) -> None:
    company = _create_company(client)
    company_id = company["id"]
    assert company["internal_reference"].startswith("CP-")
    assert company["tax_id"] == "900123456"
    assert company["tax_id_masked"].endswith("3456")

    legal = client.post(
        f"/companies/{company_id}/legal-registrations",
        json={
            "registration_type": "RUT",
            "registration_number": "RUT-001",
            "issuing_authority": "DIAN",
            "issued_at": "2026-01-01",
        },
    ).json()
    rup = client.post(
        f"/companies/{company_id}/rup",
        json={
            "registration_number": "RUP-001",
            "issued_at": "2026-01-01",
            "valid_until": "2026-12-31",
            "renewal_year": 2026,
            "financial_capacity": "1000.00",
        },
    ).json()
    unspsc = client.post(
        f"/companies/{company_id}/unspsc",
        json={"code": "81101500", "description": "Ingenieria civil", "source": "RUP"},
    ).json()
    period = client.post(
        f"/companies/{company_id}/financial-periods",
        json={
            "period_start": "2025-01-01",
            "period_end": "2025-12-31",
            "currency": "COP",
            "source_type": "FINANCIAL_STATEMENT",
        },
    ).json()
    metric = client.post(
        f"/companies/{company_id}/financial-periods/{period['id']}/metrics",
        json={
            "metric_type": "LIQUIDITY_RATIO",
            "value": "1.75",
            "unit": "ratio",
            "source_value": "1.75",
        },
    ).json()
    experience = client.post(
        f"/companies/{company_id}/experience",
        json={
            "contracting_party": "Entidad Ficticia",
            "contract_title": "Contrato sintetico de interventoria",
            "execution_status": "COMPLETED",
            "total_contract_value": "1000000",
            "company_participation_percentage": "50",
            "consortium_name": "UT Sintetica",
            "consortium_members": ["Empresa Sintetica SAS", "Aliado Ficticio SAS"],
            "unspsc_codes": ["81101500"],
        },
    ).json()
    assert experience["company_attributable_value"] == "500000.00"
    person = client.post(
        f"/companies/{company_id}/people",
        json={
            "full_name": "Persona Sintetica",
            "identification_type": "CC",
            "identification_number": "1234567890",
            "relationship_type": "EMPLOYEE",
            "availability_status": "AVAILABLE",
        },
    ).json()
    assert person["identification_masked"] == "******7890"
    credential = client.post(
        f"/companies/{company_id}/people/{person['id']}/credentials",
        json={
            "credential_type": "PROFESSIONAL_LICENSE",
            "name": "Matricula profesional sintetica",
            "issuer": "Consejo ficticio",
            "issued_at": "2020-01-01",
        },
    ).json()
    certification = client.post(
        f"/companies/{company_id}/certifications",
        json={
            "certification_type": "ISO",
            "name": "ISO 9001 sintetica",
            "issuer": "Certificador ficticio",
            "issued_at": "2025-01-01",
            "expires_at": "2027-01-01",
        },
    ).json()
    capability = client.post(
        f"/companies/{company_id}/capabilities",
        json={
            "category": "GEOGRAPHIC_COVERAGE",
            "name": "Cobertura nacional declarada",
            "value": "Nacional",
            "unit": "territorio",
        },
    ).json()

    upload = client.post(
        f"/companies/{company_id}/evidence-documents",
        params={"evidence_type": "RUP", "title": "Soporte sintetico RUP"},
        files={
            "files": (
                "soporte.txt",
                b"Liquidez 1.75\nRUP-001\nContrato sintetico de interventoria\n",
                "text/plain",
            )
        },
    )
    assert upload.status_code == 201, upload.text
    evidence = upload.json()["results"][0]["document"]
    assert evidence["processing_status"] == "QUEUED"
    assert "storage_key" not in str(upload.json())

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()
    worker_result = run_once("company-api-test")
    assert worker_result["processed"] == 1
    assert worker_result["job_status"] == "COMPLETED"

    refreshed_evidence = client.get(
        f"/companies/{company_id}/evidence-documents/{evidence['id']}"
    ).json()
    assert refreshed_evidence["processing_status"] in {"COMPLETED", "COMPLETED_WITH_WARNINGS"}

    process_document_id = refreshed_evidence["process_document_id"]
    extraction = client.get(
        f"/processes/{company['id']}/documents/{process_document_id}/extraction"
    )
    assert extraction.status_code == 404

    # The company route validates ownership when linking extraction evidence.
    from sqlalchemy import select

    from pliegocheck_api.db import get_sessionmaker as current_sessionmaker
    from pliegocheck_api.models import (
        CompanyEvidenceDocument,
        DocumentExtraction,
        ExtractedSegment,
    )

    with current_sessionmaker()() as session:
        evidence_row = session.get(CompanyEvidenceDocument, refreshed_evidence["id"])
        assert evidence_row is not None
        extraction_row = session.scalar(
            select(DocumentExtraction).where(
                DocumentExtraction.document_id == evidence_row.process_document_id
            )
        )
        assert extraction_row is not None
        segment = session.scalar(
            select(ExtractedSegment).where(ExtractedSegment.extraction_id == extraction_row.id)
        )
        assert segment is not None
        extraction_id = str(extraction_row.id)
        segment_id = str(segment.id)

    subjects = [
        ("LEGAL_REGISTRATION", legal["id"], "RUP-001"),
        ("RUP_SNAPSHOT", rup["id"], "RUP-001"),
        ("UNSPSC_CODE", unspsc["id"], None),
        ("FINANCIAL_PERIOD", period["id"], None),
        ("FINANCIAL_METRIC", metric["id"], "Liquidez 1.75"),
        ("EXPERIENCE_RECORD", experience["id"], "Contrato sintetico de interventoria"),
        ("PERSON", person["id"], None),
        ("PERSON_CREDENTIAL", credential["id"], None),
        ("COMPANY_CERTIFICATION", certification["id"], None),
        ("COMPANY_CAPABILITY", capability["id"], None),
    ]
    for subject_type, subject_id, quote in subjects:
        payload = {
            "document_id": evidence["id"],
            "subject_type": subject_type,
            "subject_id": subject_id,
            "evidence_role": "PRIMARY",
            "review_status": "SUPPORTED",
        }
        if quote:
            payload.update(
                {"extraction_id": extraction_id, "segment_id": segment_id, "quoted_text": quote}
            )
        link = client.post(f"/companies/{company_id}/evidence-links", json=payload)
        assert link.status_code == 200, link.text
        assert link.json()["validation_status"] in {"DOCUMENT_ONLY", "VALID_SEGMENT"}

    completeness = client.get(f"/companies/{company_id}/completeness").json()
    assert completeness["ready_for_review"] is True
    assert completeness["unsupported_record_count"] == 0
    assert "GO" not in str(completeness)

    snapshot = client.post(
        f"/companies/{company_id}/snapshots",
        json={"notes": "Snapshot sintetico", "allow_incomplete": False},
    )
    assert snapshot.status_code == 200, snapshot.text
    snapshot_payload = snapshot.json()
    assert len(snapshot_payload["digest"]) == 64
    published = client.post(
        f"/companies/{company_id}/snapshots/{snapshot_payload['id']}/publish"
    ).json()
    assert published["status"] == "PUBLISHED"

    client.patch(f"/companies/{company_id}", json={"trade_name": "Mutable despues"})
    old_snapshot = client.get(f"/companies/{company_id}/snapshots/{snapshot_payload['id']}").json()
    assert old_snapshot["payload"]["company"]["trade_name"] == "Sintetica"


def test_company_duplicate_tax_id_is_rejected(client: TestClient) -> None:
    _create_company(client)
    response = client.post(
        "/companies",
        json={"legal_name": "Duplicada SAS", "tax_id": "900-123-456", "tax_id_type": "NIT"},
    )
    assert response.status_code == 409
    assert response.json()["code"] == "DUPLICATE_TAX_ID"
