// Archivo generado automaticamente desde decision.schema.json
// (pnpm schemas:generate). No editar a mano: la definicion canonica son los
// modelos Pydantic de packages/schemas/src/pliegocheck_schemas/.

export type DecisionActionType =
  | "PROVIDE_INFORMATION"
  | "RESOLVE_CONFLICT"
  | "REVIEW_REQUIREMENT"
  | "REVIEW_EVIDENCE"
  | "CORRECT_FINANCIAL_GAP"
  | "SEEK_PARTNER"
  | "COMPLETE_MANDATORY_EVALUATION"
  | "CONFIRM_SUBSANABILITY"
  | "DO_NOT_SUBMIT"
  | "OTHER";
export type DecisionActionPriority = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
export type DecisionActionStatus = "OPEN" | "ACKNOWLEDGED" | "RESOLVED" | "DISMISSED";
export type DecisionCoverageStatus = "COMPLETE" | "PARTIAL" | "MISSING" | "NOT_REQUIRED";
export type DecisionFindingApplicability =
  "MANDATORY" | "OPTIONAL" | "INFORMATIONAL" | "NOT_APPLICABLE";
export type DecisionEvaluationDomain =
  | "FINANCIAL"
  | "ORGANIZATIONAL"
  | "LEGAL"
  | "EXPERIENCE"
  | "TECHNICAL"
  | "WORKFORCE"
  | "DOCUMENTARY"
  | "GUARANTEE"
  | "SCHEDULE"
  | "ECONOMIC"
  | "OPERATIONAL"
  | "RISK_AND_INELIGIBILITY"
  | "OTHER";
/**
 * Outcome canonico de un hallazgo de entrada.
 */
export type DecisionFindingOutcome =
  | "COMPLIES"
  | "DOES_NOT_COMPLY"
  | "PARTIAL"
  | "UNKNOWN"
  | "NOT_APPLICABLE"
  | "CONFLICTING_EVIDENCE"
  | "NOT_EVALUATED";
export type DecisionFindingSourceType =
  "FINANCIAL_EVALUATION" | "SPECIALIZED_EVALUATION" | "SYNTHETIC" | "MISSING_ADAPTER";
export type DecisionJobStatus =
  "PENDING" | "PROCESSING" | "COMPLETED" | "COMPLETED_WITH_WARNINGS" | "FAILED" | "CANCELLED";
/**
 * Resultados finales permitidos, en orden de precedencia descendente.
 */
export type DecisionOutcome =
  "NO_CARGAR" | "NO_GO" | "PENDIENTE_INFORMACION" | "BUSCAR_ALIADO" | "GO_CONDICIONADO" | "GO";
/**
 * Codigos deterministicos de explicacion. La UI los traduce a mensajes.
 */
export type DecisionReasonCode =
  | "FULL_MANDATORY_COVERAGE"
  | "MANDATORY_REQUIREMENT_NOT_EVALUATED"
  | "MANDATORY_REQUIREMENT_UNKNOWN"
  | "MANDATORY_REQUIREMENT_PARTIAL"
  | "MANDATORY_REQUIREMENT_UNRESOLVED"
  | "BLOCKING_REQUIREMENT_FAILED"
  | "NON_SUBSANABLE_REQUIREMENT_FAILED"
  | "CRITICAL_EVIDENCE_CONFLICT"
  | "PARTNER_SOLVABLE_GAP_CONFIRMED"
  | "REMEDIABLE_CONDITION_PENDING"
  | "SUBMISSION_BLOCKER_CONFIRMED"
  | "ALL_MANDATORY_REQUIREMENTS_COMPLY"
  | "HUMAN_REVIEW_PENDING"
  | "ADAPTER_NOT_AVAILABLE";
export type DecisionRunStatus =
  "PENDING" | "PROCESSING" | "COMPLETED" | "COMPLETED_WITH_WARNINGS" | "FAILED" | "CANCELLED";
export type DecisionReviewAction = "CONFIRM" | "OVERRIDE" | "REJECT";
export type DecisionRuleStatus = "TRIGGERED" | "NOT_TRIGGERED" | "NOT_APPLICABLE" | "INDETERMINATE";

/**
 * Contenedor para generar JSON Schema con defs compartidos.
 */
export interface Decision {
  action_item: DecisionActionItem;
  action_update_request: DecisionActionUpdateRequest;
  coverage_category: DecisionCoverageCategory;
  coverage_summary: DecisionCoverageSummary;
  input_finding: DecisionInputFinding;
  job_summary: DecisionJobSummary;
  policy_summary: DecisionPolicySummary;
  queue_response: DecisionQueueResponse;
  readiness: DecisionReadiness;
  request: DecisionRequest;
  retry_request: DecisionRetryRequest;
  review_record: DecisionReviewRecord;
  review_request: DecisionReviewRequest;
  review_response: DecisionReviewResponse;
  rule_evaluation: DecisionRuleEvaluation;
  run_detail: DecisionRunDetail;
  run_list: DecisionRunList;
  run_summary: DecisionRunSummary;
  schema_version?: "1.0.0";
}
export interface DecisionActionItem {
  action_type: DecisionActionType;
  created_at: string;
  decision_run_id: string;
  description_code: string;
  due_at: string | null;
  finding_ids?: string[];
  id: string;
  parameters?: {
    [k: string]: unknown;
  };
  priority: DecisionActionPriority;
  requirement_ids?: string[];
  status: DecisionActionStatus;
  title_code: string;
  updated_at: string;
}
export interface DecisionActionUpdateRequest {
  note?: string | null;
  status: DecisionActionStatus;
}
export interface DecisionCoverageCategory {
  adapter_available: boolean;
  category: string;
  coverage_status: DecisionCoverageStatus;
  evaluated_total: number;
  mandatory_total: number;
  not_evaluated_total: number;
  outcomes?: {
    [k: string]: number;
  };
  requirements_total: number;
}
/**
 * Cobertura mediante conteos claros; nunca un score ni probabilidad.
 */
export interface DecisionCoverageSummary {
  blocking_failure_total: number;
  categories?: DecisionCoverageCategory[];
  complies_total: number;
  conflicting_total: number;
  does_not_comply_total: number;
  evaluated_total: number;
  human_review_pending_total: number;
  mandatory_applicable_total: number;
  not_applicable_total: number;
  not_evaluated_total: number;
  optional_total: number;
  partial_total: number;
  partner_gap_total: number;
  remediable_gap_total: number;
  requirements_total: number;
  submission_blocker_total: number;
  unknown_total: number;
}
/**
 * Hallazgo canonico de entrada al motor. Nunca modifica la fuente.
 */
export interface DecisionInputFinding {
  applicability: DecisionFindingApplicability;
  category: string;
  condition_codes?: string[];
  created_at?: string | null;
  criticality: string;
  criticality_basis: string;
  evaluation_domain: DecisionEvaluationDomain;
  evidence_quality?: string | null;
  evidence_references?: {
    [k: string]: unknown;
  }[];
  id: string;
  is_blocking?: boolean;
  is_remediable?: boolean;
  modality: string;
  outcome: DecisionFindingOutcome;
  partner_solvable?: boolean;
  requirement_id: string;
  requirement_stable_key: string;
  requires_human_review?: boolean;
  review_status?: string | null;
  scope: string;
  source_result_id: string | null;
  source_run_id: string | null;
  source_type: DecisionFindingSourceType;
  submission_blocker?: boolean;
  subsanability: string;
  subsanability_basis: string;
  warning_codes?: string[];
}
export interface DecisionJobSummary {
  attempt_count: number;
  company_id: string;
  company_profile_snapshot_id: string;
  created_at: string;
  financial_evaluation_run_id: string;
  force: boolean;
  id: string;
  last_error_code?: string | null;
  max_attempts: number;
  normalization_run_id: string;
  process_id: string;
  status: DecisionJobStatus;
  updated_at: string;
}
export interface DecisionPolicySummary {
  content_sha256: string;
  created_at?: string | null;
  engine_version: string;
  id?: string | null;
  is_active: boolean;
  policy_name: string;
  semantic_version: string;
}
export interface DecisionQueueResponse {
  job: DecisionJobSummary;
  reused_existing_run?: boolean;
  run: DecisionRunSummary;
}
export interface DecisionRunSummary {
  action_count: number;
  company_id: string;
  company_profile_snapshot_id: string;
  created_at: string;
  effective_outcome: DecisionOutcome | null;
  engine_outcome: DecisionOutcome | null;
  engine_version: string;
  error_code: string | null;
  error_message: string | null;
  financial_evaluation_run_id: string;
  finding_count: number;
  finished_at: string | null;
  id: string;
  input_digest: string;
  job_id: string;
  normalization_run_id: string;
  policy_name: string;
  policy_version: string;
  process_id: string;
  reason_codes?: DecisionReasonCode[];
  requirement_count: number;
  requires_human_review: boolean;
  reviewed_outcome: DecisionOutcome | null;
  started_at: string | null;
  status: DecisionRunStatus;
  updated_at: string;
  warning_count: number;
  warnings?: string[];
}
/**
 * Diagnostico previo. No ejecuta el motor.
 */
export interface DecisionReadiness {
  available_adapters?: DecisionEvaluationDomain[];
  go_blocked_by_coverage: boolean;
  input_errors?: string[];
  inputs_valid: boolean;
  max_possible_outcome: DecisionOutcome;
  not_evaluated_mandatory_count: number;
  policy?: DecisionPolicySummary | null;
  process_id: string;
  required_categories?: DecisionReadinessCategory[];
  warnings?: string[];
}
export interface DecisionReadinessCategory {
  adapter_available: boolean;
  category: string;
  mandatory_total: number;
  requirements_total: number;
}
export interface DecisionRequest {
  company_id: string;
  company_profile_snapshot_id: string;
  financial_evaluation_run_id: string;
  force?: boolean;
  normalization_run_id: string;
}
export interface DecisionRetryRequest {
  force?: boolean;
}
export interface DecisionReviewRecord {
  action: DecisionReviewAction;
  created_at: string;
  decision_run_id: string;
  id: string;
  original_outcome: DecisionOutcome;
  reason: string | null;
  reviewed_outcome: DecisionOutcome | null;
  reviewer_reference: string;
}
export interface DecisionReviewRequest {
  action: DecisionReviewAction;
  reason?: string | null;
  reviewed_outcome?: DecisionOutcome | null;
}
export interface DecisionReviewResponse {
  review: DecisionReviewRecord;
  run: DecisionRunSummary;
}
export interface DecisionRuleEvaluation {
  created_at?: string | null;
  fact_payload?: {
    [k: string]: unknown;
  };
  finding_ids?: string[];
  id?: string | null;
  priority: number;
  reason_code: DecisionReasonCode | null;
  requirement_ids?: string[];
  rule_code: string;
  rule_version: string;
  status: DecisionRuleStatus;
  suggested_outcome: DecisionOutcome | null;
}
export interface DecisionRunDetail {
  action_count: number;
  actions?: DecisionActionItem[];
  company_id: string;
  company_profile_snapshot_id: string;
  coverage?: DecisionCoverageSummary | null;
  created_at: string;
  effective_outcome: DecisionOutcome | null;
  engine_outcome: DecisionOutcome | null;
  engine_version: string;
  error_code: string | null;
  error_message: string | null;
  events?: {
    [k: string]: unknown;
  }[];
  financial_evaluation_run_id: string;
  finding_count: number;
  findings?: DecisionInputFinding[];
  finished_at: string | null;
  id: string;
  input_digest: string;
  input_manifest?: {
    [k: string]: unknown;
  };
  job?: DecisionJobSummary | null;
  job_id: string;
  normalization_run_id: string;
  policy?: DecisionPolicySummary | null;
  policy_name: string;
  policy_version: string;
  process_id: string;
  reason_codes?: DecisionReasonCode[];
  requirement_count: number;
  requires_human_review: boolean;
  reviewed_outcome: DecisionOutcome | null;
  reviews?: DecisionReviewRecord[];
  rule_evaluations?: DecisionRuleEvaluation[];
  started_at: string | null;
  status: DecisionRunStatus;
  updated_at: string;
  warning_count: number;
  warnings?: string[];
}
export interface DecisionRunList {
  items: DecisionRunSummary[];
  limit: number;
  offset: number;
  total: number;
}
