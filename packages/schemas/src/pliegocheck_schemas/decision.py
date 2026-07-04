"""Contratos del motor deterministico de decision (Microfase 7).

El motor no usa IA: consume hallazgos canonicos de evaluadores especializados,
mide cobertura y aplica reglas versionadas de una politica de decision. La
salida es una decision preliminar auditable; nunca un concepto juridico.
"""

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

DECISION_SCHEMA_VERSION: Literal["1.0.0"] = "1.0.0"

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]


class DecisionOutcome(StrEnum):
    """Resultados finales permitidos, en orden de precedencia descendente."""

    NO_CARGAR = "NO_CARGAR"
    NO_GO = "NO_GO"
    PENDIENTE_INFORMACION = "PENDIENTE_INFORMACION"
    BUSCAR_ALIADO = "BUSCAR_ALIADO"
    GO_CONDICIONADO = "GO_CONDICIONADO"
    GO = "GO"


class DecisionJobStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class DecisionRunStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class DecisionFindingOutcome(StrEnum):
    """Outcome canonico de un hallazgo de entrada."""

    COMPLIES = "COMPLIES"
    DOES_NOT_COMPLY = "DOES_NOT_COMPLY"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    NOT_EVALUATED = "NOT_EVALUATED"


class DecisionEvaluationDomain(StrEnum):
    FINANCIAL = "FINANCIAL"
    ORGANIZATIONAL = "ORGANIZATIONAL"
    LEGAL = "LEGAL"
    EXPERIENCE = "EXPERIENCE"
    TECHNICAL = "TECHNICAL"
    WORKFORCE = "WORKFORCE"
    DOCUMENTARY = "DOCUMENTARY"
    GUARANTEE = "GUARANTEE"
    SCHEDULE = "SCHEDULE"
    ECONOMIC = "ECONOMIC"
    OPERATIONAL = "OPERATIONAL"
    RISK_AND_INELIGIBILITY = "RISK_AND_INELIGIBILITY"
    OTHER = "OTHER"


class DecisionFindingApplicability(StrEnum):
    MANDATORY = "MANDATORY"
    OPTIONAL = "OPTIONAL"
    INFORMATIONAL = "INFORMATIONAL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class DecisionFindingSourceType(StrEnum):
    FINANCIAL_EVALUATION = "FINANCIAL_EVALUATION"
    SPECIALIZED_EVALUATION = "SPECIALIZED_EVALUATION"
    SYNTHETIC = "SYNTHETIC"
    MISSING_ADAPTER = "MISSING_ADAPTER"


class DecisionCoverageStatus(StrEnum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"
    NOT_REQUIRED = "NOT_REQUIRED"


class DecisionRuleStatus(StrEnum):
    TRIGGERED = "TRIGGERED"
    NOT_TRIGGERED = "NOT_TRIGGERED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    INDETERMINATE = "INDETERMINATE"


class DecisionReviewAction(StrEnum):
    CONFIRM = "CONFIRM"
    OVERRIDE = "OVERRIDE"
    REJECT = "REJECT"


class DecisionActionType(StrEnum):
    PROVIDE_INFORMATION = "PROVIDE_INFORMATION"
    RESOLVE_CONFLICT = "RESOLVE_CONFLICT"
    REVIEW_REQUIREMENT = "REVIEW_REQUIREMENT"
    REVIEW_EVIDENCE = "REVIEW_EVIDENCE"
    CORRECT_FINANCIAL_GAP = "CORRECT_FINANCIAL_GAP"
    SEEK_PARTNER = "SEEK_PARTNER"
    COMPLETE_MANDATORY_EVALUATION = "COMPLETE_MANDATORY_EVALUATION"
    CONFIRM_SUBSANABILITY = "CONFIRM_SUBSANABILITY"
    DO_NOT_SUBMIT = "DO_NOT_SUBMIT"
    OTHER = "OTHER"


class DecisionActionPriority(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class DecisionActionStatus(StrEnum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class DecisionReasonCode(StrEnum):
    """Codigos deterministicos de explicacion. La UI los traduce a mensajes."""

    FULL_MANDATORY_COVERAGE = "FULL_MANDATORY_COVERAGE"
    MANDATORY_REQUIREMENT_NOT_EVALUATED = "MANDATORY_REQUIREMENT_NOT_EVALUATED"
    MANDATORY_REQUIREMENT_UNKNOWN = "MANDATORY_REQUIREMENT_UNKNOWN"
    MANDATORY_REQUIREMENT_PARTIAL = "MANDATORY_REQUIREMENT_PARTIAL"
    MANDATORY_REQUIREMENT_UNRESOLVED = "MANDATORY_REQUIREMENT_UNRESOLVED"
    BLOCKING_REQUIREMENT_FAILED = "BLOCKING_REQUIREMENT_FAILED"
    NON_SUBSANABLE_REQUIREMENT_FAILED = "NON_SUBSANABLE_REQUIREMENT_FAILED"
    CRITICAL_EVIDENCE_CONFLICT = "CRITICAL_EVIDENCE_CONFLICT"
    PARTNER_SOLVABLE_GAP_CONFIRMED = "PARTNER_SOLVABLE_GAP_CONFIRMED"
    REMEDIABLE_CONDITION_PENDING = "REMEDIABLE_CONDITION_PENDING"
    SUBMISSION_BLOCKER_CONFIRMED = "SUBMISSION_BLOCKER_CONFIRMED"
    ALL_MANDATORY_REQUIREMENTS_COMPLY = "ALL_MANDATORY_REQUIREMENTS_COMPLY"
    HUMAN_REVIEW_PENDING = "HUMAN_REVIEW_PENDING"
    ADAPTER_NOT_AVAILABLE = "ADAPTER_NOT_AVAILABLE"


class DecisionErrorCode(StrEnum):
    DECISION_ALREADY_QUEUED = "DECISION_ALREADY_QUEUED"
    DECISION_ALREADY_COMPLETED = "DECISION_ALREADY_COMPLETED"
    DECISION_NOT_FOUND = "DECISION_NOT_FOUND"
    DECISION_INPUT_NOT_READY = "DECISION_INPUT_NOT_READY"
    DECISION_POLICY_NOT_FOUND = "DECISION_POLICY_NOT_FOUND"
    DECISION_POLICY_INVALID = "DECISION_POLICY_INVALID"
    DECISION_NORMALIZATION_NOT_COMPLETED = "DECISION_NORMALIZATION_NOT_COMPLETED"
    DECISION_COMPANY_SNAPSHOT_NOT_PUBLISHED = "DECISION_COMPANY_SNAPSHOT_NOT_PUBLISHED"
    DECISION_FINANCIAL_EVALUATION_NOT_COMPLETED = "DECISION_FINANCIAL_EVALUATION_NOT_COMPLETED"
    DECISION_INPUT_MISMATCH = "DECISION_INPUT_MISMATCH"
    DECISION_COVERAGE_INCOMPLETE = "DECISION_COVERAGE_INCOMPLETE"
    DECISION_RULE_EVALUATION_FAILED = "DECISION_RULE_EVALUATION_FAILED"
    DECISION_ENGINE_FAILED = "DECISION_ENGINE_FAILED"
    INVALID_DECISION_OVERRIDE = "INVALID_DECISION_OVERRIDE"
    DECISION_ACTION_NOT_FOUND = "DECISION_ACTION_NOT_FOUND"


class DecisionInputFinding(BaseModel):
    """Hallazgo canonico de entrada al motor. Nunca modifica la fuente."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    requirement_id: UUID
    requirement_stable_key: Sha256
    category: str
    scope: str
    modality: str
    criticality: str
    criticality_basis: str
    subsanability: str
    subsanability_basis: str
    evaluation_domain: DecisionEvaluationDomain
    source_type: DecisionFindingSourceType
    source_run_id: UUID | None
    source_result_id: UUID | None
    outcome: DecisionFindingOutcome
    applicability: DecisionFindingApplicability
    evidence_quality: str | None = None
    review_status: str | None = None
    requires_human_review: bool = False
    is_blocking: bool = False
    is_remediable: bool = False
    partner_solvable: bool = False
    submission_blocker: bool = False
    condition_codes: list[str] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)
    evidence_references: list[dict[str, Any]] = Field(default_factory=list)
    created_at: AwareDatetime | None = None


class DecisionCoverageCategory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str
    requirements_total: int = Field(ge=0)
    mandatory_total: int = Field(ge=0)
    evaluated_total: int = Field(ge=0)
    not_evaluated_total: int = Field(ge=0)
    outcomes: dict[str, int] = Field(default_factory=dict)
    adapter_available: bool
    coverage_status: DecisionCoverageStatus


class DecisionCoverageSummary(BaseModel):
    """Cobertura mediante conteos claros; nunca un score ni probabilidad."""

    model_config = ConfigDict(extra="forbid")

    requirements_total: int = Field(ge=0)
    mandatory_applicable_total: int = Field(ge=0)
    optional_total: int = Field(ge=0)
    evaluated_total: int = Field(ge=0)
    not_evaluated_total: int = Field(ge=0)
    complies_total: int = Field(ge=0)
    does_not_comply_total: int = Field(ge=0)
    partial_total: int = Field(ge=0)
    unknown_total: int = Field(ge=0)
    not_applicable_total: int = Field(ge=0)
    conflicting_total: int = Field(ge=0)
    blocking_failure_total: int = Field(ge=0)
    remediable_gap_total: int = Field(ge=0)
    partner_gap_total: int = Field(ge=0)
    submission_blocker_total: int = Field(ge=0)
    human_review_pending_total: int = Field(ge=0)
    categories: list[DecisionCoverageCategory] = Field(default_factory=list)


class DecisionRuleEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID | None = None
    rule_code: ShortText
    rule_version: ShortText
    priority: int = Field(ge=0)
    status: DecisionRuleStatus
    suggested_outcome: DecisionOutcome | None
    fact_payload: dict[str, Any] = Field(default_factory=dict)
    requirement_ids: list[UUID] = Field(default_factory=list)
    finding_ids: list[UUID] = Field(default_factory=list)
    reason_code: DecisionReasonCode | None
    created_at: AwareDatetime | None = None


class DecisionActionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    decision_run_id: UUID
    action_type: DecisionActionType
    priority: DecisionActionPriority
    title_code: ShortText
    description_code: ShortText
    parameters: dict[str, Any] = Field(default_factory=dict)
    requirement_ids: list[UUID] = Field(default_factory=list)
    finding_ids: list[UUID] = Field(default_factory=list)
    due_at: AwareDatetime | None
    status: DecisionActionStatus
    created_at: AwareDatetime
    updated_at: AwareDatetime


class DecisionActionUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: DecisionActionStatus
    note: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_status(self) -> "DecisionActionUpdateRequest":
        if self.status == DecisionActionStatus.OPEN:
            raise ValueError("una accion no puede reabrirse; cree una nueva decision")
        return self


class DecisionJobSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    process_id: UUID
    normalization_run_id: UUID
    company_id: UUID
    company_profile_snapshot_id: UUID
    financial_evaluation_run_id: UUID
    status: DecisionJobStatus
    attempt_count: int = Field(ge=0)
    max_attempts: int = Field(gt=0)
    force: bool
    last_error_code: str | None = None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class DecisionPolicySummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID | None = None
    policy_name: ShortText
    semantic_version: ShortText
    content_sha256: Sha256
    engine_version: ShortText
    is_active: bool
    created_at: AwareDatetime | None = None


class DecisionRunSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    job_id: UUID
    process_id: UUID
    normalization_run_id: UUID
    company_id: UUID
    company_profile_snapshot_id: UUID
    financial_evaluation_run_id: UUID
    policy_name: str
    policy_version: str
    status: DecisionRunStatus
    engine_outcome: DecisionOutcome | None
    reviewed_outcome: DecisionOutcome | None
    effective_outcome: DecisionOutcome | None
    reason_codes: list[DecisionReasonCode] = Field(default_factory=list)
    input_digest: Sha256
    engine_version: ShortText
    requirement_count: int = Field(ge=0)
    finding_count: int = Field(ge=0)
    action_count: int = Field(ge=0)
    warning_count: int = Field(ge=0)
    warnings: list[str] = Field(default_factory=list)
    requires_human_review: bool
    started_at: AwareDatetime | None
    finished_at: AwareDatetime | None
    error_code: str | None
    error_message: str | None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class DecisionReviewRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    decision_run_id: UUID
    action: DecisionReviewAction
    original_outcome: DecisionOutcome
    reviewed_outcome: DecisionOutcome | None
    reason: str | None
    reviewer_reference: str
    created_at: AwareDatetime


class DecisionRunDetail(DecisionRunSummary):
    input_manifest: dict[str, Any] = Field(default_factory=dict)
    coverage: DecisionCoverageSummary | None = None
    findings: list[DecisionInputFinding] = Field(default_factory=list)
    rule_evaluations: list[DecisionRuleEvaluation] = Field(default_factory=list)
    actions: list[DecisionActionItem] = Field(default_factory=list)
    reviews: list[DecisionReviewRecord] = Field(default_factory=list)
    job: DecisionJobSummary | None = None
    policy: DecisionPolicySummary | None = None
    events: list[dict[str, Any]] = Field(default_factory=list)


class DecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    normalization_run_id: UUID
    company_id: UUID
    company_profile_snapshot_id: UUID
    financial_evaluation_run_id: UUID
    force: bool = False


class DecisionRetryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    force: bool = False


class DecisionQueueResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job: DecisionJobSummary
    run: DecisionRunSummary
    reused_existing_run: bool = False


class DecisionReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: DecisionReviewAction
    reviewed_outcome: DecisionOutcome | None = None
    reason: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_review(self) -> "DecisionReviewRequest":
        if self.action == DecisionReviewAction.OVERRIDE and self.reviewed_outcome is None:
            raise ValueError("reviewed_outcome es obligatorio para OVERRIDE")
        if self.action in {DecisionReviewAction.OVERRIDE, DecisionReviewAction.REJECT} and not (
            self.reason and self.reason.strip()
        ):
            raise ValueError("reason es obligatoria para OVERRIDE o REJECT")
        return self


class DecisionReviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run: DecisionRunSummary
    review: DecisionReviewRecord


class DecisionReadinessCategory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str
    requirements_total: int = Field(ge=0)
    mandatory_total: int = Field(ge=0)
    adapter_available: bool


class DecisionReadiness(BaseModel):
    """Diagnostico previo. No ejecuta el motor."""

    model_config = ConfigDict(extra="forbid")

    process_id: UUID
    inputs_valid: bool
    input_errors: list[str] = Field(default_factory=list)
    required_categories: list[DecisionReadinessCategory] = Field(default_factory=list)
    available_adapters: list[DecisionEvaluationDomain] = Field(default_factory=list)
    not_evaluated_mandatory_count: int = Field(ge=0)
    warnings: list[str] = Field(default_factory=list)
    max_possible_outcome: DecisionOutcome
    go_blocked_by_coverage: bool
    policy: DecisionPolicySummary | None = None


class DecisionRunList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[DecisionRunSummary]
    total: int = Field(ge=0)
    limit: int = Field(gt=0)
    offset: int = Field(ge=0)


class DecisionContracts(BaseModel):
    """Contenedor para generar JSON Schema con defs compartidos."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0.0"] = DECISION_SCHEMA_VERSION
    input_finding: DecisionInputFinding
    coverage_category: DecisionCoverageCategory
    coverage_summary: DecisionCoverageSummary
    rule_evaluation: DecisionRuleEvaluation
    action_item: DecisionActionItem
    action_update_request: DecisionActionUpdateRequest
    job_summary: DecisionJobSummary
    run_summary: DecisionRunSummary
    run_detail: DecisionRunDetail
    request: DecisionRequest
    retry_request: DecisionRetryRequest
    queue_response: DecisionQueueResponse
    review_request: DecisionReviewRequest
    review_response: DecisionReviewResponse
    review_record: DecisionReviewRecord
    readiness: DecisionReadiness
    policy_summary: DecisionPolicySummary
    run_list: DecisionRunList
