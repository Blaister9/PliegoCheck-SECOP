"""Contratos de reporte ejecutivo y paquete de decision (Microfase 9)."""

from enum import StrEnum
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints

DECISION_REPORT_SCHEMA_VERSION: Literal["1.0.0"] = "1.0.0"

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]


class DecisionReportJobStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class DecisionReportPackageStatus(StrEnum):
    DRAFT = "DRAFT"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


class DecisionReportArtifactType(StrEnum):
    EXECUTIVE_HTML = "EXECUTIVE_HTML"
    EXECUTIVE_MARKDOWN = "EXECUTIVE_MARKDOWN"
    REQUIREMENTS_MATRIX_JSON = "REQUIREMENTS_MATRIX_JSON"
    REQUIREMENTS_MATRIX_CSV = "REQUIREMENTS_MATRIX_CSV"
    EVIDENCE_INDEX_JSON = "EVIDENCE_INDEX_JSON"
    ACTIONS_JSON = "ACTIONS_JSON"
    DECISION_MANIFEST_JSON = "DECISION_MANIFEST_JSON"
    PACKAGE_MANIFEST_JSON = "PACKAGE_MANIFEST_JSON"
    PACKAGE_ZIP = "PACKAGE_ZIP"


class DecisionReportErrorCode(StrEnum):
    DECISION_REPORT_ALREADY_QUEUED = "DECISION_REPORT_ALREADY_QUEUED"
    DECISION_REPORT_ALREADY_COMPLETED = "DECISION_REPORT_ALREADY_COMPLETED"
    DECISION_REPORT_NOT_FOUND = "DECISION_REPORT_NOT_FOUND"
    DECISION_REPORT_INPUT_NOT_READY = "DECISION_REPORT_INPUT_NOT_READY"
    DECISION_REPORT_DECISION_NOT_COMPLETED = "DECISION_REPORT_DECISION_NOT_COMPLETED"
    DECISION_REPORT_TEMPLATE_NOT_FOUND = "DECISION_REPORT_TEMPLATE_NOT_FOUND"
    DECISION_REPORT_TEMPLATE_INVALID = "DECISION_REPORT_TEMPLATE_INVALID"
    DECISION_REPORT_RENDER_FAILED = "DECISION_REPORT_RENDER_FAILED"
    DECISION_REPORT_STORAGE_FAILED = "DECISION_REPORT_STORAGE_FAILED"
    DECISION_REPORT_ARTIFACT_NOT_FOUND = "DECISION_REPORT_ARTIFACT_NOT_FOUND"
    DECISION_REPORT_PACKAGE_NOT_FOUND = "DECISION_REPORT_PACKAGE_NOT_FOUND"
    DECISION_REPORT_DIGEST_MISMATCH = "DECISION_REPORT_DIGEST_MISMATCH"
    DECISION_REPORT_FAILED = "DECISION_REPORT_FAILED"


class DecisionReportArtifactMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    package_id: UUID
    artifact_type: DecisionReportArtifactType
    filename: ShortText
    content_type: ShortText
    size_bytes: int = Field(ge=0)
    sha256: Sha256
    template_version: ShortText
    source_digest: Sha256
    created_at: AwareDatetime


class DecisionReportJobSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    process_id: UUID
    decision_run_id: UUID
    status: DecisionReportJobStatus
    attempt_count: int = Field(ge=0)
    max_attempts: int = Field(gt=0)
    force: bool
    last_error_code: str | None = None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class DecisionReportPackageSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    process_id: UUID
    decision_run_id: UUID
    status: DecisionReportPackageStatus
    package_version: ShortText
    template_version: ShortText
    input_digest: Sha256
    package_digest: Sha256 | None
    artifact_count: int = Field(ge=0)
    warning_count: int = Field(ge=0)
    created_by: ShortText
    published_at: AwareDatetime | None
    error_code: str | None
    error_message: str | None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class DecisionReportSectionSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    package_id: UUID
    section_code: ShortText
    title: ShortText
    sequence: int = Field(ge=0)
    summary_payload: dict[str, Any] = Field(default_factory=dict)
    warning_codes: list[str] = Field(default_factory=list)
    created_at: AwareDatetime


class DecisionReportPackageDetail(DecisionReportPackageSummary):
    input_manifest: dict[str, Any] = Field(default_factory=dict)
    artifacts: list[DecisionReportArtifactMetadata] = Field(default_factory=list)
    sections: list[DecisionReportSectionSummary] = Field(default_factory=list)
    manifest_summary: dict[str, Any] = Field(default_factory=dict)


class DecisionReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_run_id: UUID
    force: bool = False


class DecisionReportRetryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    force: bool = True


class DecisionReportQueueResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job: DecisionReportJobSummary | None = None
    package: DecisionReportPackageSummary
    reused_existing_package: bool = False


class DecisionReportPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    package_id: UUID
    content_type: Literal["text/markdown"]
    text: str
    sha256: Sha256


class RequirementMatrixRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_id: UUID
    stable_key: str
    category: str
    scope: str
    modality: str
    description: str
    decision_finding_outcome: str
    source_domain: str
    source_run_id: UUID | None
    source_result_id: UUID | None
    requires_human_review: bool
    review_status: str | None
    evidence_count: int = Field(ge=0)
    action_count: int = Field(ge=0)
    warning_codes: list[str] = Field(default_factory=list)


class EvidenceIndexEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_id: UUID | None
    evidence_type: str
    document_id: UUID | None
    segment_id: UUID | None
    source_label: str | None
    source_location: dict[str, Any] = Field(default_factory=dict)
    document_sha256: Sha256 | None
    quoted_text: str | None
    validation_status: str | None


class DecisionActionExportRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    action_type: str
    priority: str
    status: str
    title_code: str
    description_code: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    requirement_ids: list[UUID] = Field(default_factory=list)
    finding_ids: list[UUID] = Field(default_factory=list)
    due_at: AwareDatetime | None


class DecisionReportArtifactManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: ShortText
    artifact_type: DecisionReportArtifactType
    content_type: ShortText
    size_bytes: int = Field(ge=0)
    sha256: Sha256


class DecisionReportManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    package_id: UUID
    package_version: ShortText
    input_digest: Sha256
    package_digest: Sha256 | None
    artifacts: list[DecisionReportArtifactManifest] = Field(default_factory=list)


class DecisionReportPackageList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[DecisionReportPackageSummary]
    total: int = Field(ge=0)
    limit: int = Field(gt=0)
    offset: int = Field(ge=0)


class DecisionReportContracts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0.0"] = DECISION_REPORT_SCHEMA_VERSION
    artifact: DecisionReportArtifactMetadata
    job: DecisionReportJobSummary
    package_summary: DecisionReportPackageSummary
    package_detail: DecisionReportPackageDetail
    request: DecisionReportRequest
    retry_request: DecisionReportRetryRequest
    queue_response: DecisionReportQueueResponse
    preview: DecisionReportPreview
    manifest: DecisionReportManifest
    artifact_manifest: DecisionReportArtifactManifest
    section: DecisionReportSectionSummary
    requirement_matrix_row: RequirementMatrixRow
    evidence_index_entry: EvidenceIndexEntry
    action_export_row: DecisionActionExportRow
    package_list: DecisionReportPackageList
