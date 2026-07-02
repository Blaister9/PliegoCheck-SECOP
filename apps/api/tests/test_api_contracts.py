"""Prueba que la API consume el paquete compartido de contratos."""

from fastapi.testclient import TestClient

from pliegocheck_api.main import app
from pliegocheck_schemas import NORMALIZED_REQUIREMENT_SCHEMA_VERSION

client = TestClient(app)


def test_contracts_catalog_exposes_shared_schema_version() -> None:
    response = client.get("/contracts")
    assert response.status_code == 200
    contracts = response.json()["contracts"]
    assert len(contracts) == 1
    assert contracts[0]["name"] == "normalized_requirement"
    assert contracts[0]["schema_version"] == NORMALIZED_REQUIREMENT_SCHEMA_VERSION
    assert contracts[0]["title"] == "NormalizedRequirement"
