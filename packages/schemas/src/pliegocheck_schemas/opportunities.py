"""Contratos de bandeja deterministica de oportunidades (Microfase 18)."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Any
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints

from .external_procurement import ExternalProcurementSearchRequest, ExternalProcurementSourceSystem

OPPORTUNITIES_SCHEMA_VERSION = "1.0.0"
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]


class OpportunityDiscoveryStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class OpportunityAnalysisLevel(StrEnum):
    METADATA_SCREENING = "METADATA_SCREENING"
    DOCUMENT_SCREENING = "DOCUMENT_SCREENING"
    DEEP_ANALYSIS = "DEEP_ANALYSIS"


class OpportunityOutcome(StrEnum):
    REVISAR_PRIMERO = "REVISAR_PRIMERO"
    OPORTUNIDAD_POTENCIAL = "OPORTUNIDAD_POTENCIAL"
    REQUIERE_ALIADO = "REQUIERE_ALIADO"
    INFORMACION_INSUFICIENTE = "INFORMACION_INSUFICIENTE"
    POCO_COMPATIBLE = "POCO_COMPATIBLE"
    DESCARTAR = "DESCARTAR"


class OpportunityUrgencyStatus(StrEnum):
    CLOSED = "CLOSED"
    EXPIRED = "EXPIRED"
    CRITICAL = "CRITICAL"
    URGENT = "URGENT"
    NORMAL = "NORMAL"
    LONG_HORIZON = "LONG_HORIZON"
    UNKNOWN = "UNKNOWN"


class OpportunityComponent(StrEnum):
    RELEVANCE = "RELEVANCE"
    UNSPSC_MATCH = "UNSPSC_MATCH"
    EXPERIENCE_MATCH = "EXPERIENCE_MATCH"
    FINANCIAL_FIT = "FINANCIAL_FIT"
    TECHNICAL_FIT = "TECHNICAL_FIT"
    LEGAL_READINESS = "LEGAL_READINESS"
    GEOGRAPHIC_FIT = "GEOGRAPHIC_FIT"
    VALUE_FIT = "VALUE_FIT"
    DEADLINE_URGENCY = "DEADLINE_URGENCY"
    DOCUMENT_READINESS = "DOCUMENT_READINESS"
    INFORMATION_COMPLETENESS = "INFORMATION_COMPLETENESS"
    PARTNER_NEED = "PARTNER_NEED"


class OpportunityComponentStatus(StrEnum):
    STRONG_MATCH = "STRONG_MATCH"
    MATCH = "MATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    MISMATCH = "MISMATCH"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    CONFLICTING = "CONFLICTING"


class OpportunityReviewAction(StrEnum):
    ACKNOWLEDGE = "ACKNOWLEDGE"
    SHORTLIST = "SHORTLIST"
    DISMISS = "DISMISS"
    SEEK_PARTNER = "SEEK_PARTNER"
    REQUEST_DEEP_ANALYSIS = "REQUEST_DEEP_ANALYSIS"


class OpportunityErrorCode(StrEnum):
    COMPANY_SNAPSHOT_REQUIRED = "COMPANY_SNAPSHOT_REQUIRED"
    COMPANY_SNAPSHOT_NOT_PUBLISHED = "COMPANY_SNAPSHOT_NOT_PUBLISHED"
    DISCOVERY_RUN_NOT_FOUND = "DISCOVERY_RUN_NOT_FOUND"
    OPPORTUNITY_NOT_FOUND = "OPPORTUNITY_NOT_FOUND"
    INVALID_POLICY = "INVALID_POLICY"
    DEEP_ANALYSIS_BLOCKED = "DEEP_ANALYSIS_BLOCKED"
    INVALID_FILTER = "INVALID_FILTER"


class OpportunityAssessmentEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID | None = None
    evidence_type: ShortText
    entity_type: ShortText
    entity_id: UUID | None = None
    source_reference: ShortText | None = None
    excerpt: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OpportunityAssessmentComponentDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID | None = None
    component: OpportunityComponent
    status: OpportunityComponentStatus
    score: Decimal = Field(ge=0, le=100)
    weight: Decimal = Field(ge=0, le=1)
    weighted_score: Decimal = Field(ge=0, le=100)
    reason_code: ShortText
    explanation: str = Field(max_length=2000)
    explanation_parameters: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    evidence: list[OpportunityAssessmentEvidence] = Field(default_factory=list)


class OpportunityDiscoveryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company_profile_id: UUID
    company_snapshot_id: UUID
    search_requests: list[ExternalProcurementSearchRequest] = Field(
        default_factory=list, max_length=2
    )
    candidate_ids: list[UUID] = Field(default_factory=list, max_length=100)
    effective_at: AwareDatetime | None = None
    force: bool = False


class OpportunityDiscoveryRunSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    company_profile_id: UUID
    company_snapshot_id: UUID
    policy_version: ShortText
    policy_hash: Sha256
    status: OpportunityDiscoveryStatus
    effective_at: AwareDatetime
    input_digest: Sha256
    candidate_count: int = Field(ge=0)
    assessed_count: int = Field(ge=0)
    warning_count: int = Field(ge=0)
    started_at: AwareDatetime | None = None
    finished_at: AwareDatetime | None = None
    created_at: AwareDatetime


class OpportunityCandidateSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    discovery_run_id: UUID
    external_search_result_id: UUID
    process_id: UUID | None = None
    source_system: ExternalProcurementSourceSystem
    source_process_id: str
    source_reference: str | None = None
    title: str
    entity_name: str
    modality: str | None = None
    source_status: str | None = None
    publication_date: AwareDatetime | None = None
    closing_date: AwareDatetime | None = None
    estimated_value: Decimal | None = None
    currency: str | None = None
    department: str | None = None
    municipality: str | None = None
    document_status: str
    created_at: AwareDatetime


class OpportunityAssessmentSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    candidate_id: UUID
    company_snapshot_id: UUID
    policy_version: str
    policy_hash: Sha256
    analysis_level: OpportunityAnalysisLevel
    outcome: OpportunityOutcome
    compatibility_score: Decimal = Field(ge=0, le=100)
    urgency_score: Decimal = Field(ge=0, le=100)
    information_completeness: Decimal = Field(ge=0, le=100)
    days_remaining: Decimal | None = None
    urgency_status: OpportunityUrgencyStatus
    requires_human_review: bool
    input_digest: Sha256
    summary: str
    warnings: list[str] = Field(default_factory=list)
    missing_information: dict[str, list[str]] = Field(default_factory=dict)
    partner_reasons: list[dict[str, Any]] = Field(default_factory=list)
    effective_at: AwareDatetime
    created_at: AwareDatetime


class OpportunityAssessmentDetail(OpportunityAssessmentSummary):
    candidate: OpportunityCandidateSummary
    components: list[OpportunityAssessmentComponentDetail]
    latest_review_action: OpportunityReviewAction | None = None


class OpportunityDiscoveryRunDetail(OpportunityDiscoveryRunSummary):
    candidates: list[OpportunityAssessmentDetail] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class OpportunityDiscoveryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run: OpportunityDiscoveryRunSummary
    reused: bool = False


class OpportunityInboxFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company_snapshot_id: UUID | None = None
    source_system: ExternalProcurementSourceSystem | None = None
    outcome: OpportunityOutcome | None = None
    urgency: OpportunityUrgencyStatus | None = None
    entity: str | None = Field(default=None, max_length=200)
    department: str | None = Field(default=None, max_length=200)
    municipality: str | None = Field(default=None, max_length=200)
    modality: str | None = Field(default=None, max_length=200)
    min_value: Decimal | None = Field(default=None, ge=0)
    max_value: Decimal | None = Field(default=None, ge=0)
    closing_from: datetime | None = None
    closing_to: datetime | None = None
    document_status: str | None = None
    analysis_level: OpportunityAnalysisLevel | None = None
    review_action: OpportunityReviewAction | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort: str = Field(
        default="priority",
        pattern="^(priority|compatibility|urgency|closing_date|publication_date|value)$",
    )


class OpportunityInboxResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[OpportunityAssessmentDetail]
    total: int = Field(ge=0)
    limit: int = Field(gt=0)
    offset: int = Field(ge=0)
    disclaimer: str


class OpportunityReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: OpportunityReviewAction
    reason: str | None = Field(default=None, max_length=2000)


class OpportunityReviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    assessment_id: UUID
    action: OpportunityReviewAction
    previous_action: OpportunityReviewAction | None = None
    created_at: AwareDatetime


class OpportunityReadiness(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ready: bool
    companies_count: int = Field(ge=0)
    published_snapshots_count: int = Field(ge=0)
    policy_version: str
    policy_hash: Sha256
    reasons: list[str] = Field(default_factory=list)


class OpportunityDeepAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    opportunity_id: UUID
    process_id: UUID | None = None
    steps_ready: list[str] = Field(default_factory=list)
    steps_queued: list[str] = Field(default_factory=list)
    steps_blocked: list[str] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)


class OpportunityContracts(BaseModel):
    model_config = ConfigDict(extra="forbid")
    discovery_request: OpportunityDiscoveryRequest
    discovery_response: OpportunityDiscoveryResponse
    discovery_run_summary: OpportunityDiscoveryRunSummary
    discovery_run_detail: OpportunityDiscoveryRunDetail
    candidate_summary: OpportunityCandidateSummary
    assessment_summary: OpportunityAssessmentSummary
    assessment_detail: OpportunityAssessmentDetail
    assessment_component: OpportunityAssessmentComponentDetail
    assessment_evidence: OpportunityAssessmentEvidence
    review_request: OpportunityReviewRequest
    review_response: OpportunityReviewResponse
    inbox_filters: OpportunityInboxFilters
    inbox_response: OpportunityInboxResponse
    readiness: OpportunityReadiness
    deep_analysis: OpportunityDeepAnalysisResponse
