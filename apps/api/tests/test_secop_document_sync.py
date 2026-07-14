"""Pruebas offline del inventario, SSRF, descarga y sincronizacion SECOP."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4
from zipfile import ZipFile

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from pliegocheck_api.auth import ROLE_PERMISSIONS, create_user
from pliegocheck_api.config import Settings, get_settings
from pliegocheck_api.db import get_sessionmaker
from pliegocheck_api.external_documents.download import (
    DownloadedArtifact,
    ExternalDownloadError,
    SafeDocumentDownloader,
)
from pliegocheck_api.external_documents.providers import (
    DiscoveredExternalDocument,
    ProcessRefresh,
)
from pliegocheck_api.external_documents.security import (
    ExternalDocumentSecurityError,
    validate_public_download_url,
)
from pliegocheck_api.external_documents.service import (
    enqueue_download,
    enqueue_sync,
    execute_download,
    execute_sync,
)
from pliegocheck_api.middleware import required_permission
from pliegocheck_api.models import (
    DecisionJob,
    DocumentProcessingJob,
    ExternalProcessChangeEvent,
    ExternalProcessDocument,
    ExternalProcessDocumentVersion,
    ExternalProcurementProcessLink,
    ExternalProcurementSearch,
    ExternalProcurementSearchResult,
    ExternalProcurementSource,
    Process,
    ProcessDocument,
)
from pliegocheck_schemas import (
    AuthPermission,
    AuthRoleName,
    ExternalDocumentAddendumStatus,
    ExternalDocumentDiscoveryStatus,
    ExternalDocumentDownloadStatus,
    ExternalProcessSyncStatus,
    ProcessSource,
    ProcessStatus,
)

PUBLIC_IP = ["93.184.216.34"]


@pytest.mark.parametrize(
    ("url", "addresses"),
    [
        ("http://files.example.gov.co/a.pdf", PUBLIC_IP),
        ("ftp://files.example.gov.co/a.pdf", PUBLIC_IP),
        ("https://user:pass@files.example.gov.co/a.pdf", PUBLIC_IP),
        ("https://files.example.gov.co:8443/a.pdf", PUBLIC_IP),
        ("https://other.example.gov.co/a.pdf", PUBLIC_IP),
        ("https://files.example.gov.co/a.pdf", ["127.0.0.1"]),
        ("https://files.example.gov.co/a.pdf", ["10.0.0.1"]),
        ("https://files.example.gov.co/a.pdf", ["169.254.169.254"]),
        ("https://files.example.gov.co/a.pdf", ["::1"]),
        ("https://files.example.gov.co/a.pdf", ["fc00::1"]),
    ],
)
def test_url_policy_rejects_non_https_non_allowlisted_and_non_public(
    url: str, addresses: list[str]
) -> None:
    with pytest.raises(ExternalDocumentSecurityError):
        validate_public_download_url(
            url,
            ["files.example.gov.co"],
            lambda _host, _port: addresses,
        )


def test_url_policy_accepts_allowlisted_public_https() -> None:
    result = validate_public_download_url(
        "https://files.example.gov.co/a.pdf",
        ["files.example.gov.co"],
        lambda _host, _port: PUBLIC_IP,
    )
    assert result.host == "files.example.gov.co"


def test_document_permissions_are_separated_by_action_and_role() -> None:
    base = "/processes/00000000-0000-0000-0000-000000000001"
    assert required_permission("POST", f"{base}/external-sync") is AuthPermission.EXTERNAL_SYNC
    assert (
        required_permission("POST", f"{base}/external-documents/x/download")
        is AuthPermission.EXTERNAL_DOWNLOAD
    )
    assert (
        required_permission("POST", f"{base}/external-documents/x/extract")
        is AuthPermission.DOCUMENT_WRITE
    )
    assert AuthPermission.EXTERNAL_SYNC in ROLE_PERMISSIONS[AuthRoleName.ANALYST]
    assert AuthPermission.EXTERNAL_SYNC not in ROLE_PERMISSIONS[AuthRoleName.VIEWER]
    assert AuthPermission.EXTERNAL_READ in ROLE_PERMISSIONS[AuthRoleName.VIEWER]


def test_external_document_routes_enforce_viewer_and_analyst_permissions(
    monkeypatch: pytest.MonkeyPatch, client: TestClient
) -> None:
    with get_sessionmaker()() as session:
        process, _ = _linked_process(session)
        process_id = process.id
        create_user(
            session,
            email="viewer-documents@example.com",
            display_name="Viewer documentos",
            password="very-long-password",
            roles=[AuthRoleName.VIEWER],
        )
        create_user(
            session,
            email="analyst-documents@example.com",
            display_name="Analyst documentos",
            password="very-long-password",
            roles=[AuthRoleName.ANALYST],
        )
        session.commit()

    monkeypatch.setenv("PLIEGOCHECK_AUTH_ENABLED", "true")
    monkeypatch.setenv("PLIEGOCHECK_AUTH_SECRET_KEY", "test-secret-not-real")
    get_settings.cache_clear()
    try:
        allowed_origin = "http://localhost:3000"
        anonymous = client.get(
            f"/processes/{process_id}/external-sync/readiness",
            headers={"Origin": allowed_origin},
        )
        assert anonymous.status_code == 401
        assert anonymous.json()["code"] == "AUTH_REQUIRED"
        assert anonymous.headers["access-control-allow-origin"] == allowed_origin
        assert anonymous.headers["access-control-allow-credentials"] == "true"
        assert anonymous.headers["access-control-allow-origin"] != "*"

        untrusted_origin = client.get(
            f"/processes/{process_id}/external-sync/readiness",
            headers={"Origin": "https://untrusted.example"},
        )
        assert untrusted_origin.status_code == 401
        assert "access-control-allow-origin" not in untrusted_origin.headers

        preflight = client.options(
            f"/processes/{process_id}/external-sync",
            headers={
                "Origin": allowed_origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert preflight.status_code == 200
        assert preflight.headers["access-control-allow-origin"] == allowed_origin
        assert preflight.headers["access-control-allow-credentials"] == "true"

        assert (
            client.post(
                "/auth/login",
                json={
                    "email": "viewer-documents@example.com",
                    "password": "very-long-password",
                },
            ).status_code
            == 200
        )
        assert client.get(f"/processes/{process_id}/external-sync/readiness").status_code == 200
        denied = client.post(
            f"/processes/{process_id}/external-sync",
            json={"discover_documents": True},
            headers={"Origin": allowed_origin},
        )
        assert denied.status_code == 403
        assert denied.json()["code"] == "AUTH_PERMISSION_DENIED"
        assert "required_permission" not in denied.json()["details"]
        assert denied.headers["access-control-allow-origin"] == allowed_origin
        assert denied.headers["access-control-allow-credentials"] == "true"
        download_denied = client.post(
            f"/processes/{process_id}/external-documents/{uuid4()}/download",
            json={"confirm_public_download": True},
            headers={"Origin": allowed_origin},
        )
        assert download_denied.status_code == 403
        assert download_denied.json()["code"] == "AUTH_PERMISSION_DENIED"
        assert download_denied.headers["access-control-allow-origin"] == allowed_origin

        assert client.post("/auth/logout").status_code == 200
        assert (
            client.post(
                "/auth/login",
                json={
                    "email": "analyst-documents@example.com",
                    "password": "very-long-password",
                },
            ).status_code
            == 200
        )
        queued = client.post(
            f"/processes/{process_id}/external-sync", json={"discover_documents": True}
        )
        assert queued.status_code == 202
    finally:
        get_settings.cache_clear()


def _settings(**changes: object) -> Settings:
    return get_settings().model_copy(
        update={
            "secop_document_download_enabled": True,
            "secop_document_allowed_hosts": ["files.example.gov.co"],
            "secop_document_allowed_content_types": ["application/pdf"],
            **changes,
        }
    )


def _transport(
    content: bytes, content_type: str = "application/pdf", status: int = 200
) -> httpx.MockTransport:
    return httpx.MockTransport(
        lambda request: httpx.Response(
            status,
            headers={"content-type": content_type, "content-length": str(len(content))},
            content=content,
            request=request,
        )
    )


def test_streaming_download_validates_and_hashes_pdf() -> None:
    downloader = SafeDocumentDownloader(
        _settings(), transport=_transport(b"%PDF-1.4\nfixture"), resolver=lambda *_: PUBLIC_IP
    )
    artifact = downloader.download("https://files.example.gov.co/a.pdf", "Pliego")
    try:
        assert artifact.sha256 == "7dfd2b80df499f12a5740d2f0ac27c27549ca76b03158339618d4f7d2b22d233"
        assert artifact.detected_content_type == "application/pdf"
    finally:
        artifact.path.unlink(missing_ok=True)
        downloader.close()


@pytest.mark.parametrize(
    ("content_type", "content", "detected"),
    [
        ("text/plain", b"texto publico", "text/plain"),
        ("text/csv", b"columna\nvalor\n", "text/csv"),
        (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            None,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
        (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            None,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
    ],
)
def test_supported_pipeline_types_are_detected(
    content_type: str, content: bytes | None, detected: str
) -> None:
    if content is None:
        member = "word/document.xml" if "wordprocessing" in content_type else "xl/workbook.xml"
        stream = BytesIO()
        with ZipFile(stream, "w") as archive:
            archive.writestr("[Content_Types].xml", "<Types />")
            archive.writestr(member, "<document />")
        content = stream.getvalue()
    downloader = SafeDocumentDownloader(
        _settings(secop_document_allowed_content_types=[content_type]),
        transport=_transport(content, content_type),
        resolver=lambda *_: PUBLIC_IP,
    )
    artifact = downloader.download("https://files.example.gov.co/documento", "Documento")
    try:
        assert artifact.detected_content_type == detected
    finally:
        artifact.path.unlink(missing_ok=True)
        downloader.close()


@pytest.mark.parametrize(
    ("content", "content_type", "expected"),
    [
        (b"<html>login</html>", "text/html", "EXTERNAL_DOCUMENT_HTML_RESPONSE"),
        (b"MZ malicious", "application/octet-stream", "EXTERNAL_DOCUMENT_CONTENT_TYPE_REJECTED"),
        (b"not-a-pdf", "application/pdf", "EXTERNAL_DOCUMENT_CONTENT_TYPE_REJECTED"),
    ],
)
def test_download_rejects_html_type_and_signature(
    content: bytes, content_type: str, expected: str
) -> None:
    downloader = SafeDocumentDownloader(
        _settings(), transport=_transport(content, content_type), resolver=lambda *_: PUBLIC_IP
    )
    with pytest.raises(ExternalDownloadError) as caught:
        downloader.download("https://files.example.gov.co/a.pdf", "Pliego")
    downloader.close()
    assert caught.value.code.value == expected


def test_download_rejects_declared_and_streamed_oversize() -> None:
    downloader = SafeDocumentDownloader(
        _settings(secop_document_max_file_size_bytes=8),
        transport=_transport(b"%PDF-1.4-too-long"),
        resolver=lambda *_: PUBLIC_IP,
    )
    with pytest.raises(ExternalDownloadError) as caught:
        downloader.download("https://files.example.gov.co/a.pdf", "Pliego")
    downloader.close()
    assert caught.value.code.value == "EXTERNAL_DOCUMENT_TOO_LARGE"


def test_redirect_is_revalidated_and_private_target_is_rejected() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "files.example.gov.co":
            return httpx.Response(302, headers={"location": "https://private.example/a.pdf"})
        raise AssertionError("No debe solicitar el destino rechazado")

    def resolver(host: str, _port: int) -> list[str]:
        return PUBLIC_IP if host == "files.example.gov.co" else ["127.0.0.1"]

    downloader = SafeDocumentDownloader(
        _settings(secop_document_allowed_hosts=["files.example.gov.co", "private.example"]),
        transport=httpx.MockTransport(handler),
        resolver=resolver,
    )
    with pytest.raises(ExternalDocumentSecurityError):
        downloader.download("https://files.example.gov.co/start", "Pliego")
    downloader.close()


class FakeProvider:
    def __init__(self, refresh: ProcessRefresh) -> None:
        self.refresh_result = refresh

    def refresh(self, link: ExternalProcurementProcessLink, max_documents: int) -> ProcessRefresh:
        _ = link, max_documents
        return self.refresh_result

    def close(self) -> None:
        return None


def _linked_process(session: Session) -> tuple[Process, ExternalProcurementProcessLink]:
    now = datetime.now(UTC)
    source = ExternalProcurementSource(
        id=uuid4(),
        source_system="SECOP_II",
        provider="datos_abiertos",
        name="SECOP II",
        base_url="https://www.datos.gov.co",
        dataset_id="p6dx-8zbt",
        human_url="https://www.datos.gov.co",
        api_url="https://www.datos.gov.co/resource/p6dx-8zbt.json",
        status="AVAILABLE",
        source_metadata={},
    )
    session.add(source)
    session.flush()
    search = ExternalProcurementSearch(
        id=uuid4(),
        source_id=source.id,
        filters={},
        status="COMPLETED",
        result_count=1,
        source_row_count=1,
        page_count=1,
        limit=1,
        offset=0,
        unsupported_filters=[],
        warnings=[],
        started_at=now,
        finished_at=now,
    )
    session.add(search)
    session.flush()
    result = ExternalProcurementSearchResult(
        id=uuid4(),
        search_id=search.id,
        source_id=source.id,
        source_system="SECOP_II",
        source_dataset="p6dx-8zbt",
        source_process_id="CO1.REQ.1",
        source_process_reference="REF-1",
        title="Proceso",
        entity_name="Entidad",
        raw_payload={},
        normalized_payload={},
        raw_payload_hash="a" * 64,
        field_statuses={},
        warnings=[],
        source_url="https://community.secop.gov.co",
        documents_status="DOCUMENT_LINKS_AVAILABLE",
        import_status="IMPORTED",
    )
    process = Process(
        id=uuid4(),
        internal_reference=f"TEST-{uuid4().hex[:8]}",
        title="Proceso",
        contracting_entity="Entidad",
        source=ProcessSource.SECOP_IMPORT.value,
        status=ProcessStatus.DOCUMENTS_PENDING.value,
    )
    session.add_all([result, process])
    session.flush()
    link = ExternalProcurementProcessLink(
        id=uuid4(),
        process_id=process.id,
        source_result_id=result.id,
        source_system="SECOP_II",
        source_dataset="p6dx-8zbt",
        source_process_id="CO1.REQ.1",
        source_process_reference="REF-1",
        source_url=result.source_url,
        documents_status="DOCUMENT_LINKS_AVAILABLE",
        external_metadata={},
        imported_at=now,
    )
    session.add(link)
    session.commit()
    return process, link


def _document(title: str = "Pliego", updated: datetime | None = None) -> DiscoveredExternalDocument:
    return DiscoveredExternalDocument(
        source_document_id="DOC-1",
        source_document_reference=None,
        title=title,
        document_type="pdf",
        document_category="pliego",
        source_url="https://files.example.gov.co/a.pdf",
        source_public_url="https://www.datos.gov.co/resource/dmgg-8hin",
        published_at=None,
        updated_at_source=updated,
        reported_size_bytes=10,
        reported_content_type=None,
        discovery_status=ExternalDocumentDiscoveryStatus.DISCOVERED,
        download_status=ExternalDocumentDownloadStatus.NOT_REQUESTED,
        addendum_status=ExternalDocumentAddendumStatus.NOT_ADDENDUM,
        requires_human_review=False,
    )


def _confirmed_addendum() -> DiscoveredExternalDocument:
    base = _document("Adenda expresa")
    return DiscoveredExternalDocument(
        **{
            **base.__dict__,
            "source_document_id": "ADD-1",
            "addendum_status": ExternalDocumentAddendumStatus.CONFIRMED_ADDENDUM,
            "requires_human_review": True,
        }
    )


def test_sync_is_idempotent_and_records_document_update() -> None:
    settings = _settings(secop_document_sync_enabled=True, secop_incremental_sync_enabled=True)
    with get_sessionmaker()() as session:
        process, _ = _linked_process(session)
        first = enqueue_sync(session, settings, process.id, discover_documents=True)
        execute_sync(
            session,
            settings,
            first.id,
            provider=FakeProvider(ProcessRefresh({"status": "Publicado"}, None, (_document(),))),
        )
        second = enqueue_sync(session, settings, process.id, discover_documents=True)
        execute_sync(
            session,
            settings,
            second.id,
            provider=FakeProvider(ProcessRefresh({"status": "Publicado"}, None, (_document(),))),
        )
        assert second.status == ExternalProcessSyncStatus.COMPLETED.value
        assert second.documents_unchanged == 1
        third = enqueue_sync(session, settings, process.id, discover_documents=True)
        execute_sync(
            session,
            settings,
            third.id,
            provider=FakeProvider(
                ProcessRefresh(
                    {"status": "Cerrado"},
                    None,
                    (_document("Pliego actualizado"),),
                )
            ),
        )
        assert third.documents_updated == 1
        assert (
            session.scalar(
                select(ExternalProcessDocument).where(
                    ExternalProcessDocument.process_id == process.id
                )
            )
            is not None
        )


def test_sync_reclassifies_an_unsupported_source_extension_without_deleting_history() -> None:
    settings = _settings(secop_document_sync_enabled=True, secop_incremental_sync_enabled=True)
    with get_sessionmaker()() as session:
        process, _ = _linked_process(session)
        first = enqueue_sync(session, settings, process.id, discover_documents=True)
        execute_sync(
            session,
            settings,
            first.id,
            provider=FakeProvider(ProcessRefresh({}, None, (_document(),))),
        )
        unsupported = replace(
            _document(),
            document_type="rar",
            discovery_status=ExternalDocumentDiscoveryStatus.LINK_AVAILABLE,
            download_status=ExternalDocumentDownloadStatus.UNSUPPORTED,
        )
        second = enqueue_sync(session, settings, process.id, discover_documents=True)
        execute_sync(
            session,
            settings,
            second.id,
            provider=FakeProvider(ProcessRefresh({}, None, (unsupported,))),
        )
        stored = session.scalar(
            select(ExternalProcessDocument).where(ExternalProcessDocument.process_id == process.id)
        )
        assert stored is not None
        assert stored.discovery_status == ExternalDocumentDiscoveryStatus.LINK_AVAILABLE.value
        assert stored.download_status == ExternalDocumentDownloadStatus.UNSUPPORTED.value


def test_api_exposes_readiness_inventory_and_idempotent_queue(client: TestClient) -> None:
    with get_sessionmaker()() as session:
        process, _ = _linked_process(session)
        process_id = process.id
    ready = client.get(f"/processes/{process_id}/external-sync/readiness")
    assert ready.status_code == 200
    assert ready.json()["available"] is True
    queued = client.post(
        f"/processes/{process_id}/external-sync", json={"discover_documents": True}
    )
    repeated = client.post(
        f"/processes/{process_id}/external-sync", json={"discover_documents": True}
    )
    assert queued.status_code == repeated.status_code == 202
    assert queued.json()["sync_run_id"] == repeated.json()["sync_run_id"]
    inventory = client.get(f"/processes/{process_id}/external-documents")
    assert inventory.status_code == 200
    assert inventory.json()["items"] == []


def test_missing_document_and_confirmed_addendum_create_events() -> None:
    settings = _settings(secop_document_sync_enabled=True, secop_incremental_sync_enabled=True)
    with get_sessionmaker()() as session:
        process, _ = _linked_process(session)
        first = enqueue_sync(session, settings, process.id, discover_documents=True)
        execute_sync(
            session,
            settings,
            first.id,
            provider=FakeProvider(ProcessRefresh({}, None, (_document(), _confirmed_addendum()))),
        )
        second = enqueue_sync(session, settings, process.id, discover_documents=True)
        execute_sync(
            session, settings, second.id, provider=FakeProvider(ProcessRefresh({}, None, ()))
        )
        statuses = set(
            session.scalars(
                select(ExternalProcessDocument.discovery_status).where(
                    ExternalProcessDocument.process_id == process.id
                )
            ).all()
        )
        events = set(
            session.scalars(
                select(ExternalProcessChangeEvent.event_type).where(
                    ExternalProcessChangeEvent.process_id == process.id
                )
            ).all()
        )
        assert statuses == {ExternalDocumentDiscoveryStatus.MISSING.value}
        assert "CONFIRMED_ADDENDUM_DISCOVERED" in events
        assert "DOCUMENT_REMOVED_FROM_SOURCE" in events


def test_missing_source_field_preserves_current_process_and_warns() -> None:
    settings = _settings(secop_document_sync_enabled=True, secop_incremental_sync_enabled=True)
    with get_sessionmaker()() as session:
        process, _ = _linked_process(session)
        first = enqueue_sync(session, settings, process.id, discover_documents=False)
        execute_sync(
            session,
            settings,
            first.id,
            provider=FakeProvider(
                ProcessRefresh({"title": "Titulo fuente", "status": "Abierto"}, None, ())
            ),
        )
        second = enqueue_sync(session, settings, process.id, discover_documents=False)
        execute_sync(
            session,
            settings,
            second.id,
            provider=FakeProvider(ProcessRefresh({"title": None, "status": "Cerrado"}, None, ())),
        )
        session.refresh(process)
        assert process.title == "Titulo fuente"
        assert any(item["code"] == "SOURCE_FIELD_NOW_MISSING" for item in second.warnings)


class ArtifactDownloader:
    def __init__(self, content: bytes) -> None:
        self.content = content

    def download(self, url: str, title: str) -> DownloadedArtifact:
        import hashlib

        _ = url
        with NamedTemporaryFile(suffix=".pdf", delete=False) as temp:
            temp.write(self.content)
        return DownloadedArtifact(
            Path(temp.name),
            f"{title}.pdf",
            ".pdf",
            hashlib.sha256(self.content).hexdigest(),
            len(self.content),
            "application/pdf",
            "application/pdf",
            "https://files.example.gov.co/a.pdf",
        )

    def close(self) -> None:
        return None


def test_download_deduplicates_hash_and_creates_immutable_new_version() -> None:
    settings = _settings()
    with get_sessionmaker()() as session:
        process, link = _linked_process(session)
        external = ExternalProcessDocument(
            id=uuid4(),
            process_id=process.id,
            external_process_link_id=link.id,
            source_system="SECOP_II",
            source_document_id="DOC-1",
            title="Pliego",
            source_url="https://files.example.gov.co/a.pdf",
            source_public_url="https://www.datos.gov.co/resource/dmgg-8hin",
            discovery_status="DISCOVERED",
            download_status="NOT_REQUESTED",
            addendum_status="NOT_ADDENDUM",
            requires_human_review=False,
        )
        session.add(external)
        session.commit()
        job = enqueue_download(session, settings, process.id, external.id)
        execute_download(session, settings, job.id, downloader=ArtifactDownloader(b"%PDF-1.4 v1"))
        same = enqueue_download(session, settings, process.id, external.id)
        execute_download(session, settings, same.id, downloader=ArtifactDownloader(b"%PDF-1.4 v1"))
        changed = enqueue_download(session, settings, process.id, external.id)
        execute_download(
            session, settings, changed.id, downloader=ArtifactDownloader(b"%PDF-1.4 v2")
        )
        session.refresh(external)
        assert external.version_count == 2
        assert (
            len(
                session.scalars(
                    select(ExternalProcessDocumentVersion).where(
                        ExternalProcessDocumentVersion.external_document_id == external.id
                    )
                ).all()
            )
            == 2
        )
        assert (
            len(
                session.scalars(
                    select(ProcessDocument).where(ProcessDocument.process_id == process.id)
                ).all()
            )
            == 2
        )


def test_database_failure_compensates_new_storage(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _settings()
    with get_sessionmaker()() as session:
        process, link = _linked_process(session)
        external = ExternalProcessDocument(
            id=uuid4(),
            process_id=process.id,
            external_process_link_id=link.id,
            source_system="SECOP_II",
            source_document_id="DOC-FAIL",
            title="Pliego",
            source_url="https://files.example.gov.co/a.pdf",
            source_public_url="https://www.datos.gov.co/resource/dmgg-8hin",
            discovery_status="DISCOVERED",
            download_status="NOT_REQUESTED",
            addendum_status="NOT_ADDENDUM",
            requires_human_review=False,
        )
        session.add(external)
        session.commit()
        job = enqueue_download(session, settings, process.id, external.id)
        real_commit = session.commit

        def fail_once() -> None:
            monkeypatch.setattr(session, "commit", real_commit)
            raise SQLAlchemyError("fixture database failure")

        monkeypatch.setattr(session, "commit", fail_once)
        result = execute_download(
            session, settings, job.id, downloader=ArtifactDownloader(b"%PDF-1.4 failure")
        )
        assert result.status == ExternalDocumentDownloadStatus.FAILED.value
        assert session.scalar(select(func.count()).select_from(ProcessDocument)) == 0
        assert not any(settings.storage_path.rglob("*.pdf"))


def test_explicit_extract_creates_no_decision_job(client: TestClient) -> None:
    settings = _settings()
    with get_sessionmaker()() as session:
        process, link = _linked_process(session)
        external = ExternalProcessDocument(
            id=uuid4(),
            process_id=process.id,
            external_process_link_id=link.id,
            source_system="SECOP_II",
            source_document_id="DOC-EXTRACT",
            title="Pliego",
            source_url="https://files.example.gov.co/a.pdf",
            source_public_url="https://www.datos.gov.co/resource/dmgg-8hin",
            discovery_status="DISCOVERED",
            download_status="NOT_REQUESTED",
            addendum_status="NOT_ADDENDUM",
            requires_human_review=False,
        )
        session.add(external)
        session.commit()
        job = enqueue_download(session, settings, process.id, external.id)
        execute_download(
            session,
            settings,
            job.id,
            downloader=ArtifactDownloader(b"%PDF-1.4 extraction"),
        )
        process_id, document_id = process.id, external.id
    response = client.post(
        f"/processes/{process_id}/external-documents/{document_id}/extract", json={}
    )
    assert response.status_code == 202
    with get_sessionmaker()() as session:
        assert session.scalar(select(func.count()).select_from(DocumentProcessingJob)) == 1
        assert session.scalar(select(func.count()).select_from(DecisionJob)) == 0
