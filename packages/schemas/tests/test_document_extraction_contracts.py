"""Pruebas de contratos de extraccion documental."""

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from pliegocheck_schemas import (
    DocumentExtractionStatus,
    DocumentProcessingJobStatus,
    DocumentProcessingStatus,
    ExtractedSegmentType,
    ExtractionErrorCode,
    ExtractionRequest,
)

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


def load_example(name: str) -> dict[str, Any]:
    with (EXAMPLES_DIR / name).open(encoding="utf-8") as fh:
        data: dict[str, Any] = json.load(fh)
    return data


def test_valid_extraction_request_example_is_accepted() -> None:
    request = ExtractionRequest.model_validate(load_example("extraction-request.valid.json"))
    assert request.force is True


def test_invalid_extraction_request_example_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ExtractionRequest.model_validate(load_example("extraction-request.invalid.json"))


def test_document_processing_status_enum_is_closed() -> None:
    assert {status.value for status in DocumentProcessingStatus} == {
        "NOT_QUEUED",
        "QUEUED",
        "PROCESSING",
        "COMPLETED",
        "COMPLETED_WITH_WARNINGS",
        "NEEDS_OCR",
        "UNSUPPORTED",
        "ENCRYPTED",
        "FAILED",
    }


def test_job_and_extraction_statuses_are_closed() -> None:
    assert {status.value for status in DocumentProcessingJobStatus} == {
        "PENDING",
        "PROCESSING",
        "COMPLETED",
        "FAILED",
        "CANCELLED",
    }
    assert {status.value for status in DocumentExtractionStatus} == {
        "PENDING",
        "PROCESSING",
        "COMPLETED",
        "COMPLETED_WITH_WARNINGS",
        "NEEDS_OCR",
        "UNSUPPORTED",
        "ENCRYPTED",
        "FAILED",
    }


def test_segment_types_and_error_codes_are_closed() -> None:
    assert {segment_type.value for segment_type in ExtractedSegmentType} == {
        "PAGE_TEXT",
        "PARAGRAPH",
        "TABLE",
        "SHEET_ROW",
        "TEXT_LINES",
    }
    assert "SOURCE_HASH_MISMATCH" in {code.value for code in ExtractionErrorCode}
