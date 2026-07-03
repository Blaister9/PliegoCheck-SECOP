"""Contratos de normalizacion de requisitos con evidencia trazable.

La Microfase 4 introduce el primer flujo de IA de PliegoCheck-SECOP. Estos
contratos separan tres superficies:

- salidas estructuradas del proveedor LLM;
- estado auditable de ejecuciones, lotes y trabajos;
- requisitos normalizados persistidos y su evidencia.

Ningun contrato de esta fase representa cumplimiento empresarial ni decisiones
GO / NO GO.
"""

from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints

NORMALIZED_REQUIREMENT_SCHEMA_VERSION = "2.0.0"

NonBlankStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]


class RequirementCategory(StrEnum):
    """Categorias iniciales de requisitos."""

    LEGAL = "LEGAL"
    FINANCIAL = "FINANCIAL"
    ORGANIZATIONAL = "ORGANIZATIONAL"
    EXPERIENCE = "EXPERIENCE"
    TECHNICAL = "TECHNICAL"
    WORKFORCE = "WORKFORCE"
    GUARANTEE = "GUARANTEE"
    SCHEDULE = "SCHEDULE"
    ECONOMIC = "ECONOMIC"
    OPERATIONAL = "OPERATIONAL"
    DOCUMENTARY = "DOCUMENTARY"
    RISK_AND_INELIGIBILITY = "RISK_AND_INELIGIBILITY"


class RequirementScope(StrEnum):
    PROPOSAL_SUBMISSION = "PROPOSAL_SUBMISSION"
    HABILITATING = "HABILITATING"
    SCORING = "SCORING"
    CONTRACT_EXECUTION = "CONTRACT_EXECUTION"
    INFORMATIONAL = "INFORMATIONAL"
    UNKNOWN = "UNKNOWN"


class RequirementModality(StrEnum):
    MANDATORY = "MANDATORY"
    OPTIONAL = "OPTIONAL"
    CONDITIONAL = "CONDITIONAL"
    PROHIBITED = "PROHIBITED"
    UNKNOWN = "UNKNOWN"


class RequirementCriticality(StrEnum):
    BLOCKING = "BLOCKING"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFORMATIONAL = "INFORMATIONAL"
    UNKNOWN = "UNKNOWN"


class RequirementBasis(StrEnum):
    EXPLICIT = "EXPLICIT"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"


class RequirementSubsanability(StrEnum):
    SUBSANABLE = "SUBSANABLE"
    NON_SUBSANABLE = "NON_SUBSANABLE"
    CONDITIONAL = "CONDITIONAL"
    UNKNOWN = "UNKNOWN"


class RequirementEvidenceStatus(StrEnum):
    VALIDATED = "VALIDATED"
    PARTIALLY_VALIDATED = "PARTIALLY_VALIDATED"
    REJECTED_UNSUPPORTED = "REJECTED_UNSUPPORTED"
    UNKNOWN = "UNKNOWN"


class RequirementReviewStatus(StrEnum):
    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class RequirementEvidenceRole(StrEnum):
    PRIMARY = "PRIMARY"
    SUPPORTING = "SUPPORTING"
    CONFLICTING = "CONFLICTING"


class RequirementEvidenceValidationStatus(StrEnum):
    VALID = "VALID"
    INVALID_SEGMENT = "INVALID_SEGMENT"
    QUOTE_NOT_FOUND = "QUOTE_NOT_FOUND"
    OUTSIDE_SNAPSHOT = "OUTSIDE_SNAPSHOT"
    LOCATION_MISMATCH = "LOCATION_MISMATCH"


class RequirementRelationType(StrEnum):
    INDEPENDENT = "INDEPENDENT"
    EXACT_DUPLICATE = "EXACT_DUPLICATE"
    POTENTIAL_DUPLICATE = "POTENTIAL_DUPLICATE"
    POTENTIAL_CONFLICT = "POTENTIAL_CONFLICT"
    POTENTIAL_AMENDMENT = "POTENTIAL_AMENDMENT"


class NormalizationProvider(StrEnum):
    OPENAI = "openai"
    FAKE = "fake"


class RequirementNormalizationStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class RejectedCandidateReason(StrEnum):
    SCHEMA_INVALID = "SCHEMA_INVALID"
    REJECTED_UNSUPPORTED = "REJECTED_UNSUPPORTED"
    INVALID_SEGMENT = "INVALID_SEGMENT"
    QUOTE_NOT_FOUND = "QUOTE_NOT_FOUND"
    OUTSIDE_SNAPSHOT = "OUTSIDE_SNAPSHOT"
    LOCATION_MISMATCH = "LOCATION_MISMATCH"
    FORBIDDEN_DECISION = "FORBIDDEN_DECISION"
    EXACT_DUPLICATE = "EXACT_DUPLICATE"


class NormalizationErrorCode(StrEnum):
    NORMALIZATION_DISABLED = "NORMALIZATION_DISABLED"
    OPENAI_API_KEY_MISSING = "OPENAI_API_KEY_MISSING"
    PROCESS_NOT_FOUND = "PROCESS_NOT_FOUND"
    NORMALIZATION_RUN_NOT_FOUND = "NORMALIZATION_RUN_NOT_FOUND"
    REQUIREMENT_NOT_FOUND = "REQUIREMENT_NOT_FOUND"
    NO_ELIGIBLE_EXTRACTIONS = "NO_ELIGIBLE_EXTRACTIONS"
    NO_ELIGIBLE_SEGMENTS = "NO_ELIGIBLE_SEGMENTS"
    NORMALIZATION_ALREADY_ACTIVE = "NORMALIZATION_ALREADY_ACTIVE"
    NORMALIZATION_NOT_RETRYABLE = "NORMALIZATION_NOT_RETRYABLE"
    NORMALIZATION_JOB_NOT_FOUND = "NORMALIZATION_JOB_NOT_FOUND"
    PROMPT_VERSION_NOT_FOUND = "PROMPT_VERSION_NOT_FOUND"
    PROMPT_INVALID = "PROMPT_INVALID"
    PROVIDER_CONFIGURATION_ERROR = "PROVIDER_CONFIGURATION_ERROR"
    PROVIDER_TRANSIENT_ERROR = "PROVIDER_TRANSIENT_ERROR"
    PROVIDER_RESPONSE_INVALID = "PROVIDER_RESPONSE_INVALID"
    PROVIDER_REFUSAL = "PROVIDER_REFUSAL"
    PROVIDER_INCOMPLETE = "PROVIDER_INCOMPLETE"
    EVIDENCE_VALIDATION_FAILED = "EVIDENCE_VALIDATION_FAILED"
    DATABASE_ERROR = "DATABASE_ERROR"


class SourceLocation(BaseModel):
    """Ubicacion normalizada dentro del segmento de origen."""

    model_config = ConfigDict(extra="forbid")

    page_number: int | None
    paragraph_index: int | None
    table_index: int | None
    sheet_name: str | None
    row_start: int | None
    row_end: int | None
    line_start: int | None
    line_end: int | None
    section: str | None


class ExpectedValue(BaseModel):
    """Valor exigido por el pliego cuando existe soporte explicito."""

    model_config = ConfigDict(extra="forbid")

    value: str | int | float | bool | None
    unit: str | None
    raw_text: str | None


class RequirementCandidateEvidence(BaseModel):
    """Evidencia propuesta por el agente para un candidato."""

    model_config = ConfigDict(extra="forbid")

    segment_id: UUID
    evidence_role: RequirementEvidenceRole
    quoted_text: ShortText
    quote_start: int | None = Field(ge=0)
    quote_end: int | None = Field(ge=0)
    source_location: SourceLocation


class RequirementCandidate(BaseModel):
    """Candidato producido por RequirementNormalizationAgent."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: NonBlankStr
    category: RequirementCategory
    scope: RequirementScope
    modality: RequirementModality
    description: ShortText
    condition_text: str | None
    expected_value: ExpectedValue | None
    criticality: RequirementCriticality
    criticality_basis: RequirementBasis
    subsanability: RequirementSubsanability
    subsanability_basis: RequirementBasis
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[RequirementCandidateEvidence]
    requires_human_review: bool
    uncertainty_reason: str | None


class RequirementNormalizationAgentOutput(BaseModel):
    """Structured Output estricto de RequirementNormalizationAgent."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["2.0.0"]
    agent: Literal["RequirementNormalizationAgent"]
    prompt_version: NonBlankStr
    process_id: UUID
    batch_index: int = Field(ge=0)
    candidates: list[RequirementCandidate]
    warnings: list[str]


class RequirementRelationProposal(BaseModel):
    """Relacion propuesta por RequirementConsolidationAgent."""

    model_config = ConfigDict(extra="forbid")

    source_candidate_id: NonBlankStr
    target_candidate_id: NonBlankStr
    relation_type: RequirementRelationType
    explanation: ShortText
    evidence_segment_ids: list[UUID]
    confidence: float = Field(ge=0.0, le=1.0)
    requires_human_review: bool


class RequirementConsolidationAgentOutput(BaseModel):
    """Structured Output estricto de RequirementConsolidationAgent."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["2.0.0"]
    agent: Literal["RequirementConsolidationAgent"]
    prompt_version: NonBlankStr
    process_id: UUID
    relations: list[RequirementRelationProposal]
    warnings: list[str]


class NormalizedRequirement(BaseModel):
    """Requisito persistido tras validacion deterministica de evidencia."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    process_id: UUID
    normalization_run_id: UUID
    stable_key: Sha256
    category: RequirementCategory
    scope: RequirementScope
    modality: RequirementModality
    description: ShortText
    condition_text: str | None
    expected_value: ExpectedValue | None
    criticality: RequirementCriticality
    criticality_basis: RequirementBasis
    subsanability: RequirementSubsanability
    subsanability_basis: RequirementBasis
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_status: RequirementEvidenceStatus
    review_status: RequirementReviewStatus
    requires_human_review: bool
    is_active: bool
    created_at: AwareDatetime
    updated_at: AwareDatetime


class RequirementEvidence(BaseModel):
    """Evidencia validada asociada a un requisito persistido."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    requirement_id: UUID
    extraction_id: UUID
    segment_id: UUID
    evidence_role: RequirementEvidenceRole
    quoted_text: ShortText
    quote_start: int | None
    quote_end: int | None
    source_location: SourceLocation
    validation_status: RequirementEvidenceValidationStatus
    created_at: AwareDatetime


class RequirementRelation(BaseModel):
    """Relacion entre requisitos que requiere revision humana cuando es potencial."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    process_id: UUID
    normalization_run_id: UUID
    source_requirement_id: UUID
    target_requirement_id: UUID
    relation_type: RequirementRelationType
    explanation: str
    confidence: float = Field(ge=0.0, le=1.0)
    requires_human_review: bool
    created_at: AwareDatetime


class RejectedRequirementCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    run_id: UUID
    batch_id: UUID | None
    candidate_id: str | None
    rejection_reason: RejectedCandidateReason
    rejection_message: str
    raw_candidate: dict[str, object]
    created_at: AwareDatetime


class PromptVersionSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    prompt_name: str
    semantic_version: str
    content_sha256: Sha256
    provider: str
    is_active: bool
    created_at: AwareDatetime


class NormalizationJobSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    process_id: UUID
    run_id: UUID | None
    status: RequirementNormalizationStatus
    priority: int
    attempt_count: int
    max_attempts: int
    force: bool
    available_at: AwareDatetime
    started_at: AwareDatetime | None
    finished_at: AwareDatetime | None
    last_error_code: str | None
    last_error_message: str | None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class NormalizationBatchSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    run_id: UUID
    batch_index: int
    status: RequirementNormalizationStatus
    segment_ids: list[UUID]
    input_digest: Sha256
    provider_response_id: str | None
    candidate_count: int
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int
    started_at: AwareDatetime | None
    finished_at: AwareDatetime | None
    error_code: str | None
    error_message: str | None
    created_at: AwareDatetime


class NormalizationRunSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    job_id: UUID
    process_id: UUID
    status: RequirementNormalizationStatus
    provider: NormalizationProvider
    model: str
    reasoning_effort: str
    prompt_version_id: UUID
    consolidation_prompt_version_id: UUID
    input_digest: Sha256
    source_extraction_ids: list[UUID]
    segment_count: int
    batch_count: int
    candidate_count: int
    accepted_requirement_count: int
    rejected_candidate_count: int
    warning_count: int
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int
    provider_response_ids: list[str]
    started_at: AwareDatetime | None
    finished_at: AwareDatetime | None
    error_code: str | None
    error_message: str | None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class NormalizationRunDetail(NormalizationRunSummary):
    prompt_version: PromptVersionSummary
    consolidation_prompt_version: PromptVersionSummary
    batches: list[NormalizationBatchSummary]
    warnings: list[str]
    documents_used: list[dict[str, object]]
    omitted_documents: list[dict[str, object]]


class NormalizationRunList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    process_id: UUID
    total: int = Field(ge=0)
    limit: int = Field(gt=0)
    offset: int = Field(ge=0)
    items: list[NormalizationRunSummary]


class NormalizationCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    force: bool = False
    document_ids: list[UUID] | None = None


class NormalizationCreateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job: NormalizationJobSummary
    run: NormalizationRunSummary


class NormalizationRetryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job: NormalizationJobSummary
    run: NormalizationRunSummary
    message: str


class RequirementList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    process_id: UUID
    total: int = Field(ge=0)
    limit: int = Field(gt=0)
    offset: int = Field(ge=0)
    items: list[NormalizedRequirement]


class RequirementDetail(NormalizedRequirement):
    evidence: list[RequirementEvidence]
    relations: list[RequirementRelation]
    run: NormalizationRunSummary
    prompt_version: PromptVersionSummary
    documents: list[dict[str, object]]


class RequirementNormalizationContracts(BaseModel):
    """Contenedor para generar JSON Schema conjunto de Microfase 4."""

    model_config = ConfigDict(extra="forbid")

    agent_output: RequirementNormalizationAgentOutput
    consolidation_output: RequirementConsolidationAgentOutput
    normalized_requirement: NormalizedRequirement
    requirement_evidence: RequirementEvidence
    requirement_relation: RequirementRelation
    rejected_candidate: RejectedRequirementCandidate
    prompt_version: PromptVersionSummary
    job_summary: NormalizationJobSummary
    batch_summary: NormalizationBatchSummary
    run_summary: NormalizationRunSummary
    run_detail: NormalizationRunDetail
    run_list: NormalizationRunList
    create_request: NormalizationCreateRequest
    create_response: NormalizationCreateResponse
    retry_response: NormalizationRetryResponse
    requirement_list: RequirementList
    requirement_detail: RequirementDetail
