// Archivo generado automaticamente desde opportunity-monitoring.schema.json
// (pnpm schemas:generate). No editar a mano: la definicion canonica son los
// modelos Pydantic de packages/schemas/src/pliegocheck_schemas/.

export type OpportunityAlertAction =
  "MARK_READ" | "MARK_UNREAD" | "ARCHIVE" | "RESTORE" | "RESOLVE";
export type OpportunityAlertStatus = "UNREAD" | "READ" | "ARCHIVED" | "RESOLVED";
export type OpportunityAlertType =
  | "NEW_REVIEW_FIRST"
  | "NEW_POTENTIAL_OPPORTUNITY"
  | "NEW_PARTNER_NEEDED"
  | "OPPORTUNITY_NOW_URGENT"
  | "OPPORTUNITY_NOW_CRITICAL"
  | "OUTCOME_IMPROVED"
  | "OUTCOME_WORSENED"
  | "COMPATIBILITY_INCREASED"
  | "COMPATIBILITY_DECREASED"
  | "CLOSING_DATE_CHANGED"
  | "PROCESS_CLOSED"
  | "NEW_DOCUMENT_DISCOVERED"
  | "DOCUMENT_UPDATED"
  | "POTENTIAL_ADDENDUM_DISCOVERED"
  | "CONFIRMED_ADDENDUM_DISCOVERED"
  | "DEEP_ANALYSIS_BLOCKED"
  | "MONITOR_FAILURE"
  | "MONITOR_RECOVERED";
export type OpportunityAlertSeverity = "INFO" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type OpportunityMonitorRunStatus =
  | "PENDING"
  | "PROCESSING"
  | "COMPLETED"
  | "COMPLETED_WITH_WARNINGS"
  | "FAILED"
  | "CANCELLED"
  | "SKIPPED";
export type OpportunityMonitorTriggerType = "SCHEDULED" | "MANUAL" | "RETRY" | "BASELINE";
export type OpportunityMonitorFrequency =
  "HOURLY" | "EVERY_3_HOURS" | "EVERY_6_HOURS" | "EVERY_12_HOURS" | "DAILY" | "WEEKDAYS";
export type ExternalProcurementSourceSystem = "SECOP_II" | "SECOP_I";
export type OpportunityMonitorStatus = "ACTIVE" | "PAUSED" | "DISABLED" | "ERROR";

export interface OpportunityMonitoring {
  alert_action: OpportunityAlertActionRequest;
  alert_action_response: OpportunityAlertActionResponse;
  alert_detail: OpportunityAlertDetail;
  alert_digest: OpportunityAlertDigest;
  alert_list: OpportunityAlertList;
  manual_run: OpportunityMonitorManualRunRequest;
  manual_run_response: OpportunityMonitorManualRunResponse;
  monitor_create: OpportunityMonitorCreateRequest;
  monitor_detail: OpportunityMonitorDetail;
  monitor_list: OpportunityMonitorList;
  monitor_run: OpportunityMonitorRunDetail;
  monitor_update: OpportunityMonitorUpdateRequest;
  readiness: OpportunityMonitoringReadiness;
  unread_count: OpportunityAlertUnreadCount;
}
export interface OpportunityAlertActionRequest {
  action: OpportunityAlertAction;
}
export interface OpportunityAlertActionResponse {
  status: OpportunityAlertStatus;
  updated_ids: string[];
}
export interface OpportunityAlertDetail {
  alert_fingerprint: string;
  alert_type: OpportunityAlertType;
  archived_at?: string | null;
  assessment_id?: string | null;
  disclaimer?: string;
  events?: {
    [k: string]: unknown;
  }[];
  explanation_parameters: {
    [k: string]: unknown;
  };
  first_seen_at: string;
  id: string;
  last_seen_at: string;
  monitor_id: string;
  monitor_run_id: string;
  occurred_at: string;
  opportunity_id?: string | null;
  read_at?: string | null;
  reason_code: string;
  severity: OpportunityAlertSeverity;
  status: OpportunityAlertStatus;
  summary: string;
  title: string;
}
export interface OpportunityAlertDigest {
  critical_closings?: number;
  disclaimer?: string;
  documents_and_addenda?: number;
  generated_at: string;
  monitor_failures?: number;
  period: string;
  priority_opportunities?: number;
  relevant_changes?: number;
  total?: number;
}
export interface OpportunityAlertList {
  disclaimer?: string;
  items: OpportunityAlertSummary[];
  limit: number;
  offset: number;
  total: number;
}
export interface OpportunityAlertSummary {
  alert_type: OpportunityAlertType;
  archived_at?: string | null;
  assessment_id?: string | null;
  first_seen_at: string;
  id: string;
  last_seen_at: string;
  monitor_id: string;
  monitor_run_id: string;
  occurred_at: string;
  opportunity_id?: string | null;
  read_at?: string | null;
  reason_code: string;
  severity: OpportunityAlertSeverity;
  status: OpportunityAlertStatus;
  summary: string;
  title: string;
}
export interface OpportunityMonitorManualRunRequest {
  force?: boolean;
}
export interface OpportunityMonitorManualRunResponse {
  reused?: boolean;
  run: OpportunityMonitorRunSummary;
}
export interface OpportunityMonitorRunSummary {
  alert_count?: number;
  candidate_count?: number;
  changed_candidate_count?: number;
  created_at: string;
  discovery_run_id?: string | null;
  error_code?: string | null;
  error_message?: string | null;
  finished_at?: string | null;
  id: string;
  monitor_id: string;
  new_candidate_count?: number;
  scheduled_for: string;
  started_at?: string | null;
  status: OpportunityMonitorRunStatus;
  trigger_type: OpportunityMonitorTriggerType;
  warning_count?: number;
}
export interface OpportunityMonitorCreateRequest {
  alert_rules?: OpportunityAlertRules;
  company_profile_id: string;
  company_snapshot_id: string;
  description?: string | null;
  filters: OpportunityMonitorFilters;
  frequency: OpportunityMonitorFrequency;
  name: string;
  /**
   * @minItems 1
   * @maxItems 2
   */
  source_systems:
    | [ExternalProcurementSourceSystem]
    | [ExternalProcurementSourceSystem, ExternalProcurementSourceSystem];
  timezone?: string;
}
export interface OpportunityAlertRules {
  addenda?: boolean;
  alert_on_initial_results?: boolean;
  closing_date_changes?: boolean;
  compatibility_change_threshold?: number;
  compatibility_changes?: boolean;
  critical_deadline?: boolean;
  critical_hours?: number;
  document_updates?: boolean;
  minimum_compatibility_score?: number;
  minimum_information_completeness?: number;
  monitor_failures?: boolean;
  new_documents?: boolean;
  new_potential?: boolean;
  new_review_first?: boolean;
  outcome_changes?: boolean;
  partner_needed?: boolean;
  process_closed?: boolean;
  urgent_days?: number;
  urgent_deadline?: boolean;
}
export interface OpportunityMonitorFilters {
  /**
   * @maxItems 500
   */
  candidate_ids?: string[];
  /**
   * @maxItems 10
   */
  search_requests?:
    | []
    | [ExternalProcurementSearchRequest]
    | [ExternalProcurementSearchRequest, ExternalProcurementSearchRequest]
    | [
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
      ]
    | [
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
      ]
    | [
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
      ]
    | [
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
      ]
    | [
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
      ]
    | [
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
      ]
    | [
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
      ]
    | [
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
        ExternalProcurementSearchRequest,
      ];
}
export interface ExternalProcurementSearchRequest {
  closing_from?: string | null;
  closing_to?: string | null;
  department?: string | null;
  entity_name?: string | null;
  limit?: number;
  max_value?: number | string | null;
  min_value?: number | string | null;
  modality?: string | null;
  municipality?: string | null;
  offset?: number;
  process_code?: string | null;
  published_from?: string | null;
  published_to?: string | null;
  query?: string | null;
  source_system?: "SECOP_II" | "SECOP_I";
  status?: string | null;
}
export interface OpportunityMonitorDetail {
  alert_rules: OpportunityAlertRules;
  baseline_run_id?: string | null;
  company_profile_id: string;
  company_snapshot_id: string;
  consecutive_failures?: number;
  created_at: string;
  description?: string | null;
  filters: OpportunityMonitorFilters;
  frequency: OpportunityMonitorFrequency;
  id: string;
  last_failure_at?: string | null;
  last_run_at?: string | null;
  last_success_at?: string | null;
  latest_runs?: OpportunityMonitorRunSummary[];
  name: string;
  next_run_at?: string | null;
  policy_hash: string;
  policy_version: string;
  source_systems: ExternalProcurementSourceSystem[];
  status: OpportunityMonitorStatus;
  timezone: string;
  updated_at: string;
}
export interface OpportunityMonitorList {
  items: OpportunityMonitorSummary[];
  limit: number;
  offset: number;
  total: number;
}
export interface OpportunityMonitorSummary {
  baseline_run_id?: string | null;
  company_profile_id: string;
  company_snapshot_id: string;
  consecutive_failures?: number;
  created_at: string;
  description?: string | null;
  frequency: OpportunityMonitorFrequency;
  id: string;
  last_failure_at?: string | null;
  last_run_at?: string | null;
  last_success_at?: string | null;
  name: string;
  next_run_at?: string | null;
  policy_hash: string;
  policy_version: string;
  source_systems: ExternalProcurementSourceSystem[];
  status: OpportunityMonitorStatus;
  timezone: string;
  updated_at: string;
}
export interface OpportunityMonitorRunDetail {
  alert_count?: number;
  candidate_count?: number;
  changed_candidate_count?: number;
  created_at: string;
  discovery_run_id?: string | null;
  error_code?: string | null;
  error_message?: string | null;
  finished_at?: string | null;
  id: string;
  input_digest: string;
  monitor_id: string;
  new_candidate_count?: number;
  scheduled_for: string;
  started_at?: string | null;
  status: OpportunityMonitorRunStatus;
  trigger_type: OpportunityMonitorTriggerType;
  warning_count?: number;
}
export interface OpportunityMonitorUpdateRequest {
  alert_rules?: OpportunityAlertRules | null;
  company_snapshot_id?: string | null;
  description?: string | null;
  filters?: OpportunityMonitorFilters | null;
  frequency?: OpportunityMonitorFrequency | null;
  name?: string | null;
  source_systems?:
    | [ExternalProcurementSourceSystem]
    | [ExternalProcurementSourceSystem, ExternalProcurementSourceSystem]
    | null;
  timezone?: string | null;
}
export interface OpportunityMonitoringReadiness {
  active_monitors?: number;
  enabled: boolean;
  pending_runs?: number;
  ready: boolean;
  reasons?: string[];
}
export interface OpportunityAlertUnreadCount {
  count: number;
}
