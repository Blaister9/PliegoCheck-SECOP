"""Contratos de evaluadores especializados deterministas (Microfase 8)."""

from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints, model_validator

SPECIALIZED_EVALUATION_SCHEMA_VERSION: Literal["1.0.0"] = "1.0.0"

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]


class SpecializedEvaluationDomain(StrEnum):
    LEGAL = "LEGAL"
    EXPERIENCE = "EXPERIENCE"
    TECHNICAL = "TECHNICAL"
    WORKFORCE = "WORKFORCE"
    DOCUMENTARY = "DOCUMENTARY"
    GUARANTEE = "GUARANTEE"
    OPERATIONAL = "OPERATIONAL"
    ORGANIZATIONAL = "ORGANIZATIONAL"
    RISK = "RISK"


class SpecializedEvaluationJobStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class SpecializedEvaluationRunStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class SpecializedEvaluationResultStatus(StrEnum):
    COMPLIES = "COMPLIES"
    DOES_NOT_COMPLY = "DOES_NOT_COMPLY"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"


class SpecializedEvaluationReviewStatus(StrEnum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    OVERRIDDEN = "OVERRIDDEN"
    REJECTED = "REJECTED"


class SpecializedRuleType(StrEnum):
    DOCUMENT_EXISTS = "DOCUMENT_EXISTS"
    REGISTRATION_EXISTS = "REGISTRATION_EXISTS"
    REGISTRATION_VALID = "REGISTRATION_VALID"
    CERTIFICATION_EXISTS = "CERTIFICATION_EXISTS"
    CERTIFICATION_VALID = "CERTIFICATION_VALID"
    EXPERIENCE_EXISTS = "EXPERIENCE_EXISTS"
    EXPERIENCE_COUNT = "EXPERIENCE_COUNT"
    EXPERIENCE_VALUE = "EXPERIENCE_VALUE"
    EXPERIENCE_DURATION = "EXPERIENCE_DURATION"
    EXPERIENCE_UNSPSC = "EXPERIENCE_UNSPSC"
    EXPERIENCE_ACTIVITY = "EXPERIENCE_ACTIVITY"
    PERSON_ROLE_EXISTS = "PERSON_ROLE_EXISTS"
    PERSON_CREDENTIAL_EXISTS = "PERSON_CREDENTIAL_EXISTS"
    PERSON_EXPERIENCE_YEARS = "PERSON_EXPERIENCE_YEARS"
    CAPABILITY_EXISTS = "CAPABILITY_EXISTS"
    CAPABILITY_VALUE = "CAPABILITY_VALUE"
    COVERAGE_EXISTS = "COVERAGE_EXISTS"
    COMPOSITE_ALL = "COMPOSITE_ALL"
    COMPOSITE_ANY = "COMPOSITE_ANY"
    INFORMATIONAL = "INFORMATIONAL"
    UNSUPPORTED = "UNSUPPORTED"


class SpecializedRuleMappingStatus(StrEnum):
    MAPPED = "MAPPED"
    PARTIALLY_MAPPED = "PARTIALLY_MAPPED"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"
    INVALID = "INVALID"


class SpecializedOperator(StrEnum):
    EXISTS = "EXISTS"
    NOT_EXISTS = "NOT_EXISTS"
    EQUAL = "EQUAL"
    NOT_EQUAL = "NOT_EQUAL"
    CONTAINS = "CONTAINS"
    GREATER_THAN = "GREATER_THAN"
    GREATER_THAN_OR_EQUAL = "GREATER_THAN_OR_EQUAL"
    LESS_THAN = "LESS_THAN"
    LESS_THAN_OR_EQUAL = "LESS_THAN_OR_EQUAL"
    BETWEEN_INCLUSIVE = "BETWEEN_INCLUSIVE"
    IN_SET = "IN_SET"
    ALL_OF = "ALL_OF"
    ANY_OF = "ANY_OF"


class SpecializedEvidenceValidationStatus(StrEnum):
    VERIFIED = "VERIFIED"
    SUPPORTED = "SUPPORTED"
    DECLARED_ONLY = "DECLARED_ONLY"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"
    CONFLICTING = "CONFLICTING"
    MISSING = "MISSING"


class SpecializedDataUsability(StrEnum):
    VERIFIED = "VERIFIED"
    SUPPORTED = "SUPPORTED"
    DECLARED_ONLY = "DECLARED_ONLY"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"
    CONFLICTING = "CONFLICTING"
    MISSING = "MISSING"


class SpecializedRuleSourceBasis(StrEnum):
    EXPLICIT_EXPECTED_VALUE = "EXPLICIT_EXPECTED_VALUE"
    EXPLICIT_DESCRIPTION = "EXPLICIT_DESCRIPTION"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"
    UNKNOWN = "UNKNOWN"


class SpecializedExplanationCode(StrEnum):
    REQUIREMENT_COMPLIES = "REQUIREMENT_COMPLIES"
    REQUIREMENT_NOT_MET = "REQUIREMENT_NOT_MET"
    REQUIREMENT_PARTIAL = "REQUIREMENT_PARTIAL"
    RULE_AMBIGUOUS = "RULE_AMBIGUOUS"
    RULE_UNSUPPORTED = "RULE_UNSUPPORTED"
    DATA_MISSING = "DATA_MISSING"
    DECLARED_ONLY_NOT_ACCEPTED = "DECLARED_ONLY_NOT_ACCEPTED"
    EVIDENCE_EXPIRED = "EVIDENCE_EXPIRED"
    EVIDENCE_REJECTED = "EVIDENCE_REJECTED"
    EVIDENCE_CONFLICT = "EVIDENCE_CONFLICT"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"
    ACTIVITY_NOT_COMPARABLE = "ACTIVITY_NOT_COMPARABLE"
    UNSPSC_NOT_COMPARABLE = "UNSPSC_NOT_COMPARABLE"
    CONSORTIUM_PERCENTAGE_MISSING = "CONSORTIUM_PERCENTAGE_MISSING"
    RECORD_NOT_COMPLETED = "RECORD_NOT_COMPLETED"
    NOT_APPLICABLE_DOMAIN = "NOT_APPLICABLE_DOMAIN"


class SpecializedErrorCode(StrEnum):
    SPECIALIZED_EVALUATION_ALREADY_QUEUED = "SPECIALIZED_EVALUATION_ALREADY_QUEUED"
    SPECIALIZED_EVALUATION_ALREADY_COMPLETED = "SPECIALIZED_EVALUATION_ALREADY_COMPLETED"
    SPECIALIZED_EVALUATION_NOT_FOUND = "SPECIALIZED_EVALUATION_NOT_FOUND"
    SPECIALIZED_EVALUATION_INPUT_NOT_READY = "SPECIALIZED_EVALUATION_INPUT_NOT_READY"
    SPECIALIZED_REQUIREMENTS_NOT_FOUND = "SPECIALIZED_REQUIREMENTS_NOT_FOUND"
    SPECIALIZED_RULE_AMBIGUOUS = "SPECIALIZED_RULE_AMBIGUOUS"
    SPECIALIZED_RULE_UNSUPPORTED = "SPECIALIZED_RULE_UNSUPPORTED"
    SPECIALIZED_DATA_MISSING = "SPECIALIZED_DATA_MISSING"
    SPECIALIZED_EVIDENCE_CONFLICT = "SPECIALIZED_EVIDENCE_CONFLICT"
    SPECIALIZED_SNAPSHOT_NOT_PUBLISHED = "SPECIALIZED_SNAPSHOT_NOT_PUBLISHED"
    SPECIALIZED_INPUT_MISMATCH = "SPECIALIZED_INPUT_MISMATCH"
    SPECIALIZED_EVALUATION_FAILED = "SPECIALIZED_EVALUATION_FAILED"
    INVALID_SPECIALIZED_OVERRIDE = "INVALID_SPECIALIZED_OVERRIDE"
    SPECIALIZED_RESULT_NOT_FOUND = "SPECIALIZED_RESULT_NOT_FOUND"
    DATABASE_ERROR = "DATABASE_ERROR"


class SpecializedRequirementRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    requirement_id: UUID
    normalization_run_id: UUID
    domain: SpecializedEvaluationDomain
    rule_type: SpecializedRuleType
    subject: str | None
    operator: SpecializedOperator | None
    expected_value: str | None = None
    expected_min_value: Decimal | None = None
    expected_max_value: Decimal | None = None
    unit: str | None = None
    currency: str | None = None
    period_policy: str | None = None
    condition_group: dict[str, Any] = Field(default_factory=dict)
    source_basis: SpecializedRuleSourceBasis
    mapping_status: SpecializedRuleMappingStatus
    mapping_warnings: list[str] = Field(default_factory=list)
    requires_human_review: bool = False
    manual_override_payload: dict[str, Any] = Field(default_factory=dict)
    version: int = Field(gt=0)
    is_manual_override: bool = False
    created_at: AwareDatetime
    updated_at: AwareDatetime


class SpecializedRequirementRuleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domain: SpecializedEvaluationDomain | None = None
    rule_type: SpecializedRuleType | None = None
    subject: str | None = None
    operator: SpecializedOperator | None = None
    expected_value: str | None = None
    expected_min_value: Decimal | None = None
    expected_max_value: Decimal | None = None
    unit: str | None = None
    currency: str | None = None
    period_policy: str | None = None
    condition_group: dict[str, Any] | None = None
    mapping_warnings: list[str] | None = None
    requires_human_review: bool | None = None
    override_reason: ShortText | None = None


class SpecializedEvaluationEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    result_id: UUID
    evidence_type: str
    company_evidence_link_id: UUID | None = None
    company_evidence_document_id: UUID | None = None
    requirement_evidence_id: UUID | None = None
    extracted_segment_id: UUID | None = None
    quoted_text: str | None = None
    source_location: dict[str, Any] = Field(default_factory=dict)
    validation_status: SpecializedEvidenceValidationStatus
    created_at: AwareDatetime


class SpecializedEvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    run_id: UUID
    requirement_id: UUID
    specialized_rule_id: UUID | None
    domain: SpecializedEvaluationDomain
    status: SpecializedEvaluationResultStatus
    rule_type: SpecializedRuleType
    subject: str | None
    operator: SpecializedOperator | None
    expected_value: str | None = None
    actual_value: str | None = None
    unit: str | None = None
    source_record_type: str | None = None
    source_record_id: UUID | None = None
    explanation_code: SpecializedExplanationCode
    explanation_parameters: dict[str, Any] = Field(default_factory=dict)
    requires_human_review: bool = False
    review_status: SpecializedEvaluationReviewStatus = SpecializedEvaluationReviewStatus.PENDING
    reviewed_status: SpecializedEvaluationResultStatus | None = None
    review_notes: str | None = None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class SpecializedEvaluationResultDetail(SpecializedEvaluationResult):
    requirement: dict[str, Any] = Field(default_factory=dict)
    rule: SpecializedRequirementRule | None = None
    evidence: list[SpecializedEvaluationEvidence] = Field(default_factory=list)
    reviews: list[dict[str, Any]] = Field(default_factory=list)


class SpecializedEvaluationJobSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    process_id: UUID
    normalization_run_id: UUID
    company_id: UUID
    company_profile_snapshot_id: UUID
    domain: SpecializedEvaluationDomain
    status: SpecializedEvaluationJobStatus
    attempt_count: int = Field(ge=0)
    max_attempts: int = Field(gt=0)
    force: bool
    last_error_code: str | None = None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class SpecializedEvaluationRunSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    job_id: UUID
    process_id: UUID
    normalization_run_id: UUID
    company_id: UUID
    company_profile_snapshot_id: UUID
    domain: SpecializedEvaluationDomain
    status: SpecializedEvaluationRunStatus
    input_digest: Sha256
    rule_version: ShortText
    requirement_count: int = Field(ge=0)
    evaluated_count: int = Field(ge=0)
    complies_count: int = Field(ge=0)
    does_not_comply_count: int = Field(ge=0)
    partial_count: int = Field(ge=0)
    unknown_count: int = Field(ge=0)
    not_applicable_count: int = Field(ge=0)
    conflicting_count: int = Field(ge=0)
    warning_count: int = Field(ge=0)
    started_at: AwareDatetime | None
    finished_at: AwareDatetime | None
    error_code: str | None
    error_message: str | None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class SpecializedEvaluationRunDetail(SpecializedEvaluationRunSummary):
    input_manifest: dict[str, Any]
    job: SpecializedEvaluationJobSummary | None = None
    rules: list[SpecializedRequirementRule] = Field(default_factory=list)
    results: list[SpecializedEvaluationResult] = Field(default_factory=list)
    events: list[dict[str, Any]] = Field(default_factory=list)


class SpecializedEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    normalization_run_id: UUID
    company_id: UUID
    company_profile_snapshot_id: UUID
    domain: SpecializedEvaluationDomain
    force: bool = False


class SpecializedEvaluationRetryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    force: bool = False


class SpecializedEvaluationQueueResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job: SpecializedEvaluationJobSummary
    run: SpecializedEvaluationRunSummary


class SpecializedEvaluationResultReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_status: SpecializedEvaluationReviewStatus
    override_result: SpecializedEvaluationResultStatus | None = None
    override_reason: str | None = Field(default=None, max_length=2000)
    review_notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_override(self) -> "SpecializedEvaluationResultReviewRequest":
        if self.review_status == SpecializedEvaluationReviewStatus.OVERRIDDEN and (
            self.override_result is None or not self.override_reason
        ):
            raise ValueError("override_result y override_reason son obligatorios")
        return self


class SpecializedEvaluationList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[SpecializedEvaluationRunSummary]
    total: int = Field(ge=0)
    limit: int = Field(gt=0)
    offset: int = Field(ge=0)


class SpecializedEvaluationResultList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[SpecializedEvaluationResult]
    total: int = Field(ge=0)
    limit: int = Field(gt=0)
    offset: int = Field(ge=0)


class SpecializedEvaluationReadiness(BaseModel):
    model_config = ConfigDict(extra="forbid")

    process_id: UUID
    normalization_run_id: UUID
    company_profile_snapshot_id: UUID
    domain: SpecializedEvaluationDomain
    available_domains: list[SpecializedEvaluationDomain]
    requirement_count: int = Field(ge=0)
    evaluable_count: int = Field(ge=0)
    ambiguous_count: int = Field(ge=0)
    unsupported_count: int = Field(ge=0)
    snapshot_published: bool
    warnings: list[str] = Field(default_factory=list)
    rules: list[SpecializedRequirementRule] = Field(default_factory=list)


class SpecializedEvaluationContracts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0.0"] = SPECIALIZED_EVALUATION_SCHEMA_VERSION
    rule: SpecializedRequirementRule
    rule_update: SpecializedRequirementRuleUpdate
    evidence: SpecializedEvaluationEvidence
    result: SpecializedEvaluationResult
    result_detail: SpecializedEvaluationResultDetail
    job: SpecializedEvaluationJobSummary
    run_summary: SpecializedEvaluationRunSummary
    run_detail: SpecializedEvaluationRunDetail
    request: SpecializedEvaluationRequest
    retry_request: SpecializedEvaluationRetryRequest
    queue_response: SpecializedEvaluationQueueResponse
    review_request: SpecializedEvaluationResultReviewRequest
    evaluation_list: SpecializedEvaluationList
    result_list: SpecializedEvaluationResultList
    readiness: SpecializedEvaluationReadiness
