"""Contratos tipados para monitores y alertas de oportunidades."""

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from .external_procurement import ExternalProcurementSearchRequest, ExternalProcurementSourceSystem

OPPORTUNITY_MONITORING_SCHEMA_VERSION = "1.0.0"
ALERT_DISCLAIMER = (
    "Las alertas señalan novedades o cambios relevantes según la política configurada. "
    "No constituyen una recomendación automática de presentar oferta."
)


class OpportunityMonitorStatus(StrEnum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DISABLED = "DISABLED"
    ERROR = "ERROR"


class OpportunityMonitorFrequency(StrEnum):
    HOURLY = "HOURLY"
    EVERY_3_HOURS = "EVERY_3_HOURS"
    EVERY_6_HOURS = "EVERY_6_HOURS"
    EVERY_12_HOURS = "EVERY_12_HOURS"
    DAILY = "DAILY"
    WEEKDAYS = "WEEKDAYS"


class OpportunityMonitorRunStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    SKIPPED = "SKIPPED"


class OpportunityMonitorTriggerType(StrEnum):
    SCHEDULED = "SCHEDULED"
    MANUAL = "MANUAL"
    RETRY = "RETRY"
    BASELINE = "BASELINE"


class OpportunityAlertType(StrEnum):
    NEW_REVIEW_FIRST = "NEW_REVIEW_FIRST"
    NEW_POTENTIAL_OPPORTUNITY = "NEW_POTENTIAL_OPPORTUNITY"
    NEW_PARTNER_NEEDED = "NEW_PARTNER_NEEDED"
    OPPORTUNITY_NOW_URGENT = "OPPORTUNITY_NOW_URGENT"
    OPPORTUNITY_NOW_CRITICAL = "OPPORTUNITY_NOW_CRITICAL"
    OUTCOME_IMPROVED = "OUTCOME_IMPROVED"
    OUTCOME_WORSENED = "OUTCOME_WORSENED"
    COMPATIBILITY_INCREASED = "COMPATIBILITY_INCREASED"
    COMPATIBILITY_DECREASED = "COMPATIBILITY_DECREASED"
    CLOSING_DATE_CHANGED = "CLOSING_DATE_CHANGED"
    PROCESS_CLOSED = "PROCESS_CLOSED"
    NEW_DOCUMENT_DISCOVERED = "NEW_DOCUMENT_DISCOVERED"
    DOCUMENT_UPDATED = "DOCUMENT_UPDATED"
    POTENTIAL_ADDENDUM_DISCOVERED = "POTENTIAL_ADDENDUM_DISCOVERED"
    CONFIRMED_ADDENDUM_DISCOVERED = "CONFIRMED_ADDENDUM_DISCOVERED"
    DEEP_ANALYSIS_BLOCKED = "DEEP_ANALYSIS_BLOCKED"
    MONITOR_FAILURE = "MONITOR_FAILURE"
    MONITOR_RECOVERED = "MONITOR_RECOVERED"


class OpportunityAlertSeverity(StrEnum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class OpportunityAlertStatus(StrEnum):
    UNREAD = "UNREAD"
    READ = "READ"
    ARCHIVED = "ARCHIVED"
    RESOLVED = "RESOLVED"


class OpportunityAlertAction(StrEnum):
    MARK_READ = "MARK_READ"
    MARK_UNREAD = "MARK_UNREAD"
    ARCHIVE = "ARCHIVE"
    RESTORE = "RESTORE"
    RESOLVE = "RESOLVE"


class OpportunityAlertRules(BaseModel):
    model_config = ConfigDict(extra="forbid")
    new_review_first: bool = True
    new_potential: bool = True
    partner_needed: bool = True
    urgent_deadline: bool = True
    critical_deadline: bool = True
    outcome_changes: bool = True
    compatibility_changes: bool = True
    closing_date_changes: bool = True
    process_closed: bool = True
    new_documents: bool = True
    document_updates: bool = True
    addenda: bool = True
    monitor_failures: bool = True
    compatibility_change_threshold: float = Field(default=10, ge=1, le=100)
    minimum_compatibility_score: float = Field(default=0, ge=0, le=100)
    minimum_information_completeness: float = Field(default=0, ge=0, le=100)
    urgent_days: int = Field(default=5, ge=1, le=90)
    critical_hours: int = Field(default=48, ge=1, le=168)
    alert_on_initial_results: bool = False


class OpportunityMonitorFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    search_requests: list[ExternalProcurementSearchRequest] = Field(
        default_factory=list, max_length=10
    )
    candidate_ids: list[UUID] = Field(default_factory=list, max_length=500)

    @model_validator(mode="after")
    def require_scope(self) -> "OpportunityMonitorFilters":
        if not self.search_requests and not self.candidate_ids:
            raise ValueError("Debe configurar filtros SECOP o candidatos persistidos.")
        return self


class OpportunityMonitorCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    company_profile_id: UUID
    company_snapshot_id: UUID
    frequency: OpportunityMonitorFrequency
    timezone: str = Field(default="America/Bogota", min_length=1, max_length=64)
    filters: OpportunityMonitorFilters
    source_systems: list[ExternalProcurementSourceSystem] = Field(min_length=1, max_length=2)
    alert_rules: OpportunityAlertRules = Field(default_factory=OpportunityAlertRules)

    @model_validator(mode="after")
    def sources_match_filters(self) -> "OpportunityMonitorCreateRequest":
        requested = {item.source_system for item in self.filters.search_requests}
        if requested and not requested.issubset(set(self.source_systems)):
            raise ValueError("Las fuentes de filtros deben estar habilitadas en el monitor.")
        return self


class OpportunityMonitorUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    company_snapshot_id: UUID | None = None
    frequency: OpportunityMonitorFrequency | None = None
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    filters: OpportunityMonitorFilters | None = None
    source_systems: list[ExternalProcurementSourceSystem] | None = Field(
        default=None, min_length=1, max_length=2
    )
    alert_rules: OpportunityAlertRules | None = None


class OpportunityMonitorRunSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    monitor_id: UUID
    trigger_type: OpportunityMonitorTriggerType
    status: OpportunityMonitorRunStatus
    scheduled_for: AwareDatetime
    started_at: AwareDatetime | None = None
    finished_at: AwareDatetime | None = None
    discovery_run_id: UUID | None = None
    candidate_count: int = 0
    new_candidate_count: int = 0
    changed_candidate_count: int = 0
    alert_count: int = 0
    warning_count: int = 0
    error_code: str | None = None
    error_message: str | None = None
    created_at: AwareDatetime


class OpportunityMonitorSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    name: str
    description: str | None = None
    company_profile_id: UUID
    company_snapshot_id: UUID
    policy_version: str
    policy_hash: str
    status: OpportunityMonitorStatus
    frequency: OpportunityMonitorFrequency
    timezone: str
    source_systems: list[ExternalProcurementSourceSystem]
    last_run_at: AwareDatetime | None = None
    next_run_at: AwareDatetime | None = None
    last_success_at: AwareDatetime | None = None
    last_failure_at: AwareDatetime | None = None
    consecutive_failures: int = 0
    baseline_run_id: UUID | None = None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class OpportunityMonitorDetail(OpportunityMonitorSummary):
    filters: OpportunityMonitorFilters
    alert_rules: OpportunityAlertRules
    latest_runs: list[OpportunityMonitorRunSummary] = Field(default_factory=list)


class OpportunityMonitorList(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[OpportunityMonitorSummary]
    total: int
    limit: int
    offset: int


class OpportunityMonitorRunDetail(OpportunityMonitorRunSummary):
    input_digest: str


class OpportunityMonitorManualRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    force: bool = False


class OpportunityMonitorManualRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run: OpportunityMonitorRunSummary
    reused: bool = False


class OpportunityAlertSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    monitor_id: UUID
    monitor_run_id: UUID
    opportunity_id: UUID | None = None
    assessment_id: UUID | None = None
    alert_type: OpportunityAlertType
    severity: OpportunityAlertSeverity
    status: OpportunityAlertStatus
    title: str
    summary: str
    reason_code: str
    occurred_at: AwareDatetime
    first_seen_at: AwareDatetime
    last_seen_at: AwareDatetime
    read_at: AwareDatetime | None = None
    archived_at: AwareDatetime | None = None


class OpportunityAlertDetail(OpportunityAlertSummary):
    explanation_parameters: dict[str, Any]
    alert_fingerprint: str
    events: list[dict[str, Any]] = Field(default_factory=list)
    disclaimer: str = ALERT_DISCLAIMER


class OpportunityAlertList(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[OpportunityAlertSummary]
    total: int
    limit: int
    offset: int
    disclaimer: str = ALERT_DISCLAIMER


class OpportunityAlertActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: OpportunityAlertAction


class OpportunityAlertBulkActionRequest(OpportunityAlertActionRequest):
    alert_ids: list[UUID] = Field(min_length=1, max_length=100)


class OpportunityAlertActionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    updated_ids: list[UUID]
    status: OpportunityAlertStatus


class OpportunityAlertDigest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    period: str = Field(pattern="^(TODAY|LAST_24_HOURS|LAST_7_DAYS)$")
    generated_at: AwareDatetime
    priority_opportunities: int = 0
    critical_closings: int = 0
    relevant_changes: int = 0
    documents_and_addenda: int = 0
    monitor_failures: int = 0
    total: int = 0
    disclaimer: str = ALERT_DISCLAIMER


class OpportunityAlertUnreadCount(BaseModel):
    model_config = ConfigDict(extra="forbid")
    count: int = Field(ge=0)


class OpportunityMonitoringReadiness(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ready: bool
    enabled: bool
    active_monitors: int = 0
    pending_runs: int = 0
    reasons: list[str] = Field(default_factory=list)


class OpportunityMonitoringContracts(BaseModel):
    model_config = ConfigDict(extra="forbid")
    monitor_create: OpportunityMonitorCreateRequest
    monitor_update: OpportunityMonitorUpdateRequest
    monitor_detail: OpportunityMonitorDetail
    monitor_list: OpportunityMonitorList
    monitor_run: OpportunityMonitorRunDetail
    manual_run: OpportunityMonitorManualRunRequest
    manual_run_response: OpportunityMonitorManualRunResponse
    alert_detail: OpportunityAlertDetail
    alert_list: OpportunityAlertList
    alert_action: OpportunityAlertActionRequest
    alert_action_response: OpportunityAlertActionResponse
    alert_digest: OpportunityAlertDigest
    unread_count: OpportunityAlertUnreadCount
    readiness: OpportunityMonitoringReadiness
