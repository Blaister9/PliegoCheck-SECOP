"""Pruebas API de normalizacion de requisitos con proveedor falso."""

from typing import Any, cast

from fastapi.testclient import TestClient

from pliegocheck_api.config import get_settings
from pliegocheck_api.db import get_engine, get_sessionmaker
from pliegocheck_worker.normalization.orchestrator import normalization_run_once
from pliegocheck_worker.runner import run_once


def test_normalization_api_flow_with_fake_provider(client: TestClient) -> None:
    process = _create_process(client)
    upload = client.post(
        f"/processes/{process['id']}/documents",
        files={
            "files": (
                "pliego.txt",
                (
                    b"El proponente debe acreditar indice de liquidez minimo de 1.2.\n"
                    b"El proponente debe presentar experiencia minima de dos contratos.\n"
                ),
                "text/plain",
            )
        },
    )
    assert upload.status_code == 201, upload.text
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()
    assert run_once("api-normalization-extraction")["job_status"] == "COMPLETED"

    queued = client.post(
        f"/processes/{process['id']}/requirements/normalizations",
        json={"force": False, "document_ids": None},
    )
    assert queued.status_code == 202, queued.text
    queued_payload = queued.json()
    assert queued_payload["run"]["status"] == "PENDING"
    assert queued_payload["run"]["provider"] == "fake"
    assert queued_payload["run"]["segment_count"] == 1

    worker = normalization_run_once(worker_id="api-normalization-worker", provider_name="fake")
    assert worker["processed"] == 1
    assert worker["run_status"] in {"COMPLETED", "COMPLETED_WITH_WARNINGS"}
    assert worker["accepted_requirement_count"] >= 1

    runs = client.get(f"/processes/{process['id']}/requirements/normalizations")
    assert runs.status_code == 200
    run_id = runs.json()["items"][0]["id"]
    detail = client.get(f"/processes/{process['id']}/requirements/normalizations/{run_id}")
    assert detail.status_code == 200
    assert detail.json()["batches"][0]["status"] == "COMPLETED"
    assert "system_content" not in str(detail.json())

    requirements = client.get(f"/processes/{process['id']}/requirements")
    assert requirements.status_code == 200
    payload = requirements.json()
    assert payload["total"] >= 1
    first = payload["items"][0]
    assert first["review_status"] == "PENDING"
    assert first["requires_human_review"] is True
    assert first["evidence_status"] == "VALIDATED"
    assert "COMPLIES" not in str(payload)

    requirement = client.get(f"/processes/{process['id']}/requirements/{first['id']}")
    assert requirement.status_code == 200
    requirement_payload = requirement.json()
    assert requirement_payload["evidence"][0]["validation_status"] == "VALID"
    assert "indice de liquidez" in requirement_payload["evidence"][0]["quoted_text"]


def test_normalization_disabled_is_explicit(client: TestClient, monkeypatch: Any) -> None:
    monkeypatch.setenv("PLIEGOCHECK_ALLOW_FAKE_NORMALIZATION_PROVIDER", "false")
    get_settings.cache_clear()
    process = _create_process(client, title="Proceso sin IA")
    response = client.post(
        f"/processes/{process['id']}/requirements/normalizations",
        json={"force": False, "document_ids": None},
    )
    assert response.status_code == 409
    assert response.json()["code"] == "NORMALIZATION_DISABLED"
    monkeypatch.setenv("PLIEGOCHECK_ALLOW_FAKE_NORMALIZATION_PROVIDER", "true")
    get_settings.cache_clear()


def _create_process(client: TestClient, title: str = "Proceso normalizacion") -> dict[str, Any]:
    response = client.post(
        "/processes",
        json={
            "title": title,
            "contracting_entity": "Entidad de prueba",
        },
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json())
