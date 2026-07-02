"""Modelos internos serializables del extractor deterministico."""

from dataclasses import dataclass, field
from typing import Any

EXTRACTOR_NAME = "pliegocheck-deterministic-extractor"
EXTRACTOR_VERSION = "1.0.0"


@dataclass(frozen=True)
class ExtractionWarningData:
    code: str
    message: str
    location: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SegmentData:
    sequence: int
    segment_type: str
    text: str
    page_number: int | None = None
    paragraph_index: int | None = None
    table_index: int | None = None
    sheet_name: str | None = None
    row_start: int | None = None
    row_end: int | None = None
    line_start: int | None = None
    line_end: int | None = None
    source_location: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExtractionResultData:
    status: str
    detected_format: str
    segments: list[SegmentData] = field(default_factory=list)
    warnings: list[ExtractionWarningData] = field(default_factory=list)
    page_count: int | None = None
    sheet_count: int | None = None
    character_count: int = 0
    language_hint: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    contains_macros: bool = False


class ControlledExtractionError(Exception):
    """Error esperado y sanitizado de extraccion."""

    def __init__(self, code: str, message: str, status: str = "FAILED") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
