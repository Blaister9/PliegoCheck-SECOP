"""Contratos de evaluacion financiera deterministica (Microfase 6)."""

from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

from pliegocheck_schemas.company_profile import FinancialMetricType

FINANCIAL_EVALUATION_SCHEMA_VERSION: Literal["1.0.0"] = "1.0.0"

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]


class FinancialEvaluationJobStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class FinancialEvaluationRunStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class FinancialEvaluationResultStatus(StrEnum):
    COMPLIES = "COMPLIES"
    DOES_NOT_COMPLY = "DOES_NOT_COMPLY"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"


class FinancialEvaluationReviewStatus(StrEnum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    OVERRIDDEN = "OVERRIDDEN"
    REJECTED = "REJECTED"


class FinancialRuleType(StrEnum):
    DIRECT_METRIC = "DIRECT_METRIC"
    DERIVED_METRIC = "DERIVED_METRIC"
    RANGE = "RANGE"
    COMPOSITE_ALL = "COMPOSITE_ALL"
    COMPOSITE_ANY = "COMPOSITE_ANY"
    INFORMATIONAL = "INFORMATIONAL"
    UNSUPPORTED = "UNSUPPORTED"


class FinancialRuleMappingStatus(StrEnum):
    MAPPED = "MAPPED"
    PARTIALLY_MAPPED = "PARTIALLY_MAPPED"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"
    INVALID = "INVALID"


class FinancialOperator(StrEnum):
    GREATER_THAN = "GREATER_THAN"
    GREATER_THAN_OR_EQUAL = "GREATER_THAN_OR_EQUAL"
    LESS_THAN = "LESS_THAN"
    LESS_THAN_OR_EQUAL = "LESS_THAN_OR_EQUAL"
    EQUAL = "EQUAL"
    NOT_EQUAL = "NOT_EQUAL"
    BETWEEN_INCLUSIVE = "BETWEEN_INCLUSIVE"
    BETWEEN_EXCLUSIVE = "BETWEEN_EXCLUSIVE"
    EXISTS = "EXISTS"
    NOT_EXISTS = "NOT_EXISTS"


class FinancialPeriodPolicy(StrEnum):
    EXACT_YEAR = "EXACT_YEAR"
    LATEST_AVAILABLE = "LATEST_AVAILABLE"
    LATEST_BEFORE_PROCESS_CLOSING = "LATEST_BEFORE_PROCESS_CLOSING"
    RUP_REFERENCE_PERIOD = "RUP_REFERENCE_PERIOD"
    MANUAL_SELECTION = "MANUAL_SELECTION"
    UNKNOWN = "UNKNOWN"


class FinancialMetricUsability(StrEnum):
    VERIFIED = "VERIFIED"
    SUPPORTED = "SUPPORTED"
    DECLARED_ONLY = "DECLARED_ONLY"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"
    CONFLICTING = "CONFLICTING"
    MISSING = "MISSING"


class FinancialCalculationStatus(StrEnum):
    COMPLETED = "COMPLETED"
    MISSING_INPUT = "MISSING_INPUT"
    DIVISION_BY_ZERO = "DIVISION_BY_ZERO"
    UNIT_MISMATCH = "UNIT_MISMATCH"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"
    CONFLICTING_INPUT = "CONFLICTING_INPUT"
    FAILED = "FAILED"


class FinancialCompositeOperator(StrEnum):
    ALL = "ALL"
    ANY = "ANY"


class FinancialRuleSourceBasis(StrEnum):
    EXPLICIT_EXPECTED_VALUE = "EXPLICIT_EXPECTED_VALUE"
    EXPLICIT_DESCRIPTION = "EXPLICIT_DESCRIPTION"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"
    UNKNOWN = "UNKNOWN"


class FinancialExplanationCode(StrEnum):
    VALUE_MEETS_MINIMUM = "VALUE_MEETS_MINIMUM"
    VALUE_BELOW_MINIMUM = "VALUE_BELOW_MINIMUM"
    VALUE_MEETS_MAXIMUM = "VALUE_MEETS_MAXIMUM"
    VALUE_EXCEEDS_MAXIMUM = "VALUE_EXCEEDS_MAXIMUM"
    VALUE_WITHIN_RANGE = "VALUE_WITHIN_RANGE"
    VALUE_OUTSIDE_RANGE = "VALUE_OUTSIDE_RANGE"
    METRIC_MISSING = "METRIC_MISSING"
    PERIOD_NOT_RESOLVED = "PERIOD_NOT_RESOLVED"
    DECLARED_VALUE_NOT_VERIFIED = "DECLARED_VALUE_NOT_VERIFIED"
    EVIDENCE_CONFLICT = "EVIDENCE_CONFLICT"
    UNIT_MISMATCH = "UNIT_MISMATCH"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"
    DIVISION_BY_ZERO = "DIVISION_BY_ZERO"
    RULE_AMBIGUOUS = "RULE_AMBIGUOUS"
    RULE_UNSUPPORTED = "RULE_UNSUPPORTED"
    NOT_FINANCIAL_REQUIREMENT = "NOT_FINANCIAL_REQUIREMENT"


class FinancialErrorCode(StrEnum):
    FINANCIAL_EVALUATION_ALREADY_QUEUED = "FINANCIAL_EVALUATION_ALREADY_QUEUED"
    FINANCIAL_EVALUATION_ALREADY_COMPLETED = "FINANCIAL_EVALUATION_ALREADY_COMPLETED"
    FINANCIAL_EVALUATION_NOT_FOUND = "FINANCIAL_EVALUATION_NOT_FOUND"
    FINANCIAL_EVALUATION_INPUT_NOT_READY = "FINANCIAL_EVALUATION_INPUT_NOT_READY"
    FINANCIAL_REQUIREMENTS_NOT_FOUND = "FINANCIAL_REQUIREMENTS_NOT_FOUND"
    COMPANY_SNAPSHOT_NOT_FOUND = "COMPANY_SNAPSHOT_NOT_FOUND"
    COMPANY_SNAPSHOT_NOT_PUBLISHED = "COMPANY_SNAPSHOT_NOT_PUBLISHED"
    FINANCIAL_RULE_AMBIGUOUS = "FINANCIAL_RULE_AMBIGUOUS"
    FINANCIAL_RULE_UNSUPPORTED = "FINANCIAL_RULE_UNSUPPORTED"
    FINANCIAL_METRIC_MISSING = "FINANCIAL_METRIC_MISSING"
    FINANCIAL_PERIOD_NOT_RESOLVED = "FINANCIAL_PERIOD_NOT_RESOLVED"
    FINANCIAL_UNIT_MISMATCH = "FINANCIAL_UNIT_MISMATCH"
    FINANCIAL_CURRENCY_MISMATCH = "FINANCIAL_CURRENCY_MISMATCH"
    FINANCIAL_DIVISION_BY_ZERO = "FINANCIAL_DIVISION_BY_ZERO"
    FINANCIAL_EVIDENCE_CONFLICT = "FINANCIAL_EVIDENCE_CONFLICT"
    FINANCIAL_CALCULATION_FAILED = "FINANCIAL_CALCULATION_FAILED"
    FINANCIAL_EVALUATION_FAILED = "FINANCIAL_EVALUATION_FAILED"
    INVALID_FINANCIAL_OVERRIDE = "INVALID_FINANCIAL_OVERRIDE"
    DATABASE_ERROR = "DATABASE_ERROR"


class FinancialFormulaVersion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    formula_name: ShortText
    semantic_version: ShortText
    expression: ShortText
    required_metric_types: list[FinancialMetricType]
    output_metric_type: FinancialMetricType
    output_unit: str | None = None
    rounding_policy: ShortText
    created_at: AwareDatetime | None = None
    is_active: bool = True


class FinancialRequirementRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    requirement_id: UUID
    normalization_run_id: UUID
    rule_type: FinancialRuleType
    metric_type: FinancialMetricType | None
    operator: FinancialOperator | None
    required_value: Decimal | None = None
    required_min_value: Decimal | None = None
    required_max_value: Decimal | None = None
    unit: str | None = None
    currency: str | None = None
    period_policy: FinancialPeriodPolicy
    period_year: int | None = Field(default=None, ge=1900, le=2200)
    condition_group: dict[str, Any] = Field(default_factory=dict)
    source_basis: FinancialRuleSourceBasis
    mapping_status: FinancialRuleMappingStatus
    mapping_warnings: list[str] = Field(default_factory=list)
    requires_human_review: bool = False
    version: int = Field(gt=0)
    is_manual_override: bool = False
    created_at: AwareDatetime
    updated_at: AwareDatetime


class FinancialRequirementRuleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_type: FinancialRuleType | None = None
    metric_type: FinancialMetricType | None = None
    operator: FinancialOperator | None = None
    required_value: Decimal | None = None
    required_min_value: Decimal | None = None
    required_max_value: Decimal | None = None
    unit: str | None = None
    currency: str | None = None
    period_policy: FinancialPeriodPolicy | None = None
    period_year: int | None = Field(default=None, ge=1900, le=2200)
    condition_group: dict[str, Any] | None = None
    mapping_warnings: list[str] | None = None
    requires_human_review: bool | None = None
    override_reason: ShortText | None = None


class FinancialMetricInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_id: UUID | None
    metric_type: FinancialMetricType
    value: Decimal | None
    unit: str | None
    currency: str | None
    period_start: date | None
    period_end: date | None
    evidence_status: FinancialMetricUsability
    review_status: str | None = None
    evidence_ids: list[UUID] = Field(default_factory=list)
    source_type: str | None = None


class FinancialMetricCalculation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    run_id: UUID
    financial_period_id: UUID | None
    metric_type: FinancialMetricType
    formula_name: str
    formula_version: str
    input_values: dict[str, Any]
    raw_result: Decimal | None
    rounded_result: Decimal | None
    unit: str | None
    status: FinancialCalculationStatus
    warning_codes: list[str] = Field(default_factory=list)
    created_at: AwareDatetime


class FinancialEvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    run_id: UUID
    requirement_id: UUID
    financial_rule_id: UUID | None
    status: FinancialEvaluationResultStatus
    metric_type: FinancialMetricType | None
    operator: FinancialOperator | None
    required_value: Decimal | None = None
    required_min_value: Decimal | None = None
    required_max_value: Decimal | None = None
    required_unit: str | None = None
    actual_value: Decimal | None = None
    actual_unit: str | None = None
    currency: str | None = None
    financial_period_id: UUID | None = None
    calculation_id: UUID | None = None
    explanation_code: FinancialExplanationCode
    explanation_parameters: dict[str, Any] = Field(default_factory=dict)
    requires_human_review: bool = False
    review_status: FinancialEvaluationReviewStatus = FinancialEvaluationReviewStatus.PENDING
    reviewed_status: FinancialEvaluationResultStatus | None = None
    review_notes: str | None = None
    reviewed_at: AwareDatetime | None = None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class FinancialEvaluationResultDetail(FinancialEvaluationResult):
    requirement: dict[str, Any] = Field(default_factory=dict)
    rule: FinancialRequirementRule | None = None
    calculation: FinancialMetricCalculation | None = None
    metric_inputs: list[FinancialMetricInput] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
    reviews: list[dict[str, Any]] = Field(default_factory=list)


class FinancialEvaluationJobSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    process_id: UUID
    normalization_run_id: UUID
    company_id: UUID
    company_profile_snapshot_id: UUID
    status: FinancialEvaluationJobStatus
    attempt_count: int = Field(ge=0)
    max_attempts: int = Field(gt=0)
    force: bool
    created_at: AwareDatetime
    updated_at: AwareDatetime


class FinancialEvaluationRunSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    job_id: UUID
    process_id: UUID
    normalization_run_id: UUID
    company_id: UUID
    company_profile_snapshot_id: UUID
    status: FinancialEvaluationRunStatus
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


class FinancialEvaluationRunDetail(FinancialEvaluationRunSummary):
    input_manifest: dict[str, Any]
    job: FinancialEvaluationJobSummary | None = None
    rules: list[FinancialRequirementRule] = Field(default_factory=list)
    calculations: list[FinancialMetricCalculation] = Field(default_factory=list)
    results: list[FinancialEvaluationResult] = Field(default_factory=list)
    events: list[dict[str, Any]] = Field(default_factory=list)


class FinancialEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    normalization_run_id: UUID
    company_id: UUID
    company_profile_snapshot_id: UUID
    force: bool = False


class FinancialEvaluationRetryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    force: bool = False


class FinancialEvaluationQueueResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job: FinancialEvaluationJobSummary
    run: FinancialEvaluationRunSummary


class FinancialEvaluationResultReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_status: FinancialEvaluationReviewStatus
    override_result: FinancialEvaluationResultStatus | None = None
    override_reason: str | None = Field(default=None, max_length=2000)
    review_notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_override(self) -> "FinancialEvaluationResultReviewRequest":
        if self.review_status == FinancialEvaluationReviewStatus.OVERRIDDEN and (
            self.override_result is None or not self.override_reason
        ):
            raise ValueError("override_result y override_reason son obligatorios")
        return self


class FinancialEvaluationList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[FinancialEvaluationRunSummary]
    total: int = Field(ge=0)
    limit: int = Field(gt=0)
    offset: int = Field(ge=0)


class FinancialEvaluationResultList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[FinancialEvaluationResult]
    total: int = Field(ge=0)
    limit: int = Field(gt=0)
    offset: int = Field(ge=0)


class FinancialEvaluationCompleteness(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: UUID
    has_financial_requirements: bool
    has_published_company_snapshot: bool
    has_financial_periods: bool
    has_financial_metrics: bool
    ambiguous_rule_count: int = Field(ge=0)
    missing_metric_count: int = Field(ge=0)
    conflicting_evidence_count: int = Field(ge=0)
    ready_for_review: bool


class FinancialEvaluationContracts(BaseModel):
    """Contenedor para generar JSON Schema con defs compartidos."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0.0"] = FINANCIAL_EVALUATION_SCHEMA_VERSION
    formula_version: FinancialFormulaVersion
    rule: FinancialRequirementRule
    rule_update: FinancialRequirementRuleUpdate
    metric_input: FinancialMetricInput
    calculation: FinancialMetricCalculation
    result: FinancialEvaluationResult
    result_detail: FinancialEvaluationResultDetail
    job: FinancialEvaluationJobSummary
    run_summary: FinancialEvaluationRunSummary
    run_detail: FinancialEvaluationRunDetail
    request: FinancialEvaluationRequest
    retry_request: FinancialEvaluationRetryRequest
    queue_response: FinancialEvaluationQueueResponse
    review_request: FinancialEvaluationResultReviewRequest
    evaluation_list: FinancialEvaluationList
    result_list: FinancialEvaluationResultList
    completeness: FinancialEvaluationCompleteness
