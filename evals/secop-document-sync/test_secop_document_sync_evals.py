"""Evals deterministas y completamente offline de Microfase 17."""

import json
from pathlib import Path

import pytest

from pliegocheck_api.external_documents.providers import _map_secop_i, _map_secop_ii
from pliegocheck_api.external_documents.security import (
    ExternalDocumentSecurityError,
    validate_public_download_url,
)
from pliegocheck_api.external_documents.service import detect_process_changes
from pliegocheck_schemas import (
    ExternalDocumentAddendumStatus,
    ExternalDocumentDiscoveryStatus,
    ExternalDocumentDownloadStatus,
    ExternalProcessChangeEventType,
)

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "document_rows.json").read_text(encoding="utf-8")
)


def test_metadata_update_emits_only_supported_change_events() -> None:
    changes = detect_process_changes(
        {"status": "Publicado", "unknown": "old"},
        {"status": "Cerrado", "unknown": "new"},
    )
    assert changes == [
        (ExternalProcessChangeEventType.PROCESS_STATUS_CHANGED, "Publicado", "Cerrado")
    ]


def test_secop_ii_document_is_discovered_and_potential_addendum() -> None:
    document = _map_secop_ii(FIXTURE["secop_ii"], "dmgg-8hin")
    assert document.source_document_id == "DOC-17"
    assert document.addendum_status is ExternalDocumentAddendumStatus.POTENTIAL_ADDENDUM
    assert document.requires_human_review is True


def test_secop_ii_unsupported_extension_remains_a_link_only() -> None:
    row = {**FIXTURE["secop_ii"], "extensi_n": "rar"}
    document = _map_secop_ii(row, "dmgg-8hin")
    assert document.discovery_status is ExternalDocumentDiscoveryStatus.LINK_AVAILABLE
    assert document.download_status is ExternalDocumentDownloadStatus.UNSUPPORTED


def test_secop_i_public_link_is_inventory_only_not_downloadable() -> None:
    document = _map_secop_i(FIXTURE["secop_i"], "ps88-5e3v")
    assert document.download_status is ExternalDocumentDownloadStatus.UNSUPPORTED
    assert document.source_url.startswith("http://")


def test_secop_i_explicit_type_can_confirm_addendum() -> None:
    row = {**FIXTURE["secop_i"], "tipo": "Adenda", "nombrearchivo": "documento-1.pdf"}
    document = _map_secop_i(row, "ps88-5e3v")
    assert document.addendum_status is ExternalDocumentAddendumStatus.CONFIRMED_ADDENDUM


def test_public_link_failure_is_explicit_and_never_falls_back_to_private_network() -> None:
    with pytest.raises(ExternalDocumentSecurityError):
        validate_public_download_url(
            "https://files.example.gov.co/adenda.pdf",
            ["files.example.gov.co"],
            lambda _host, _port: ["169.254.169.254"],
        )
