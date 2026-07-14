"""Evals offline del conector; ninguna prueba abre conexiones de red."""

import json
from pathlib import Path

import httpx
import pytest

from pliegocheck_api.config import get_settings
from pliegocheck_api.external_procurement.datos_abiertos import (
    DatosAbiertosClient,
    build_query_params,
)
from pliegocheck_api.external_procurement.errors import ExternalProviderError
from pliegocheck_api.external_procurement.providers import SOURCE_DEFINITIONS, get_source_definition
from pliegocheck_api.external_procurement.secop_mapper import map_secop_process
from pliegocheck_schemas import (
    ExternalProcurementDocumentStatus,
    ExternalProcurementErrorCode,
    ExternalProcurementSearchRequest,
    ExternalProcurementSourceSystem,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).parent / "fixtures/secop_ii_processes.json"


def rows() -> list[dict[str, object]]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_source_catalog_is_official_and_configured() -> None:
    assert SOURCE_DEFINITIONS[ExternalProcurementSourceSystem.SECOP_II].dataset_id == "p6dx-8zbt"
    assert SOURCE_DEFINITIONS[ExternalProcurementSourceSystem.SECOP_I].dataset_id == "f789-7hwg"
    assert all(item.metadata["verified_on"] == "2026-07-13" for item in SOURCE_DEFINITIONS.values())
    assert (
        SOURCE_DEFINITIONS[ExternalProcurementSourceSystem.SECOP_I].field_map["source_process_id"]
        == "numero_de_proceso"
    )


@pytest.mark.parametrize(
    ("payload", "expected_fragment"),
    [
        ({"query": "vigilancia"}, ("$q", "vigilancia")),
        ({"entity_name": "ENTIDAD"}, ("$where", "entidad")),
        ({"published_from": "2026-01-01T00:00:00-05:00"}, ("$where", "fecha_de_publicacion_del")),
        ({"limit": 10, "offset": 20}, ("$offset", "20")),
    ],
)
def test_search_filters_and_pagination(
    payload: dict[str, object], expected_fragment: tuple[str, str]
) -> None:
    params, _ = build_query_params(
        get_source_definition(ExternalProcurementSourceSystem.SECOP_II),
        ExternalProcurementSearchRequest.model_validate(payload),
    )
    assert expected_fragment[1] in params[expected_fragment[0]]


def test_normalized_result_and_missing_field_warning() -> None:
    complete, safe = map_secop_process(
        rows()[0], get_source_definition(ExternalProcurementSourceSystem.SECOP_II)
    )
    missing_row = dict(rows()[1])
    missing_row.pop("fecha_de_recepcion_de", None)
    missing, _ = map_secop_process(
        missing_row, get_source_definition(ExternalProcurementSourceSystem.SECOP_II)
    )
    assert complete.raw_payload_hash
    assert complete.estimated_value == 125_000_000
    assert complete.currency is None
    assert any(warning.code == "UNKNOWN_CURRENCY" for warning in complete.warnings)
    assert (
        complete.documents_status is ExternalProcurementDocumentStatus.DOCUMENT_DOWNLOAD_UNSUPPORTED
    )
    assert any(warning.field == "closing_date" for warning in missing.warnings)
    assert set(safe).issubset(
        get_source_definition(ExternalProcurementSourceSystem.SECOP_II).safe_fields
    )


def test_source_down_is_controlled_with_mock_transport_only() -> None:
    settings = get_settings().model_copy(
        update={"secop_enabled": True, "secop_cache_ttl_minutes": 0}
    )
    client = DatosAbiertosClient(
        settings,
        transport=httpx.MockTransport(lambda _request: httpx.Response(503)),
    )
    with pytest.raises(ExternalProviderError) as captured:
        client.search(
            get_source_definition(ExternalProcurementSourceSystem.SECOP_II),
            ExternalProcurementSearchRequest(limit=1),
        )
    assert captured.value.code is ExternalProcurementErrorCode.SOURCE_UNAVAILABLE
    client.close()


def test_ci_and_commands_keep_live_network_disabled() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    api_tests = (ROOT / "apps/api/tests/test_secop_connector.py").read_text(encoding="utf-8")
    assert 'PLIEGOCHECK_SECOP_ALLOW_LIVE_TESTS: "false"' in workflow
    assert "secop:smoke" not in workflow
    assert "secop:eval" in package["scripts"]["check"]
    for evidence in [
        "SKIPPED_DUPLICATE",
        "external-links",
        "external:import",
        "DecisionJob",
        '"raw_payload" not in',
    ]:
        assert evidence in api_tests
