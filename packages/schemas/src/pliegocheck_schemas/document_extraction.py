"""Contratos de inventario y extraccion documental deterministica."""

from enum import StrEnum
from typing import Annotated, Any
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints

DOCUMENT_EXTRACTION_SCHEMA_VERSION = "1.0.0"

Sha256 = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]


class DocumentProcessingStatus(StrEnum):
    NOT_QUEUED = "NOT_QUEUED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    NEEDS_OCR = "NEEDS_OCR"
    UNSUPPORTED = "UNSUPPORTED"
    ENCRYPTED = "ENCRYPTED"
    FAILED = "FAILED"


class DocumentProcessingJobStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class DocumentProcessingJobType(StrEnum):
    EXTRACT_DOCUMENT = "EXTRACT_DOCUMENT"


class DocumentExtractionStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    NEEDS_OCR = "NEEDS_OCR"
    UNSUPPORTED = "UNSUPPORTED"
    ENCRYPTED = "ENCRYPTED"
    FAILED = "FAILED"


class ExtractedSegmentType(StrEnum):
    PAGE_TEXT = "PAGE_TEXT"
    PARAGRAPH = "PARAGRAPH"
    TABLE = "TABLE"
    SHEET_ROW = "SHEET_ROW"
    TEXT_LINES = "TEXT_LINES"


class ExtractionErrorCode(StrEnum):
    PROCESSING_JOB_NOT_FOUND = "PROCESSING_JOB_NOT_FOUND"
    EXTRACTION_NOT_FOUND = "EXTRACTION_NOT_FOUND"
    EXTRACTION_ALREADY_QUEUED = "EXTRACTION_ALREADY_QUEUED"
    EXTRACTION_ALREADY_COMPLETED = "EXTRACTION_ALREADY_COMPLETED"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    ENCRYPTED_DOCUMENT = "ENCRYPTED_DOCUMENT"
    NEEDS_OCR = "NEEDS_OCR"
    SOURCE_FILE_NOT_FOUND = "SOURCE_FILE_NOT_FOUND"
    SOURCE_HASH_MISMATCH = "SOURCE_HASH_MISMATCH"
    EXTRACTION_TIMEOUT = "EXTRACTION_TIMEOUT"
    EXTRACTION_LIMIT_EXCEEDED = "EXTRACTION_LIMIT_EXCEEDED"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    DATABASE_ERROR = "DATABASE_ERROR"


class ExtractionWarning(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    location: dict[str, Any] = Field(default_factory=dict)


class ExtractionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    force: bool = False


class ExtractionRetryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: UUID
    job_id: UUID | None = None
    processing_status: DocumentProcessingStatus
    message: str


class DocumentExtractionSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    document_id: UUID
    job_id: UUID
    source_sha256: Sha256
    extractor_name: str
    extractor_version: str
    status: DocumentExtractionStatus
    detected_format: str
    page_count: int | None = Field(default=None, ge=0)
    sheet_count: int | None = Field(default=None, ge=0)
    segment_count: int = Field(ge=0)
    character_count: int = Field(ge=0)
    language_hint: str | None = None
    warnings: list[ExtractionWarning] = Field(default_factory=list)
    error_code: ExtractionErrorCode | None = None
    error_message: str | None = None
    started_at: AwareDatetime | None = None
    finished_at: AwareDatetime | None = None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class DocumentInventoryItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: UUID
    original_filename: str
    document_type: str
    extension: str
    size_bytes: int = Field(gt=0)
    sha256: Sha256
    declared_content_type: str | None
    detected_content_type: str | None
    upload_status: str
    processing_status: DocumentProcessingStatus
    detected_format: str | None = None
    page_count: int | None = Field(default=None, ge=0)
    sheet_count: int | None = Field(default=None, ge=0)
    has_text: bool = False
    is_encrypted: bool = False
    needs_ocr: bool = False
    contains_macros: bool = False
    segment_count: int = Field(ge=0)
    character_count: int = Field(ge=0)
    warnings: list[ExtractionWarning] = Field(default_factory=list)
    latest_extraction: DocumentExtractionSummary | None = None
    created_at: AwareDatetime


class ProcessInventory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    process_id: UUID
    total: int = Field(ge=0)
    documents: list[DocumentInventoryItem]


class ExtractedSegment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    extraction_id: UUID
    sequence: int = Field(ge=1)
    segment_type: ExtractedSegmentType
    text: Annotated[str, StringConstraints(min_length=1)]
    page_number: int | None = Field(default=None, ge=1)
    paragraph_index: int | None = Field(default=None, ge=1)
    table_index: int | None = Field(default=None, ge=1)
    sheet_name: str | None = None
    row_start: int | None = Field(default=None, ge=1)
    row_end: int | None = Field(default=None, ge=1)
    line_start: int | None = Field(default=None, ge=1)
    line_end: int | None = Field(default=None, ge=1)
    source_location: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: AwareDatetime


class ExtractedSegmentList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    extraction_id: UUID
    total: int = Field(ge=0)
    limit: int = Field(gt=0)
    offset: int = Field(ge=0)
    segments: list[ExtractedSegment]


class DocumentExtractionDetail(DocumentExtractionSummary):
    segments_preview: list[ExtractedSegment] = Field(default_factory=list)


class ProcessingJobSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    document_id: UUID
    job_type: DocumentProcessingJobType
    status: DocumentProcessingJobStatus
    priority: int
    attempt_count: int = Field(ge=0)
    max_attempts: int = Field(gt=0)
    available_at: AwareDatetime
    started_at: AwareDatetime | None
    finished_at: AwareDatetime | None
    locked_at: AwareDatetime | None
    locked_by: str | None
    last_error_code: str | None
    last_error_message: str | None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class DocumentExtractionContracts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    inventory_item: DocumentInventoryItem
    process_inventory: ProcessInventory
    extraction_summary: DocumentExtractionSummary
    extraction_detail: DocumentExtractionDetail
    extracted_segment: ExtractedSegment
    extracted_segment_list: ExtractedSegmentList
    extraction_warning: ExtractionWarning
    extraction_request: ExtractionRequest
    extraction_retry_response: ExtractionRetryResponse
    processing_job_summary: ProcessingJobSummary
