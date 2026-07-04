// Archivo generado automaticamente desde specialized-evaluation.schema.json
// (pnpm schemas:generate). No editar a mano: la definicion canonica son los
// modelos Pydantic de packages/schemas/src/pliegocheck_schemas/.

export type SpecializedEvaluationDomain =
  | "LEGAL"
  | "EXPERIENCE"
  | "TECHNICAL"
  | "WORKFORCE"
  | "DOCUMENTARY"
  | "GUARANTEE"
  | "OPERATIONAL"
  | "ORGANIZATIONAL"
  | "RISK";
export type SpecializedEvaluationRunStatus =
  "PENDING" | "PROCESSING" | "COMPLETED" | "COMPLETED_WITH_WARNINGS" | "FAILED" | "CANCELLED";
export type SpecializedEvidenceValidationStatus =
  "VERIFIED" | "SUPPORTED" | "DECLARED_ONLY" | "EXPIRED" | "REJECTED" | "CONFLICTING" | "MISSING";
export type SpecializedEvaluationJobStatus =
  "PENDING" | "PROCESSING" | "COMPLETED" | "COMPLETED_WITH_WARNINGS" | "FAILED" | "CANCELLED";
export type SpecializedRuleMappingStatus =
  "MAPPED" | "PARTIALLY_MAPPED" | "AMBIGUOUS" | "UNSUPPORTED" | "INVALID";
export type SpecializedOperator =
  | "EXISTS"
  | "NOT_EXISTS"
  | "EQUAL"
  | "NOT_EQUAL"
  | "CONTAINS"
  | "GREATER_THAN"
  | "GREATER_THAN_OR_EQUAL"
  | "LESS_THAN"
  | "LESS_THAN_OR_EQUAL"
  | "BETWEEN_INCLUSIVE"
  | "IN_SET"
  | "ALL_OF"
  | "ANY_OF";
export type SpecializedRuleType =
  | "DOCUMENT_EXISTS"
  | "REGISTRATION_EXISTS"
  | "REGISTRATION_VALID"
  | "CERTIFICATION_EXISTS"
  | "CERTIFICATION_VALID"
  | "EXPERIENCE_EXISTS"
  | "EXPERIENCE_COUNT"
  | "EXPERIENCE_VALUE"
  | "EXPERIENCE_DURATION"
  | "EXPERIENCE_UNSPSC"
  | "EXPERIENCE_ACTIVITY"
  | "PERSON_ROLE_EXISTS"
  | "PERSON_CREDENTIAL_EXISTS"
  | "PERSON_EXPERIENCE_YEARS"
  | "CAPABILITY_EXISTS"
  | "CAPABILITY_VALUE"
  | "COVERAGE_EXISTS"
  | "COMPOSITE_ALL"
  | "COMPOSITE_ANY"
  | "INFORMATIONAL"
  | "UNSUPPORTED";
export type SpecializedRuleSourceBasis =
  "EXPLICIT_EXPECTED_VALUE" | "EXPLICIT_DESCRIPTION" | "MANUAL_OVERRIDE" | "UNKNOWN";
export type SpecializedExplanationCode =
  | "REQUIREMENT_COMPLIES"
  | "REQUIREMENT_NOT_MET"
  | "REQUIREMENT_PARTIAL"
  | "RULE_AMBIGUOUS"
  | "RULE_UNSUPPORTED"
  | "DATA_MISSING"
  | "DECLARED_ONLY_NOT_ACCEPTED"
  | "EVIDENCE_EXPIRED"
  | "EVIDENCE_REJECTED"
  | "EVIDENCE_CONFLICT"
  | "CURRENCY_MISMATCH"
  | "ACTIVITY_NOT_COMPARABLE"
  | "UNSPSC_NOT_COMPARABLE"
  | "CONSORTIUM_PERCENTAGE_MISSING"
  | "RECORD_NOT_COMPLETED"
  | "NOT_APPLICABLE_DOMAIN";
export type SpecializedEvaluationResultStatus =
  | "COMPLIES"
  | "DOES_NOT_COMPLY"
  | "PARTIAL"
  | "UNKNOWN"
  | "NOT_APPLICABLE"
  | "CONFLICTING_EVIDENCE";
export type SpecializedEvaluationReviewStatus = "PENDING" | "CONFIRMED" | "OVERRIDDEN" | "REJECTED";

export interface SpecializedEvaluation {
  evaluation_list: SpecializedEvaluationList;
  evidence: SpecializedEvaluationEvidence;
  job: SpecializedEvaluationJobSummary;
  queue_response: SpecializedEvaluationQueueResponse;
  readiness: SpecializedEvaluationReadiness;
  request: SpecializedEvaluationRequest;
  result: SpecializedEvaluationResult;
  result_detail: SpecializedEvaluationResultDetail;
  result_list: SpecializedEvaluationResultList;
  retry_request: SpecializedEvaluationRetryRequest;
  review_request: SpecializedEvaluationResultReviewRequest;
  rule: SpecializedRequirementRule;
  rule_update: SpecializedRequirementRuleUpdate;
  run_detail: SpecializedEvaluationRunDetail;
  run_summary: SpecializedEvaluationRunSummary;
  schema_version?: "1.0.0";
}
export interface SpecializedEvaluationList {
  items: SpecializedEvaluationRunSummary[];
  limit: number;
  offset: number;
  total: number;
}
export interface SpecializedEvaluationRunSummary {
  company_id: string;
  company_profile_snapshot_id: string;
  complies_count: number;
  conflicting_count: number;
  created_at: string;
  does_not_comply_count: number;
  domain: SpecializedEvaluationDomain;
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
  status: SpecializedEvaluationRunStatus;
  unknown_count: number;
  updated_at: string;
  warning_count: number;
}
export interface SpecializedEvaluationEvidence {
  company_evidence_document_id?: string | null;
  company_evidence_link_id?: string | null;
  created_at: string;
  evidence_type: string;
  extracted_segment_id?: string | null;
  id: string;
  quoted_text?: string | null;
  requirement_evidence_id?: string | null;
  result_id: string;
  source_location?: {
    [k: string]: unknown;
  };
  validation_status: SpecializedEvidenceValidationStatus;
}
export interface SpecializedEvaluationJobSummary {
  attempt_count: number;
  company_id: string;
  company_profile_snapshot_id: string;
  created_at: string;
  domain: SpecializedEvaluationDomain;
  force: boolean;
  id: string;
  last_error_code?: string | null;
  max_attempts: number;
  normalization_run_id: string;
  process_id: string;
  status: SpecializedEvaluationJobStatus;
  updated_at: string;
}
export interface SpecializedEvaluationQueueResponse {
  job: SpecializedEvaluationJobSummary;
  run: SpecializedEvaluationRunSummary;
}
export interface SpecializedEvaluationReadiness {
  ambiguous_count: number;
  available_domains: SpecializedEvaluationDomain[];
  company_profile_snapshot_id: string;
  domain: SpecializedEvaluationDomain;
  evaluable_count: number;
  normalization_run_id: string;
  process_id: string;
  requirement_count: number;
  rules?: SpecializedRequirementRule[];
  snapshot_published: boolean;
  unsupported_count: number;
  warnings?: string[];
}
export interface SpecializedRequirementRule {
  condition_group?: {
    [k: string]: unknown;
  };
  created_at: string;
  currency?: string | null;
  domain: SpecializedEvaluationDomain;
  expected_max_value?: number | string | null;
  expected_min_value?: number | string | null;
  expected_value?: string | null;
  id: string;
  is_manual_override?: boolean;
  manual_override_payload?: {
    [k: string]: unknown;
  };
  mapping_status: SpecializedRuleMappingStatus;
  mapping_warnings?: string[];
  normalization_run_id: string;
  operator: SpecializedOperator | null;
  period_policy?: string | null;
  requirement_id: string;
  requires_human_review?: boolean;
  rule_type: SpecializedRuleType;
  source_basis: SpecializedRuleSourceBasis;
  subject: string | null;
  unit?: string | null;
  updated_at: string;
  version: number;
}
export interface SpecializedEvaluationRequest {
  company_id: string;
  company_profile_snapshot_id: string;
  domain: SpecializedEvaluationDomain;
  force?: boolean;
  normalization_run_id: string;
}
export interface SpecializedEvaluationResult {
  actual_value?: string | null;
  created_at: string;
  domain: SpecializedEvaluationDomain;
  expected_value?: string | null;
  explanation_code: SpecializedExplanationCode;
  explanation_parameters?: {
    [k: string]: unknown;
  };
  id: string;
  operator: SpecializedOperator | null;
  requirement_id: string;
  requires_human_review?: boolean;
  review_notes?: string | null;
  review_status?: "PENDING" | "CONFIRMED" | "OVERRIDDEN" | "REJECTED";
  reviewed_status?: SpecializedEvaluationResultStatus | null;
  rule_type: SpecializedRuleType;
  run_id: string;
  source_record_id?: string | null;
  source_record_type?: string | null;
  specialized_rule_id: string | null;
  status: SpecializedEvaluationResultStatus;
  subject: string | null;
  unit?: string | null;
  updated_at: string;
}
export interface SpecializedEvaluationResultDetail {
  actual_value?: string | null;
  created_at: string;
  domain: SpecializedEvaluationDomain;
  evidence?: SpecializedEvaluationEvidence[];
  expected_value?: string | null;
  explanation_code: SpecializedExplanationCode;
  explanation_parameters?: {
    [k: string]: unknown;
  };
  id: string;
  operator: SpecializedOperator | null;
  requirement?: {
    [k: string]: unknown;
  };
  requirement_id: string;
  requires_human_review?: boolean;
  review_notes?: string | null;
  review_status?: "PENDING" | "CONFIRMED" | "OVERRIDDEN" | "REJECTED";
  reviewed_status?: SpecializedEvaluationResultStatus | null;
  reviews?: {
    [k: string]: unknown;
  }[];
  rule?: SpecializedRequirementRule | null;
  rule_type: SpecializedRuleType;
  run_id: string;
  source_record_id?: string | null;
  source_record_type?: string | null;
  specialized_rule_id: string | null;
  status: SpecializedEvaluationResultStatus;
  subject: string | null;
  unit?: string | null;
  updated_at: string;
}
export interface SpecializedEvaluationResultList {
  items: SpecializedEvaluationResult[];
  limit: number;
  offset: number;
  total: number;
}
export interface SpecializedEvaluationRetryRequest {
  force?: boolean;
}
export interface SpecializedEvaluationResultReviewRequest {
  override_reason?: string | null;
  override_result?: SpecializedEvaluationResultStatus | null;
  review_notes?: string | null;
  review_status: SpecializedEvaluationReviewStatus;
}
export interface SpecializedRequirementRuleUpdate {
  condition_group?: {
    [k: string]: unknown;
  } | null;
  currency?: string | null;
  domain?: SpecializedEvaluationDomain | null;
  expected_max_value?: number | string | null;
  expected_min_value?: number | string | null;
  expected_value?: string | null;
  mapping_warnings?: string[] | null;
  operator?: SpecializedOperator | null;
  override_reason?: string | null;
  period_policy?: string | null;
  requires_human_review?: boolean | null;
  rule_type?: SpecializedRuleType | null;
  subject?: string | null;
  unit?: string | null;
}
export interface SpecializedEvaluationRunDetail {
  company_id: string;
  company_profile_snapshot_id: string;
  complies_count: number;
  conflicting_count: number;
  created_at: string;
  does_not_comply_count: number;
  domain: SpecializedEvaluationDomain;
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
  job?: SpecializedEvaluationJobSummary | null;
  job_id: string;
  normalization_run_id: string;
  not_applicable_count: number;
  partial_count: number;
  process_id: string;
  requirement_count: number;
  results?: SpecializedEvaluationResult[];
  rule_version: string;
  rules?: SpecializedRequirementRule[];
  started_at: string | null;
  status: SpecializedEvaluationRunStatus;
  unknown_count: number;
  updated_at: string;
  warning_count: number;
}
