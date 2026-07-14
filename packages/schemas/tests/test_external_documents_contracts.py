"""Contratos cerrados de la Microfase 17."""

import pytest
from pydantic import ValidationError

from pliegocheck_schemas import (
    ExternalDocumentDownloadRequest,
    ExternalDocumentErrorCode,
    ExternalProcessSyncRequest,
)


def test_sync_request_is_closed_and_defaults_to_discovery() -> None:
    assert ExternalProcessSyncRequest().discover_documents is True
    with pytest.raises(ValidationError):
        ExternalProcessSyncRequest.model_validate({"download": True})


def test_download_requires_explicit_boolean_confirmation() -> None:
    assert ExternalDocumentDownloadRequest(confirm_public_download=True).confirm_public_download
    with pytest.raises(ValidationError):
        ExternalDocumentDownloadRequest.model_validate({})


def test_error_vocabulary_contains_security_and_versioning_failures() -> None:
    values = {item.value for item in ExternalDocumentErrorCode}
    assert {
        "EXTERNAL_DOCUMENT_URL_REJECTED",
        "EXTERNAL_DOCUMENT_TOO_LARGE",
        "EXTERNAL_DOCUMENT_CONTENT_TYPE_REJECTED",
        "EXTERNAL_DOCUMENT_VERSION_CONFLICT",
    } <= values
