"""Prueba que la API consume el paquete compartido de contratos."""

from fastapi.testclient import TestClient

from pliegocheck_schemas import (
    EXTERNAL_PROCUREMENT_SCHEMA_VERSION,
    MANUAL_IMPORT_SCHEMA_VERSION,
    NORMALIZED_REQUIREMENT_SCHEMA_VERSION,
)


def test_contracts_catalog_exposes_shared_schema_version(client: TestClient) -> None:
    response = client.get("/contracts")
    assert response.status_code == 200
    contracts = response.json()["contracts"]
    by_name = {contract["name"]: contract for contract in contracts}
    assert (
        by_name["normalized_requirement"]["schema_version"] == NORMALIZED_REQUIREMENT_SCHEMA_VERSION
    )
    assert by_name["normalized_requirement"]["title"] == "NormalizedRequirement"
    assert by_name["manual_import"]["schema_version"] == MANUAL_IMPORT_SCHEMA_VERSION
    assert by_name["manual_import"]["title"] == "ManualImportContracts"
    assert by_name["external_procurement"]["schema_version"] == EXTERNAL_PROCUREMENT_SCHEMA_VERSION
