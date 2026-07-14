"""Pruebas offline del conector SECOP y su flujo persistente."""

import json
from collections.abc import Generator
from http import HTTPStatus
from pathlib import Path
from typing import Any, cast

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from pliegocheck_api.auth import create_user
from pliegocheck_api.config import get_settings
from pliegocheck_api.db import get_sessionmaker
from pliegocheck_api.external_procurement.datos_abiertos import (
    DatosAbiertosClient,
    build_query_params,
)
from pliegocheck_api.external_procurement.errors import ExternalProviderError
from pliegocheck_api.external_procurement.providers import get_source_definition
from pliegocheck_api.external_procurement.secop_mapper import map_secop_process
from pliegocheck_api.models import (
    DecisionJob,
    ExternalProcurementProcessLink,
    ExternalProcurementSearchResult,
    Process,
)
from pliegocheck_schemas import (
    AuthRoleName,
    ExternalProcurementErrorCode,
    ExternalProcurementSearchRequest,
    ExternalProcurementSourceSystem,
)

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "evals/secop-connector/fixtures/secop_ii_processes.json"


@pytest.fixture(autouse=True)
def clear_secop_state() -> Generator[None, None, None]:
    DatosAbiertosClient._requests.clear()
    DatosAbiertosClient._cache.clear()
    yield
    get_settings.cache_clear()


def _rows() -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], json.loads(FIXTURE.read_text(encoding="utf-8")))


def _enable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLIEGOCHECK_SECOP_ENABLED", "true")
    monkeypatch.setenv("PLIEGOCHECK_SECOP_CACHE_TTL_MINUTES", "0")
    get_settings.cache_clear()


class FixtureClient:
    def __init__(self, _settings: object) -> None:
        pass

    def search(
        self, definition: object, request: ExternalProcurementSearchRequest
    ) -> tuple[list[dict[str, Any]], list[str]]:
        _ = definition
        rows = _rows()[request.offset : request.offset + request.limit]
        unsupported = [
            name
            for name in ("closing_from", "closing_to")
            if request.source_system is ExternalProcurementSourceSystem.SECOP_I
            and getattr(request, name) is not None
        ]
        return rows, unsupported

    def close(self) -> None:
        pass


class FailingClient(FixtureClient):
    def search(
        self, definition: object, request: ExternalProcurementSearchRequest
    ) -> tuple[list[dict[str, Any]], list[str]]:
        _ = (definition, request)
        raise ExternalProviderError(
            ExternalProcurementErrorCode.SOURCE_TIMEOUT,
            "La fuente publica no respondio dentro del tiempo configurado.",
        )


class DuplicateFixtureClient(FixtureClient):
    def search(
        self, definition: object, request: ExternalProcurementSearchRequest
    ) -> tuple[list[dict[str, Any]], list[str]]:
        _ = (definition, request)
        row = _rows()[0]
        return [row, dict(row)], []


def test_mapper_normalizes_fixture_and_omits_unnecessary_data() -> None:
    row = {**_rows()[0], "identificacion_del_contratista": "SHOULD-NOT-BE-STORED"}
    normalized, safe = map_secop_process(
        row, get_source_definition(ExternalProcurementSourceSystem.SECOP_II)
    )
    assert normalized.source_process_id == "CO1.REQ.FIXTURE-001"
    assert normalized.estimated_value == 125_000_000
    assert normalized.currency is None
    assert any(item.code == "UNKNOWN_CURRENCY" for item in normalized.warnings)
    assert normalized.publication_date is not None
    assert normalized.source_url and normalized.source_url.startswith("https://")
    assert "identificacion_del_contratista" not in safe


def test_missing_field_produces_warning() -> None:
    row = dict(_rows()[0])
    row.pop("fecha_de_recepcion_de")
    normalized, _ = map_secop_process(
        row, get_source_definition(ExternalProcurementSourceSystem.SECOP_II)
    )
    assert normalized.closing_date is None
    assert any(item.field == "closing_date" for item in normalized.warnings)


def test_mapper_rejects_untrusted_process_url_and_unknown_currency() -> None:
    secop_i = get_source_definition(ExternalProcurementSourceSystem.SECOP_I)
    row = {
        "numero_de_proceso": "LP-SECOP-I-001",
        "detalle_del_objeto_a_contratar": "Servicio de fixture",
        "objeto_a_contratar": "Servicio de fixture",
        "nombre_entidad": "ENTIDAD PUBLICA FIXTURE",
        "cuantia_proceso": "1000",
        "moneda": "moneda no informada",
        "ruta_proceso_en_secop_i": {"url": "https://example.invalid/process"},
    }
    normalized, _ = map_secop_process(row, secop_i)
    assert normalized.source_process_id == "LP-SECOP-I-001"
    assert normalized.currency is None
    assert normalized.source_url is None
    assert {warning.code for warning in normalized.warnings} >= {
        "UNKNOWN_CURRENCY",
        "UNTRUSTED_SOURCE_URL",
    }


def test_secop_i_maps_published_currency_and_reports_unsupported_closing_filter() -> None:
    secop_i = get_source_definition(ExternalProcurementSourceSystem.SECOP_I)
    row = {
        "numero_de_proceso": "LP-SECOP-I-002",
        "detalle_del_objeto_a_contratar": "Servicio público de fixture",
        "objeto_a_contratar": "Servicio público de fixture",
        "nombre_entidad": "ENTIDAD PÚBLICA FIXTURE",
        "cuantia_proceso": "2500000",
        "moneda": "Peso Colombiano",
        "fecha_de_cargue_en_el_secop": "2026-07-01T00:00:00.000",
        "ruta_proceso_en_secop_i": {
            "url": "https://www.contratos.gov.co/consultas/detalleProceso.do?numConstancia=fixture"
        },
    }
    normalized, _ = map_secop_process(row, secop_i)
    assert normalized.source_process_id == "LP-SECOP-I-002"
    assert normalized.currency == "COP"
    assert normalized.publication_date is not None
    assert normalized.source_url is not None

    request = ExternalProcurementSearchRequest.model_validate(
        {
            "source_system": "SECOP_I",
            "closing_from": "2026-07-01T00:00:00-05:00",
            "closing_to": "2026-07-31T23:59:59-05:00",
        }
    )
    params, unsupported = build_query_params(secop_i, request)
    assert unsupported == ["closing_from", "closing_to"]
    assert "fecha_de_recepcion_de" not in params.get("$where", "")


def test_query_builder_uses_limit_offset_and_safe_filters() -> None:
    payload = ExternalProcurementSearchRequest.model_validate(
        {
            "query": "vigilancia",
            "entity_name": "Entidad O'Hara",
            "published_from": "2026-01-01T00:00:00-05:00",
            "limit": 10,
            "offset": 20,
        }
    )
    params, unsupported = build_query_params(
        get_source_definition(ExternalProcurementSourceSystem.SECOP_II), payload
    )
    assert params["$limit"] == "10"
    assert params["$offset"] == "20"
    assert params["$q"] == "vigilancia"
    assert "o''hara" in params["$where"]
    assert unsupported == []


@pytest.mark.parametrize(
    ("handler", "expected"),
    [
        (lambda _request: httpx.Response(503), ExternalProcurementErrorCode.SOURCE_UNAVAILABLE),
        (
            lambda _request: httpx.Response(200, json={"bad": "payload"}),
            ExternalProcurementErrorCode.SOURCE_INVALID_RESPONSE,
        ),
    ],
)
def test_http_errors_are_controlled(handler: Any, expected: ExternalProcurementErrorCode) -> None:
    settings = get_settings().model_copy(
        update={"secop_enabled": True, "secop_cache_ttl_minutes": 0}
    )
    client = DatosAbiertosClient(settings, transport=httpx.MockTransport(handler))
    with pytest.raises(ExternalProviderError) as captured:
        client.search(
            get_source_definition(ExternalProcurementSourceSystem.SECOP_II),
            ExternalProcurementSearchRequest(limit=1),
        )
    assert captured.value.code is expected
    client.close()


def test_timeout_retries_are_bounded() -> None:
    calls = 0

    def timeout(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("fixture timeout", request=request)

    settings = get_settings().model_copy(
        update={"secop_enabled": True, "secop_cache_ttl_minutes": 0}
    )
    client = DatosAbiertosClient(settings, transport=httpx.MockTransport(timeout))
    with pytest.raises(ExternalProviderError) as captured:
        client.search(
            get_source_definition(ExternalProcurementSourceSystem.SECOP_II),
            ExternalProcurementSearchRequest(limit=1),
        )
    assert captured.value.code is ExternalProcurementErrorCode.SOURCE_TIMEOUT
    assert calls == 3
    client.close()


def test_basic_local_rate_limit() -> None:
    settings = get_settings().model_copy(
        update={
            "secop_enabled": True,
            "secop_cache_ttl_minutes": 0,
            "secop_rate_limit_per_minute": 1,
        }
    )
    client = DatosAbiertosClient(
        settings,
        transport=httpx.MockTransport(lambda _request: httpx.Response(200, json=[])),
    )
    definition = get_source_definition(ExternalProcurementSourceSystem.SECOP_II)
    client.search(definition, ExternalProcurementSearchRequest(query="uno"))
    with pytest.raises(ExternalProviderError) as captured:
        client.search(definition, ExternalProcurementSearchRequest(query="dos"))
    assert captured.value.code is ExternalProcurementErrorCode.RATE_LIMITED
    client.close()


def test_secop_base_url_rejects_local_or_unofficial_hosts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PLIEGOCHECK_SECOP_BASE_URL", "https://127.0.0.1")
    get_settings.cache_clear()
    with pytest.raises(ValueError, match="origen HTTPS oficial"):
        get_settings()


def test_sources_search_import_duplicate_and_external_link(
    monkeypatch: pytest.MonkeyPatch, client: TestClient
) -> None:
    _enable(monkeypatch)
    monkeypatch.setattr(
        "pliegocheck_api.external_procurement.service.DatosAbiertosClient", FixtureClient
    )
    sources = client.get("/external-procurement/sources")
    assert sources.status_code == HTTPStatus.OK
    assert {item["dataset_id"] for item in sources.json()} == {"p6dx-8zbt", "f789-7hwg"}

    search = client.post(
        "/external-procurement/searches",
        json={"query": "vigilancia", "entity_name": "ENTIDAD", "limit": 1, "offset": 0},
    )
    assert search.status_code == HTTPStatus.CREATED
    body = search.json()
    assert body["search"]["result_count"] == 1
    assert "raw_payload" not in body["items"][0]
    result_id = body["items"][0]["id"]
    source_process_id = body["items"][0]["source_process_id"]

    imported = client.post(
        f"/external-procurement/results/{result_id}/import",
        json={"expected_source_process_id": source_process_id},
    )
    assert imported.status_code == HTTPStatus.CREATED
    assert imported.json()["status"] == "IMPORTED"
    process_id = imported.json()["process_id"]
    duplicate = client.post(
        f"/external-procurement/results/{result_id}/import",
        json={"expected_source_process_id": source_process_id},
    )
    assert duplicate.status_code == HTTPStatus.CREATED
    assert duplicate.json()["status"] == "SKIPPED_DUPLICATE"
    assert duplicate.json()["process_id"] == process_id

    links = client.get(f"/processes/{process_id}/external-links")
    assert links.status_code == HTTPStatus.OK
    assert links.json()["total"] == 1
    assert links.json()["items"][0]["source_process_id"] == source_process_id
    with get_sessionmaker()() as session:
        assert session.scalar(select(func.count()).select_from(Process)) == 1
        assert session.scalar(select(func.count()).select_from(ExternalProcurementProcessLink)) == 1
        assert session.scalar(select(func.count()).select_from(DecisionJob)) == 0
        stored = session.scalar(select(ExternalProcurementSearchResult))
        assert stored is not None
        assert "identificacion_del_contratista" not in stored.raw_payload
        process = session.get(Process, process_id)
        assert process is not None
        assert process.estimated_value == 125_000_000
        assert process.currency is None


def test_search_deduplicates_repeated_source_process_rows(
    monkeypatch: pytest.MonkeyPatch, client: TestClient
) -> None:
    _enable(monkeypatch)
    monkeypatch.setattr(
        "pliegocheck_api.external_procurement.service.DatosAbiertosClient",
        DuplicateFixtureClient,
    )
    response = client.post("/external-procurement/searches", json={"limit": 2})
    assert response.status_code == HTTPStatus.CREATED
    body = response.json()
    assert body["search"]["result_count"] == 1
    assert body["search"]["source_row_count"] == 2
    assert len(body["items"]) == 1
    assert any(
        warning["code"] == "DUPLICATE_SOURCE_PROCESS_SKIPPED"
        for warning in body["search"]["warnings"]
    )


def test_source_failure_is_persisted_and_sanitized(
    monkeypatch: pytest.MonkeyPatch, client: TestClient
) -> None:
    _enable(monkeypatch)
    monkeypatch.setattr(
        "pliegocheck_api.external_procurement.service.DatosAbiertosClient", FailingClient
    )
    response = client.post("/external-procurement/searches", json={"query": "fixture"})
    assert response.status_code == HTTPStatus.BAD_GATEWAY
    assert response.json()["code"] == "SOURCE_TIMEOUT"
    search_id = response.json()["details"]["search_id"]
    stored = client.get(f"/external-procurement/searches/{search_id}")
    assert stored.json()["status"] == "FAILED"
    assert "Traceback" not in stored.json()["error_message"]


def test_viewer_cannot_import(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    _enable(monkeypatch)
    monkeypatch.setattr(
        "pliegocheck_api.external_procurement.service.DatosAbiertosClient", FixtureClient
    )
    search = client.post("/external-procurement/searches", json={"limit": 1})
    result_id = search.json()["items"][0]["id"]
    monkeypatch.setenv("PLIEGOCHECK_AUTH_ENABLED", "true")
    monkeypatch.setenv("PLIEGOCHECK_AUTH_SECRET_KEY", "test-secret-not-real")
    get_settings.cache_clear()
    with get_sessionmaker()() as session:
        create_user(
            session,
            email="viewer-secop@example.com",
            display_name="Viewer",
            password="very-long-password",
            roles=[AuthRoleName.VIEWER],
        )
        session.commit()
    assert (
        client.post(
            "/auth/login",
            json={"email": "viewer-secop@example.com", "password": "very-long-password"},
        ).status_code
        == HTTPStatus.OK
    )
    denied = client.post(f"/external-procurement/results/{result_id}/import", json={})
    assert denied.status_code == HTTPStatus.FORBIDDEN
    assert denied.json()["details"]["required_permission"] == "external:import"


def test_cors_preflight_does_not_require_auth(client: TestClient) -> None:
    response = client.options(
        "/external-procurement/searches",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
