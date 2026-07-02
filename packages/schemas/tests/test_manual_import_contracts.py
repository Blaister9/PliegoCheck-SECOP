"""Pruebas de los contratos de importacion manual."""

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from pliegocheck_schemas import (
    DocumentUploadStatus,
    ProcessCreate,
    ProcessDocumentMetadata,
    ProcessStatus,
)

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


def load_example(name: str) -> dict[str, Any]:
    with (EXAMPLES_DIR / name).open(encoding="utf-8") as fh:
        data: dict[str, Any] = json.load(fh)
    return data


def test_valid_process_create_example_is_accepted() -> None:
    process = ProcessCreate.model_validate(load_example("process-create.valid.json"))
    assert process.title == "Servicio de vigilancia judicial"
    assert process.currency == "COP"
    assert process.estimated_value == Decimal("1250000000.50")
    assert process.published_at is not None and process.published_at.tzinfo is not None
    assert process.closing_at is not None and process.closing_at >= process.published_at


def test_invalid_process_create_example_is_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        ProcessCreate.model_validate(load_example("process-create.invalid.json"))
    failed = {
        str(error["loc"][0]) if error["loc"] else "__root__" for error in excinfo.value.errors()
    }
    assert {"title", "contracting_entity", "source_url", "estimated_value", "currency"} <= failed


def test_minimal_process_create_defaults() -> None:
    process = ProcessCreate.model_validate(
        {"title": "Proceso mínimo", "contracting_entity": "Entidad"}
    )
    assert process.currency == "COP"
    assert process.estimated_value is None
    assert process.secop_reference is None


def test_closing_before_published_is_rejected() -> None:
    with pytest.raises(ValidationError, match="closing_at"):
        ProcessCreate.model_validate(
            {
                "title": "Proceso",
                "contracting_entity": "Entidad",
                "published_at": "2026-07-15T17:00:00-05:00",
                "closing_at": "2026-06-01T08:00:00-05:00",
            }
        )


def test_naive_datetimes_are_rejected() -> None:
    with pytest.raises(ValidationError):
        ProcessCreate.model_validate(
            {
                "title": "Proceso",
                "contracting_entity": "Entidad",
                "published_at": "2026-06-01T08:00:00",
            }
        )


def test_estimated_value_is_decimal_not_float() -> None:
    process = ProcessCreate.model_validate(
        {
            "title": "Proceso",
            "contracting_entity": "Entidad",
            "estimated_value": "0.1",
        }
    )
    assert isinstance(process.estimated_value, Decimal)
    assert process.estimated_value == Decimal("0.1")


def test_process_status_enum_is_closed() -> None:
    assert {status.value for status in ProcessStatus} == {
        "DRAFT",
        "DOCUMENTS_PENDING",
        "READY_FOR_INVENTORY",
    }


def test_document_metadata_rejects_invalid_sha256() -> None:
    with pytest.raises(ValidationError):
        ProcessDocumentMetadata.model_validate(
            {
                "id": "0e5efb37-6f3b-4f2f-9b41-000000000001",
                "original_filename": "pliego.pdf",
                "document_type": "TERMS",
                "extension": ".pdf",
                "size_bytes": 100,
                "sha256": "NO-ES-UN-HASH",
                "declared_content_type": "application/pdf",
                "detected_content_type": "application/pdf",
                "upload_status": DocumentUploadStatus.STORED,
                "created_at": datetime.now(UTC),
            }
        )
