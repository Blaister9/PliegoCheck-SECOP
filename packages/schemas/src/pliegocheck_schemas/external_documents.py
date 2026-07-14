"""Contratos de sincronización incremental y documentos públicos SECOP."""

from enum import StrEnum
from typing import Annotated, Any
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints

EXTERNAL_DOCUMENTS_SCHEMA_VERSION = "1.0.0"

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
HttpsUrl = Annotated[str, StringConstraints(pattern=r"^https://", max_length=2083)]


class ExternalProcessSyncStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ExternalDocumentDiscoveryStatus(StrEnum):
    DISCOVERED = "DISCOVERED"
    LINK_AVAILABLE = "LINK_AVAILABLE"
    METADATA_ONLY = "METADATA_ONLY"
    UNSUPPORTED = "UNSUPPORTED"
    MISSING = "MISSING"
    ERROR = "ERROR"


class ExternalDocumentDownloadStatus(StrEnum):
    NOT_REQUESTED = "NOT_REQUESTED"
    PENDING = "PENDING"
    DOWNLOADING = "DOWNLOADING"
    DOWNLOADED = "DOWNLOADED"
    UNCHANGED = "UNCHANGED"
    UPDATED = "UPDATED"
    UNSUPPORTED = "UNSUPPORTED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


class ExternalDocumentAddendumStatus(StrEnum):
    CONFIRMED_ADDENDUM = "CONFIRMED_ADDENDUM"
    POTENTIAL_ADDENDUM = "POTENTIAL_ADDENDUM"
    NOT_ADDENDUM = "NOT_ADDENDUM"
    UNKNOWN = "UNKNOWN"


class ExternalProcessChangeEventType(StrEnum):
    PROCESS_STATUS_CHANGED = "PROCESS_STATUS_CHANGED"
    CLOSING_DATE_CHANGED = "CLOSING_DATE_CHANGED"
    ESTIMATED_VALUE_CHANGED = "ESTIMATED_VALUE_CHANGED"
    DOCUMENT_DISCOVERED = "DOCUMENT_DISCOVERED"
    DOCUMENT_UPDATED = "DOCUMENT_UPDATED"
    DOCUMENT_REMOVED_FROM_SOURCE = "DOCUMENT_REMOVED_FROM_SOURCE"
    POTENTIAL_ADDENDUM_DISCOVERED = "POTENTIAL_ADDENDUM_DISCOVERED"
    CONFIRMED_ADDENDUM_DISCOVERED = "CONFIRMED_ADDENDUM_DISCOVERED"
    DOWNLOAD_FAILED = "DOWNLOAD_FAILED"


class ExternalDocumentErrorCode(StrEnum):
    EXTERNAL_SYNC_NOT_AVAILABLE = "EXTERNAL_SYNC_NOT_AVAILABLE"
    EXTERNAL_SYNC_ALREADY_QUEUED = "EXTERNAL_SYNC_ALREADY_QUEUED"
    EXTERNAL_SYNC_NOT_FOUND = "EXTERNAL_SYNC_NOT_FOUND"
    EXTERNAL_SOURCE_UNAVAILABLE = "EXTERNAL_SOURCE_UNAVAILABLE"
    EXTERNAL_PROCESS_LINK_NOT_FOUND = "EXTERNAL_PROCESS_LINK_NOT_FOUND"
    EXTERNAL_DOCUMENT_NOT_FOUND = "EXTERNAL_DOCUMENT_NOT_FOUND"
    EXTERNAL_DOCUMENT_DOWNLOAD_UNSUPPORTED = "EXTERNAL_DOCUMENT_DOWNLOAD_UNSUPPORTED"
    EXTERNAL_DOCUMENT_URL_REJECTED = "EXTERNAL_DOCUMENT_URL_REJECTED"
    EXTERNAL_DOCUMENT_HOST_REJECTED = "EXTERNAL_DOCUMENT_HOST_REJECTED"
    EXTERNAL_DOCUMENT_TOO_LARGE = "EXTERNAL_DOCUMENT_TOO_LARGE"
    EXTERNAL_DOCUMENT_CONTENT_TYPE_REJECTED = "EXTERNAL_DOCUMENT_CONTENT_TYPE_REJECTED"
    EXTERNAL_DOCUMENT_HTML_RESPONSE = "EXTERNAL_DOCUMENT_HTML_RESPONSE"
    EXTERNAL_DOCUMENT_DOWNLOAD_FAILED = "EXTERNAL_DOCUMENT_DOWNLOAD_FAILED"
    EXTERNAL_DOCUMENT_HASH_MISMATCH = "EXTERNAL_DOCUMENT_HASH_MISMATCH"
    EXTERNAL_DOCUMENT_ALREADY_DOWNLOADED = "EXTERNAL_DOCUMENT_ALREADY_DOWNLOADED"
    EXTERNAL_DOCUMENT_VERSION_CONFLICT = "EXTERNAL_DOCUMENT_VERSION_CONFLICT"
    EXTERNAL_DOCUMENT_EXTRACTION_NOT_READY = "EXTERNAL_DOCUMENT_EXTRACTION_NOT_READY"


class ExternalProcessSyncRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    discover_documents: bool = True


class ExternalProcessSyncQueueResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    process_id: UUID
    sync_run_id: UUID
    status: ExternalProcessSyncStatus
    message: ShortText


class ExternalProcessSyncReadiness(BaseModel):
    model_config = ConfigDict(extra="forbid")

    process_id: UUID
    available: bool
    enabled: bool
    source_system: str | None
    external_process_link_id: UUID | None
    active_sync_run_id: UUID | None
    last_sync_at: AwareDatetime | None
    reason: ShortText | None


class ExternalProcessSyncRunSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    process_id: UUID
    external_process_link_id: UUID
    source_system: str
    status: ExternalProcessSyncStatus
    started_at: AwareDatetime | None
    finished_at: AwareDatetime | None
    source_updated_at: AwareDatetime | None
    metadata_changed: bool
    documents_discovered: int = Field(ge=0)
    documents_added: int = Field(ge=0)
    documents_updated: int = Field(ge=0)
    documents_unchanged: int = Field(ge=0)
    documents_failed: int = Field(ge=0)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    error_code: ExternalDocumentErrorCode | None
    error_message: ShortText | None
    created_at: AwareDatetime


class ExternalProcessChangeEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    process_id: UUID
    sync_run_id: UUID
    event_type: ExternalProcessChangeEventType
    external_document_id: UUID | None
    old_value: str | None
    new_value: str | None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: AwareDatetime


class ExternalProcessSyncRunDetail(ExternalProcessSyncRunSummary):
    input_digest: Sha256
    events: list[ExternalProcessChangeEvent] = Field(default_factory=list)


class ExternalProcessSyncRunList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    process_id: UUID
    items: list[ExternalProcessSyncRunSummary]
    total: int = Field(ge=0)


class ExternalProcessDocumentVersion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    external_document_id: UUID
    version_number: int = Field(ge=1)
    source_url: str | None
    source_updated_at: AwareDatetime | None
    reported_size_bytes: int | None = Field(default=None, ge=0)
    reported_content_type: str | None
    sha256: Sha256
    size_bytes: int = Field(gt=0)
    detected_content_type: str
    downloaded_at: AwareDatetime
    process_document_id: UUID
    previous_version_id: UUID | None
    created_at: AwareDatetime


class ExternalProcessDocumentSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    process_id: UUID
    source_system: str
    source_document_id: str
    source_document_reference: str | None
    title: ShortText
    document_type: str | None
    document_category: str | None
    source_url: str | None
    source_public_url: HttpsUrl | None
    published_at: AwareDatetime | None
    updated_at_source: AwareDatetime | None
    reported_size_bytes: int | None = Field(default=None, ge=0)
    reported_content_type: str | None
    discovery_status: ExternalDocumentDiscoveryStatus
    download_status: ExternalDocumentDownloadStatus
    addendum_status: ExternalDocumentAddendumStatus
    requires_human_review: bool
    current_version_id: UUID | None
    version_count: int = Field(ge=0)
    first_seen_at: AwareDatetime
    last_seen_at: AwareDatetime


class ExternalProcessDocumentDetail(ExternalProcessDocumentSummary):
    versions: list[ExternalProcessDocumentVersion] = Field(default_factory=list)


class ExternalProcessDocumentList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    process_id: UUID
    items: list[ExternalProcessDocumentSummary]
    total: int = Field(ge=0)


class ExternalDocumentDownloadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirm_public_download: bool


class ExternalDocumentDownloadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    process_id: UUID
    external_document_id: UUID
    status: ExternalDocumentDownloadStatus
    version_id: UUID | None
    process_document_id: UUID | None
    sha256: Sha256 | None
    message: LongText


class ExternalDocumentExtractResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    process_id: UUID
    external_document_id: UUID
    process_document_id: UUID
    extraction_job_id: UUID | None
    message: ShortText


class ExternalDocumentsContracts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sync_request: ExternalProcessSyncRequest
    sync_queue_response: ExternalProcessSyncQueueResponse
    sync_readiness: ExternalProcessSyncReadiness
    sync_summary: ExternalProcessSyncRunSummary
    sync_detail: ExternalProcessSyncRunDetail
    sync_list: ExternalProcessSyncRunList
    document_summary: ExternalProcessDocumentSummary
    document_detail: ExternalProcessDocumentDetail
    document_list: ExternalProcessDocumentList
    document_version: ExternalProcessDocumentVersion
    download_request: ExternalDocumentDownloadRequest
    download_response: ExternalDocumentDownloadResponse
    extract_response: ExternalDocumentExtractResponse
    change_event: ExternalProcessChangeEvent
