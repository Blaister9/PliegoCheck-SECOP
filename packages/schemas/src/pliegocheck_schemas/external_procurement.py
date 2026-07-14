"""Contratos del conector de busqueda e importacion SECOP (Microfase 16)."""

from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Any
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints, model_validator

EXTERNAL_PROCUREMENT_SCHEMA_VERSION = "1.0.0"

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]
CurrencyCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]


class ExternalProcurementSourceStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    STALE = "STALE"
    ERROR = "ERROR"
    UNSUPPORTED = "UNSUPPORTED"


class ExternalProcurementSearchStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    FAILED = "FAILED"


class ExternalProcurementImportStatus(StrEnum):
    PENDING = "PENDING"
    IMPORTED = "IMPORTED"
    SKIPPED_DUPLICATE = "SKIPPED_DUPLICATE"
    FAILED = "FAILED"


class ExternalProcurementProvider(StrEnum):
    DATOS_ABIERTOS = "datos_abiertos"


class ExternalProcurementSourceSystem(StrEnum):
    SECOP_II = "SECOP_II"
    SECOP_I = "SECOP_I"


class ExternalProcurementFieldStatus(StrEnum):
    PRESENT = "PRESENT"
    MISSING = "MISSING"
    NORMALIZED = "NORMALIZED"
    UNMAPPED = "UNMAPPED"
    CONFLICTING = "CONFLICTING"


class ExternalProcurementDocumentStatus(StrEnum):
    DOCUMENTS_NOT_AVAILABLE = "DOCUMENTS_NOT_AVAILABLE"
    DOCUMENT_LINKS_AVAILABLE = "DOCUMENT_LINKS_AVAILABLE"
    DOCUMENT_DOWNLOAD_UNSUPPORTED = "DOCUMENT_DOWNLOAD_UNSUPPORTED"
    DOCUMENT_DOWNLOAD_FAILED = "DOCUMENT_DOWNLOAD_FAILED"
    DOCUMENTS_IMPORTED = "DOCUMENTS_IMPORTED"


class ExternalProcurementErrorCode(StrEnum):
    SOURCE_DISABLED = "SOURCE_DISABLED"
    SOURCE_NOT_FOUND = "SOURCE_NOT_FOUND"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    SOURCE_TIMEOUT = "SOURCE_TIMEOUT"
    SOURCE_INVALID_RESPONSE = "SOURCE_INVALID_RESPONSE"
    RATE_LIMITED = "RATE_LIMITED"
    UNSUPPORTED_FILTER = "UNSUPPORTED_FILTER"
    SEARCH_NOT_FOUND = "SEARCH_NOT_FOUND"
    RESULT_NOT_FOUND = "RESULT_NOT_FOUND"
    IMPORT_NOT_FOUND = "IMPORT_NOT_FOUND"
    INVALID_EXTERNAL_PROCESS = "INVALID_EXTERNAL_PROCESS"
    EXTERNAL_DATABASE_ERROR = "EXTERNAL_DATABASE_ERROR"


class ExternalProcurementWarning(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: ShortText
    message: LongText
    field: ShortText | None = None


class ExternalProcurementSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_system: ExternalProcurementSourceSystem = ExternalProcurementSourceSystem.SECOP_II
    query: str | None = Field(default=None, min_length=1, max_length=200)
    entity_name: str | None = Field(default=None, min_length=1, max_length=300)
    modality: str | None = Field(default=None, min_length=1, max_length=200)
    status: str | None = Field(default=None, min_length=1, max_length=200)
    department: str | None = Field(default=None, min_length=1, max_length=200)
    municipality: str | None = Field(default=None, min_length=1, max_length=200)
    process_code: str | None = Field(default=None, min_length=1, max_length=200)
    min_value: Decimal | None = Field(default=None, ge=0)
    max_value: Decimal | None = Field(default=None, ge=0)
    published_from: AwareDatetime | None = None
    published_to: AwareDatetime | None = None
    closing_from: AwareDatetime | None = None
    closing_to: AwareDatetime | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0, le=1_000_000)

    @model_validator(mode="after")
    def validate_ranges(self) -> "ExternalProcurementSearchRequest":
        if (
            self.min_value is not None
            and self.max_value is not None
            and self.min_value > self.max_value
        ):
            raise ValueError("min_value no puede ser mayor que max_value")
        if self.published_from and self.published_to and self.published_from > self.published_to:
            raise ValueError("published_from no puede ser posterior a published_to")
        if self.closing_from and self.closing_to and self.closing_from > self.closing_to:
            raise ValueError("closing_from no puede ser posterior a closing_to")
        return self


class SecopProcessNormalized(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_system: ExternalProcurementSourceSystem
    source_dataset: ShortText
    source_process_id: ShortText
    reference: str | None = Field(default=None, max_length=500)
    title: ShortText
    description: str | None = Field(default=None, max_length=5000)
    entity_name: ShortText
    entity_nit: str | None = Field(default=None, max_length=100)
    modality: str | None = Field(default=None, max_length=500)
    status: str | None = Field(default=None, max_length=500)
    estimated_value: Decimal | None = Field(default=None, ge=0)
    currency: CurrencyCode | None = None
    publication_date: AwareDatetime | None = None
    closing_date: AwareDatetime | None = None
    department: str | None = Field(default=None, max_length=300)
    municipality: str | None = Field(default=None, max_length=300)
    source_url: str | None = Field(default=None, max_length=2083)
    documents_url: str | None = Field(default=None, max_length=2083)
    documents_status: ExternalProcurementDocumentStatus
    raw_payload_hash: Sha256
    field_statuses: dict[str, ExternalProcurementFieldStatus] = Field(default_factory=dict)
    warnings: list[ExternalProcurementWarning] = Field(default_factory=list)


class ExternalProcurementSourceSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    source_system: ExternalProcurementSourceSystem
    provider: ExternalProcurementProvider
    name: ShortText
    base_url: str
    dataset_id: ShortText
    human_url: str
    api_url: str
    status: ExternalProcurementSourceStatus
    enabled: bool
    last_checked_at: AwareDatetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: AwareDatetime
    updated_at: AwareDatetime


class ExternalProcurementSearchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    search_id: UUID
    source_id: UUID
    source_system: ExternalProcurementSourceSystem
    source_dataset: ShortText
    source_process_id: ShortText
    source_process_reference: str | None
    title: str
    entity_name: str
    modality: str | None
    status: str | None
    estimated_value: str | None
    currency: CurrencyCode | None
    publication_date: AwareDatetime | None
    closing_date: AwareDatetime | None
    department: str | None
    municipality: str | None
    source_url: str | None
    documents_status: ExternalProcurementDocumentStatus
    raw_payload_hash: Sha256
    field_statuses: dict[str, ExternalProcurementFieldStatus] = Field(default_factory=dict)
    warnings: list[ExternalProcurementWarning] = Field(default_factory=list)
    import_status: ExternalProcurementImportStatus
    process_id: UUID | None = None
    created_at: AwareDatetime


class ExternalProcurementSearchSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    source_id: UUID
    source_system: ExternalProcurementSourceSystem
    query: str | None
    filters: dict[str, Any]
    status: ExternalProcurementSearchStatus
    result_count: int = Field(ge=0)
    source_row_count: int = Field(ge=0)
    page_count: int = Field(ge=0)
    limit: int = Field(gt=0)
    offset: int = Field(ge=0)
    unsupported_filters: list[str] = Field(default_factory=list)
    warnings: list[ExternalProcurementWarning] = Field(default_factory=list)
    started_at: AwareDatetime | None
    finished_at: AwareDatetime | None
    error_code: ExternalProcurementErrorCode | None
    error_message: str | None
    created_at: AwareDatetime


class ExternalProcurementSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    search: ExternalProcurementSearchSummary
    items: list[ExternalProcurementSearchResult]


class ExternalProcurementSearchList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ExternalProcurementSearchSummary]
    total: int = Field(ge=0)
    limit: int = Field(gt=0)
    offset: int = Field(ge=0)


class ExternalProcurementResultList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    search_id: UUID
    items: list[ExternalProcurementSearchResult]
    total: int = Field(ge=0)
    limit: int = Field(gt=0)
    offset: int = Field(ge=0)


class ExternalProcurementImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_source_process_id: str | None = Field(default=None, max_length=500)


class ExternalProcurementImportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    source_result_id: UUID
    process_id: UUID
    status: ExternalProcurementImportStatus
    deduplication_key: Sha256
    imported_at: AwareDatetime | None
    created_at: AwareDatetime
    message: str


class ExternalProcurementImportList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ExternalProcurementImportResponse]
    total: int = Field(ge=0)
    limit: int = Field(gt=0)
    offset: int = Field(ge=0)


class ExternalProcurementProcessLink(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    process_id: UUID
    source_system: ExternalProcurementSourceSystem
    source_dataset: ShortText
    source_process_id: ShortText
    source_process_reference: str | None
    source_url: str | None
    documents_url: str | None
    documents_status: ExternalProcurementDocumentStatus
    external_metadata: dict[str, Any] = Field(default_factory=dict)
    imported_at: AwareDatetime
    created_at: AwareDatetime


class ExternalProcurementProcessLinkList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    process_id: UUID
    items: list[ExternalProcurementProcessLink]
    total: int = Field(ge=0)


class ExternalProcurementContracts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: ExternalProcurementSourceSummary
    search_request: ExternalProcurementSearchRequest
    search_response: ExternalProcurementSearchResponse
    search_list: ExternalProcurementSearchList
    result_list: ExternalProcurementResultList
    normalized_process: SecopProcessNormalized
    import_request: ExternalProcurementImportRequest
    import_response: ExternalProcurementImportResponse
    import_list: ExternalProcurementImportList
    process_link_list: ExternalProcurementProcessLinkList
