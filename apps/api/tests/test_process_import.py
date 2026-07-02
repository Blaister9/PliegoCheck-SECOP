"""Pruebas de importacion manual de procesos y documentos."""

from hashlib import sha256
from pathlib import Path
from typing import Any, cast

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import Engine

PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n"


def create_process(
    client: TestClient,
    title: str = "Servicio de vigilancia judicial",
) -> dict[str, Any]:
    response = client.post(
        "/processes",
        json={
            "title": title,
            "contracting_entity": "Entidad de ejemplo",
            "secop_reference": "CO1.NTC.123",
            "estimated_value": "1250000000.50",
            "published_at": "2026-06-01T08:00:00-05:00",
            "closing_at": "2026-07-15T17:00:00-05:00",
        },
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json())


def test_create_process_and_detail(client: TestClient, migrated_engine: Engine) -> None:
    process = create_process(client)
    assert process["title"] == "Servicio de vigilancia judicial"
    assert process["status"] == "DRAFT"
    assert process["source"] == "MANUAL"
    assert process["internal_reference"].startswith("MAN-")
    assert process["document_count"] == 0
    assert process["estimated_value"] == "1250000000.50"

    detail = client.get(f"/processes/{process['id']}").json()
    assert detail["id"] == process["id"]
    assert "storage_key" not in str(detail)
    with migrated_engine.connect() as connection:
        count = connection.scalar(
            text("SELECT count(*) FROM import_events WHERE event_type = 'PROCESS_CREATED'")
        )
    assert count == 1


def test_process_validation_errors_are_structured(client: TestClient) -> None:
    response = client.post(
        "/processes",
        json={
            "title": " ",
            "contracting_entity": "",
            "published_at": "2026-07-15T17:00:00-05:00",
            "closing_at": "2026-06-01T08:00:00-05:00",
        },
    )
    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "INVALID_PROCESS_DATA"
    assert "details" in payload


def test_list_search_filter_and_pagination(client: TestClient) -> None:
    first = create_process(client, "Servicio de vigilancia judicial")
    create_process(client, "Obra civil menor")

    response = client.get("/processes", params={"search": "vigilancia", "limit": 1, "offset": 0})
    payload = response.json()
    assert response.status_code == 200
    assert payload["total"] == 1
    assert payload["items"][0]["id"] == first["id"]

    filtered = client.get("/processes", params={"status": "DRAFT"}).json()
    assert filtered["total"] == 2


def test_process_not_found(client: TestClient) -> None:
    response = client.get("/processes/00000000-0000-0000-0000-000000000001")
    assert response.status_code == 404
    assert response.json()["code"] == "PROCESS_NOT_FOUND"


def test_upload_list_duplicate_and_download(client: TestClient, migrated_engine: Engine) -> None:
    process = create_process(client)
    upload = client.post(
        f"/processes/{process['id']}/documents",
        files={"files": ("pliego.pdf", PDF_BYTES, "application/pdf")},
    )
    assert upload.status_code == 201, upload.text
    result = upload.json()["results"][0]
    assert result["upload_status"] == "STORED"
    document = result["document"]
    assert document["sha256"] == sha256(PDF_BYTES).hexdigest()
    assert document["document_type"] == "UNKNOWN"
    assert "storage_key" not in str(upload.json())

    detail = client.get(f"/processes/{process['id']}").json()
    assert detail["status"] == "READY_FOR_INVENTORY"
    assert detail["document_count"] == 1

    duplicate = client.post(
        f"/processes/{process['id']}/documents",
        files={"files": ("pliego.pdf", PDF_BYTES, "application/pdf")},
    )
    assert duplicate.status_code == 400
    duplicate_result = duplicate.json()["results"][0]
    assert duplicate_result["upload_status"] == "REJECTED"
    assert duplicate_result["error"]["code"] == "DUPLICATE_DOCUMENT"

    listed = client.get(f"/processes/{process['id']}/documents").json()
    assert listed["total"] == 1
    assert "storage_key" not in str(listed)

    download = client.get(f"/processes/{process['id']}/documents/{document['id']}/download")
    assert download.status_code == 200
    assert download.content == PDF_BYTES
    assert sha256(download.content).hexdigest() == document["sha256"]
    assert "filename*=UTF-8''pliego.pdf" in download.headers["content-disposition"]

    with migrated_engine.connect() as connection:
        event_types = (
            connection.execute(text("SELECT event_type FROM import_events")).scalars().all()
        )
    assert "DOCUMENT_UPLOADED" in event_types
    assert "DUPLICATE_DOCUMENT_REJECTED" in event_types
    assert "DOCUMENT_DOWNLOADED" in event_types


def test_multiple_upload_partial_success(client: TestClient) -> None:
    process = create_process(client)
    response = client.post(
        f"/processes/{process['id']}/documents",
        files=[
            ("files", ("pliego.pdf", PDF_BYTES, "application/pdf")),
            ("files", ("script.exe", b"MZ", "application/x-msdownload")),
        ],
    )
    assert response.status_code == 207
    payload = response.json()
    assert payload["stored_count"] == 1
    assert payload["rejected_count"] == 1
    assert {result["upload_status"] for result in payload["results"]} == {"STORED", "REJECTED"}


def test_rejects_empty_forbidden_large_and_mismatched_files(client: TestClient) -> None:
    process = create_process(client)
    cases = [
        ("empty.pdf", b"", "application/pdf", "FILE_EMPTY"),
        ("script.exe", b"MZ", "application/x-msdownload", "FILE_TYPE_NOT_ALLOWED"),
        ("pliego.pdf", b"MZ", "application/pdf", "FILE_CONTENT_MISMATCH"),
        ("safe.pdf.exe.pdf", PDF_BYTES, "application/pdf", "FILE_CONTENT_MISMATCH"),
        ("large.pdf", b"%PDF-" + (b"0" * (1024 * 1024 + 1)), "application/pdf", "FILE_TOO_LARGE"),
    ]
    for filename, content, content_type, expected_code in cases:
        response = client.post(
            f"/processes/{process['id']}/documents",
            files={"files": (filename, content, content_type)},
        )
        assert response.status_code == 400
        result = response.json()["results"][0]
        assert result["upload_status"] == "REJECTED"
        assert result["error"]["code"] == expected_code


def test_cross_process_download_is_not_allowed(client: TestClient) -> None:
    first = create_process(client, "Primer proceso")
    second = create_process(client, "Segundo proceso")
    upload = client.post(
        f"/processes/{first['id']}/documents",
        files={"files": ("pliego.pdf", PDF_BYTES, "application/pdf")},
    ).json()
    document_id = upload["results"][0]["document"]["id"]

    response = client.get(f"/processes/{second['id']}/documents/{document_id}/download")
    assert response.status_code == 404
    assert response.json()["code"] == "DOCUMENT_NOT_FOUND"


def test_storage_uses_relative_keys(client: TestClient, migrated_engine: Engine) -> None:
    process = create_process(client)
    client.post(
        f"/processes/{process['id']}/documents",
        files={"files": ("pliego.pdf", PDF_BYTES, "application/pdf")},
    )
    with migrated_engine.connect() as connection:
        storage_key = connection.scalar(text("SELECT storage_key FROM process_documents LIMIT 1"))
    assert storage_key is not None
    assert not Path(storage_key).is_absolute()
    assert ".." not in Path(storage_key).parts
