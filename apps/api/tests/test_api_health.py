"""Pruebas de los endpoints de salud y del contrato OpenAPI de la API."""

from fastapi.testclient import TestClient

from pliegocheck_api.config import settings


def test_health_live_returns_200_with_expected_body(client: TestClient) -> None:
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "api", "version": settings.version}


def test_health_ready_returns_200_with_expected_body(client: TestClient) -> None:
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "api", "version": settings.version}


def test_openapi_document_is_available(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    document = response.json()
    assert document["info"]["title"] == settings.title
    assert document["info"]["version"] == settings.version
    assert "/health/live" in document["paths"]
    assert "/health/ready" in document["paths"]
    assert "/processes" in document["paths"]


def test_health_response_schema_in_openapi(client: TestClient) -> None:
    document = client.get("/openapi.json").json()
    schema = document["components"]["schemas"]["HealthResponse"]
    assert set(schema["required"]) == {"status", "service", "version"}
    assert schema["properties"]["status"]["const"] == "ok"
