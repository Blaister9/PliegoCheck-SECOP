// Archivo generado automaticamente desde financial-evaluation.schema.json
// (pnpm schemas:generate). No editar a mano: la definicion canonica son los
// modelos Pydantic de packages/schemas/src/pliegocheck_schemas/.

export type FinancialMetricType =
  | "CURRENT_ASSETS"
  | "CURRENT_LIABILITIES"
  | "TOTAL_ASSETS"
  | "TOTAL_LIABILITIES"
  | "EQUITY"
  | "REVENUE"
  | "OPERATING_PROFIT"
  | "NET_PROFIT"
  | "INTEREST_EXPENSE"
  | "WORKING_CAPITAL"
  | "LIQUIDITY_RATIO"
  | "DEBT_RATIO"
  | "INTEREST_COVERAGE"
  | "RETURN_ON_ASSETS"
  | "RETURN_ON_EQUITY"
  | "OTHER";
export type FinancialCalculationStatus =
  | "COMPLETED"
  | "MISSING_INPUT"
  | "DIVISION_BY_ZERO"
  | "UNIT_MISMATCH"
  | "CURRENCY_MISMATCH"
  | "CONFLICTING_INPUT"
  | "FAILED";
export type FinancialEvaluationRunStatus =
  "PENDING" | "PROCESSING" | "COMPLETED" | "COMPLETED_WITH_WARNINGS" | "FAILED" | "CANCELLED";
export type FinancialEvaluationJobStatus =
  "PENDING" | "PROCESSING" | "COMPLETED" | "COMPLETED_WITH_WARNINGS" | "FAILED" | "CANCELLED";
export type FinancialMetricUsability =
  "VERIFIED" | "SUPPORTED" | "DECLARED_ONLY" | "EXPIRED" | "REJECTED" | "CONFLICTING" | "MISSING";
export type FinancialExplanationCode =
  | "VALUE_MEETS_MINIMUM"
  | "VALUE_BELOW_MINIMUM"
  | "VALUE_MEETS_MAXIMUM"
  | "VALUE_EXCEEDS_MAXIMUM"
  | "VALUE_WITHIN_RANGE"
  | "VALUE_OUTSIDE_RANGE"
  | "METRIC_MISSING"
  | "PERIOD_NOT_RESOLVED"
  | "DECLARED_VALUE_NOT_VERIFIED"
  | "EVIDENCE_CONFLICT"
  | "UNIT_MISMATCH"
  | "CURRENCY_MISMATCH"
  | "DIVISION_BY_ZERO"
  | "RULE_AMBIGUOUS"
  | "RULE_UNSUPPORTED"
  | "NOT_FINANCIAL_REQUIREMENT";
export type FinancialOperator =
  | "GREATER_THAN"
  | "GREATER_THAN_OR_EQUAL"
  | "LESS_THAN"
  | "LESS_THAN_OR_EQUAL"
  | "EQUAL"
  | "NOT_EQUAL"
  | "BETWEEN_INCLUSIVE"
  | "BETWEEN_EXCLUSIVE"
  | "EXISTS"
  | "NOT_EXISTS";
export type FinancialEvaluationResultStatus =
  | "COMPLIES"
  | "DOES_NOT_COMPLY"
  | "PARTIAL"
  | "UNKNOWN"
  | "NOT_APPLICABLE"
  | "CONFLICTING_EVIDENCE";
export type FinancialRuleMappingStatus =
  "MAPPED" | "PARTIALLY_MAPPED" | "AMBIGUOUS" | "UNSUPPORTED" | "INVALID";
export type FinancialPeriodPolicy =
  | "EXACT_YEAR"
  | "LATEST_AVAILABLE"
  | "LATEST_BEFORE_PROCESS_CLOSING"
  | "RUP_REFERENCE_PERIOD"
  | "MANUAL_SELECTION"
  | "UNKNOWN";
export type FinancialRuleType =
  | "DIRECT_METRIC"
  | "DERIVED_METRIC"
  | "RANGE"
  | "COMPOSITE_ALL"
  | "COMPOSITE_ANY"
  | "INFORMATIONAL"
  | "UNSUPPORTED";
export type FinancialRuleSourceBasis =
  "EXPLICIT_EXPECTED_VALUE" | "EXPLICIT_DESCRIPTION" | "MANUAL_OVERRIDE" | "UNKNOWN";
export type FinancialEvaluationReviewStatus = "PENDING" | "CONFIRMED" | "OVERRIDDEN" | "REJECTED";

/**
 * Contenedor para generar JSON Schema con defs compartidos.
 */
export interface FinancialEvaluation {
  calculation: FinancialMetricCalculation;
  completeness: FinancialEvaluationCompleteness;
  evaluation_list: FinancialEvaluationList;
  formula_version: FinancialFormulaVersion;
  job: FinancialEvaluationJobSummary;
  metric_input: FinancialMetricInput;
  queue_response: FinancialEvaluationQueueResponse;
  request: FinancialEvaluationRequest;
  result: FinancialEvaluationResult;
  result_detail: FinancialEvaluationResultDetail;
  result_list: FinancialEvaluationResultList;
  retry_request: FinancialEvaluationRetryRequest;
  review_request: FinancialEvaluationResultReviewRequest;
  rule: FinancialRequirementRule;
  rule_update: FinancialRequirementRuleUpdate;
  run_detail: FinancialEvaluationRunDetail;
  run_summary: FinancialEvaluationRunSummary;
  schema_version?: "1.0.0";
}
export interface FinancialMetricCalculation {
  created_at: string;
  financial_period_id: string | null;
  formula_name: string;
  formula_version: string;
  id: string;
  input_values: {
    [k: string]: unknown;
  };
  metric_type: FinancialMetricType;
  raw_result: number | string | null;
  rounded_result: number | string | null;
  run_id: string;
  status: FinancialCalculationStatus;
  unit: string | null;
  warning_codes?: string[];
}
export interface FinancialEvaluationCompleteness {
  ambiguous_rule_count: number;
  conflicting_evidence_count: number;
  has_financial_metrics: boolean;
  has_financial_periods: boolean;
  has_financial_requirements: boolean;
  has_published_company_snapshot: boolean;
  missing_metric_count: number;
  ready_for_review: boolean;
  run_id: string;
}
export interface FinancialEvaluationList {
  items: FinancialEvaluationRunSummary[];
  limit: number;
  offset: number;
  total: number;
}
export interface FinancialEvaluationRunSummary {
  company_id: string;
  company_profile_snapshot_id: string;
  complies_count: number;
  conflicting_count: number;
  created_at: string;
  does_not_comply_count: number;
  error_code: string | null;
  error_message: string | null;
  evaluated_count: number;
  finished_at: string | null;
  id: string;
  input_digest: string;
  job_id: string;
  normalization_run_id: string;
  not_applicable_count: number;
  partial_count: number;
  process_id: string;
  requirement_count: number;
  rule_version: string;
  started_at: string | null;
  status: FinancialEvaluationRunStatus;
  unknown_count: number;
  updated_at: string;
  warning_count: number;
}
export interface FinancialFormulaVersion {
  created_at?: string | null;
  expression: string;
  formula_name: string;
  is_active?: boolean;
  output_metric_type: FinancialMetricType;
  output_unit?: string | null;
  required_metric_types: FinancialMetricType[];
  rounding_policy: string;
  semantic_version: string;
}
export interface FinancialEvaluationJobSummary {
  attempt_count: number;
  company_id: string;
  company_profile_snapshot_id: string;
  created_at: string;
  force: boolean;
  id: string;
  max_attempts: number;
  normalization_run_id: string;
  process_id: string;
  status: FinancialEvaluationJobStatus;
  updated_at: string;
}
export interface FinancialMetricInput {
  currency: string | null;
  evidence_ids?: string[];
  evidence_status: FinancialMetricUsability;
  metric_type: FinancialMetricType;
  period_end: string | null;
  period_start: string | null;
  record_id: string | null;
  review_status?: string | null;
  source_type?: string | null;
  unit: string | null;
  value: number | string | null;
}
export interface FinancialEvaluationQueueResponse {
  job: FinancialEvaluationJobSummary;
  run: FinancialEvaluationRunSummary;
}
export interface FinancialEvaluationRequest {
  company_id: string;
  company_profile_snapshot_id: string;
  force?: boolean;
  normalization_run_id: string;
}
export interface FinancialEvaluationResult {
  actual_unit?: string | null;
  actual_value?: number | string | null;
  calculation_id?: string | null;
  created_at: string;
  currency?: string | null;
  explanation_code: FinancialExplanationCode;
  explanation_parameters?: {
    [k: string]: unknown;
  };
  financial_period_id?: string | null;
  financial_rule_id: string | null;
  id: string;
  metric_type: FinancialMetricType | null;
  operator: FinancialOperator | null;
  required_max_value?: number | string | null;
  required_min_value?: number | string | null;
  required_unit?: string | null;
  required_value?: number | string | null;
  requirement_id: string;
  requires_human_review?: boolean;
  review_notes?: string | null;
  review_status?: "PENDING" | "CONFIRMED" | "OVERRIDDEN" | "REJECTED";
  reviewed_at?: string | null;
  reviewed_status?: FinancialEvaluationResultStatus | null;
  run_id: string;
  status: FinancialEvaluationResultStatus;
  updated_at: string;
}
export interface FinancialEvaluationResultDetail {
  actual_unit?: string | null;
  actual_value?: number | string | null;
  calculation?: FinancialMetricCalculation | null;
  calculation_id?: string | null;
  created_at: string;
  currency?: string | null;
  evidence?: {
    [k: string]: unknown;
  };
  explanation_code: FinancialExplanationCode;
  explanation_parameters?: {
    [k: string]: unknown;
  };
  financial_period_id?: string | null;
  financial_rule_id: string | null;
  id: string;
  metric_inputs?: FinancialMetricInput[];
  metric_type: FinancialMetricType | null;
  operator: FinancialOperator | null;
  required_max_value?: number | string | null;
  required_min_value?: number | string | null;
  required_unit?: string | null;
  required_value?: number | string | null;
  requirement?: {
    [k: string]: unknown;
  };
  requirement_id: string;
  requires_human_review?: boolean;
  review_notes?: string | null;
  review_status?: "PENDING" | "CONFIRMED" | "OVERRIDDEN" | "REJECTED";
  reviewed_at?: string | null;
  reviewed_status?: FinancialEvaluationResultStatus | null;
  reviews?: {
    [k: string]: unknown;
  }[];
  rule?: FinancialRequirementRule | null;
  run_id: string;
  status: FinancialEvaluationResultStatus;
  updated_at: string;
}
export interface FinancialRequirementRule {
  condition_group?: {
    [k: string]: unknown;
  };
  created_at: string;
  currency?: string | null;
  id: string;
  is_manual_override?: boolean;
  mapping_status: FinancialRuleMappingStatus;
  mapping_warnings?: string[];
  metric_type: FinancialMetricType | null;
  normalization_run_id: string;
  operator: FinancialOperator | null;
  period_policy: FinancialPeriodPolicy;
  period_year?: number | null;
  required_max_value?: number | string | null;
  required_min_value?: number | string | null;
  required_value?: number | string | null;
  requirement_id: string;
  requires_human_review?: boolean;
  rule_type: FinancialRuleType;
  source_basis: FinancialRuleSourceBasis;
  unit?: string | null;
  updated_at: string;
  version: number;
}
export interface FinancialEvaluationResultList {
  items: FinancialEvaluationResult[];
  limit: number;
  offset: number;
  total: number;
}
export interface FinancialEvaluationRetryRequest {
  force?: boolean;
}
export interface FinancialEvaluationResultReviewRequest {
  override_reason?: string | null;
  override_result?: FinancialEvaluationResultStatus | null;
  review_notes?: string | null;
  review_status: FinancialEvaluationReviewStatus;
}
export interface FinancialRequirementRuleUpdate {
  condition_group?: {
    [k: string]: unknown;
  } | null;
  currency?: string | null;
  mapping_warnings?: string[] | null;
  metric_type?: FinancialMetricType | null;
  operator?: FinancialOperator | null;
  override_reason?: string | null;
  period_policy?: FinancialPeriodPolicy | null;
  period_year?: number | null;
  required_max_value?: number | string | null;
  required_min_value?: number | string | null;
  required_value?: number | string | null;
  requires_human_review?: boolean | null;
  rule_type?: FinancialRuleType | null;
  unit?: string | null;
}
export interface FinancialEvaluationRunDetail {
  calculations?: FinancialMetricCalculation[];
  company_id: string;
  company_profile_snapshot_id: string;
  complies_count: number;
  conflicting_count: number;
  created_at: string;
  does_not_comply_count: number;
  error_code: string | null;
  error_message: string | null;
  evaluated_count: number;
  events?: {
    [k: string]: unknown;
  }[];
  finished_at: string | null;
  id: string;
  input_digest: string;
  input_manifest: {
    [k: string]: unknown;
  };
  job?: FinancialEvaluationJobSummary | null;
  job_id: string;
  normalization_run_id: string;
  not_applicable_count: number;
  partial_count: number;
  process_id: string;
  requirement_count: number;
  results?: FinancialEvaluationResult[];
  rule_version: string;
  rules?: FinancialRequirementRule[];
  started_at: string | null;
  status: FinancialEvaluationRunStatus;
  unknown_count: number;
  updated_at: string;
  warning_count: number;
}
