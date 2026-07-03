// Archivo generado automaticamente desde requirement-normalization.schema.json
// (pnpm schemas:generate). No editar a mano: la definicion canonica son los
// modelos Pydantic de packages/schemas/src/pliegocheck_schemas/.

/**
 * Categorias iniciales de requisitos.
 */
export type RequirementCategory =
  | "LEGAL"
  | "FINANCIAL"
  | "ORGANIZATIONAL"
  | "EXPERIENCE"
  | "TECHNICAL"
  | "WORKFORCE"
  | "GUARANTEE"
  | "SCHEDULE"
  | "ECONOMIC"
  | "OPERATIONAL"
  | "DOCUMENTARY"
  | "RISK_AND_INELIGIBILITY";
export type RequirementCriticality =
  "BLOCKING" | "HIGH" | "MEDIUM" | "LOW" | "INFORMATIONAL" | "UNKNOWN";
export type RequirementBasis = "EXPLICIT" | "INFERRED" | "UNKNOWN";
export type RequirementEvidenceRole = "PRIMARY" | "SUPPORTING" | "CONFLICTING";
export type RequirementModality =
  "MANDATORY" | "OPTIONAL" | "CONDITIONAL" | "PROHIBITED" | "UNKNOWN";
export type RequirementScope =
  | "PROPOSAL_SUBMISSION"
  | "HABILITATING"
  | "SCORING"
  | "CONTRACT_EXECUTION"
  | "INFORMATIONAL"
  | "UNKNOWN";
export type RequirementSubsanability = "SUBSANABLE" | "NON_SUBSANABLE" | "CONDITIONAL" | "UNKNOWN";
export type RequirementNormalizationStatus =
  "PENDING" | "PROCESSING" | "COMPLETED" | "COMPLETED_WITH_WARNINGS" | "FAILED" | "CANCELLED";
export type RequirementRelationType =
  | "INDEPENDENT"
  | "EXACT_DUPLICATE"
  | "POTENTIAL_DUPLICATE"
  | "POTENTIAL_CONFLICT"
  | "POTENTIAL_AMENDMENT";
export type NormalizationProvider = "openai" | "fake";
export type RequirementEvidenceStatus =
  "VALIDATED" | "PARTIALLY_VALIDATED" | "REJECTED_UNSUPPORTED" | "UNKNOWN";
export type RequirementReviewStatus = "PENDING" | "IN_REVIEW" | "ACCEPTED" | "REJECTED";
export type RejectedCandidateReason =
  | "SCHEMA_INVALID"
  | "REJECTED_UNSUPPORTED"
  | "INVALID_SEGMENT"
  | "QUOTE_NOT_FOUND"
  | "OUTSIDE_SNAPSHOT"
  | "LOCATION_MISMATCH"
  | "FORBIDDEN_DECISION"
  | "EXACT_DUPLICATE";
export type RequirementEvidenceValidationStatus =
  "VALID" | "INVALID_SEGMENT" | "QUOTE_NOT_FOUND" | "OUTSIDE_SNAPSHOT" | "LOCATION_MISMATCH";

/**
 * Contenedor para generar JSON Schema conjunto de Microfase 4.
 */
export interface RequirementNormalization {
  agent_output: RequirementNormalizationAgentOutput;
  batch_summary: NormalizationBatchSummary;
  consolidation_output: RequirementConsolidationAgentOutput;
  create_request: NormalizationCreateRequest;
  create_response: NormalizationCreateResponse;
  job_summary: NormalizationJobSummary;
  normalized_requirement: NormalizedRequirement;
  prompt_version: PromptVersionSummary;
  rejected_candidate: RejectedRequirementCandidate;
  requirement_detail: RequirementDetail;
  requirement_evidence: RequirementEvidence;
  requirement_list: RequirementList;
  requirement_relation: RequirementRelation;
  retry_response: NormalizationRetryResponse;
  run_detail: NormalizationRunDetail;
  run_list: NormalizationRunList;
  run_summary: NormalizationRunSummary;
}
/**
 * Structured Output estricto de RequirementNormalizationAgent.
 */
export interface RequirementNormalizationAgentOutput {
  agent: "RequirementNormalizationAgent";
  batch_index: number;
  candidates: RequirementCandidate[];
  process_id: string;
  prompt_version: string;
  schema_version: "2.0.0";
  warnings: string[];
}
/**
 * Candidato producido por RequirementNormalizationAgent.
 */
export interface RequirementCandidate {
  candidate_id: string;
  category: RequirementCategory;
  condition_text: string | null;
  confidence: number;
  criticality: RequirementCriticality;
  criticality_basis: RequirementBasis;
  description: string;
  evidence: RequirementCandidateEvidence[];
  expected_value: ExpectedValue | null;
  modality: RequirementModality;
  requires_human_review: boolean;
  scope: RequirementScope;
  subsanability: RequirementSubsanability;
  subsanability_basis: RequirementBasis;
  uncertainty_reason: string | null;
}
/**
 * Evidencia propuesta por el agente para un candidato.
 */
export interface RequirementCandidateEvidence {
  evidence_role: RequirementEvidenceRole;
  quote_end: number | null;
  quote_start: number | null;
  quoted_text: string;
  segment_id: string;
  source_location: SourceLocation;
}
/**
 * Ubicacion normalizada dentro del segmento de origen.
 */
export interface SourceLocation {
  line_end: number | null;
  line_start: number | null;
  page_number: number | null;
  paragraph_index: number | null;
  row_end: number | null;
  row_start: number | null;
  section: string | null;
  sheet_name: string | null;
  table_index: number | null;
}
/**
 * Valor exigido por el pliego cuando existe soporte explicito.
 */
export interface ExpectedValue {
  raw_text: string | null;
  unit: string | null;
  value: string | number | boolean | null;
}
export interface NormalizationBatchSummary {
  batch_index: number;
  candidate_count: number;
  created_at: string;
  error_code: string | null;
  error_message: string | null;
  finished_at: string | null;
  id: string;
  input_digest: string;
  input_tokens: number;
  output_tokens: number;
  provider_response_id: string | null;
  reasoning_tokens: number;
  run_id: string;
  segment_ids: string[];
  started_at: string | null;
  status: RequirementNormalizationStatus;
}
/**
 * Structured Output estricto de RequirementConsolidationAgent.
 */
export interface RequirementConsolidationAgentOutput {
  agent: "RequirementConsolidationAgent";
  process_id: string;
  prompt_version: string;
  relations: RequirementRelationProposal[];
  schema_version: "2.0.0";
  warnings: string[];
}
/**
 * Relacion propuesta por RequirementConsolidationAgent.
 */
export interface RequirementRelationProposal {
  confidence: number;
  evidence_segment_ids: string[];
  explanation: string;
  relation_type: RequirementRelationType;
  requires_human_review: boolean;
  source_candidate_id: string;
  target_candidate_id: string;
}
export interface NormalizationCreateRequest {
  document_ids?: string[] | null;
  force?: boolean;
}
export interface NormalizationCreateResponse {
  job: NormalizationJobSummary;
  run: NormalizationRunSummary;
}
export interface NormalizationJobSummary {
  attempt_count: number;
  available_at: string;
  created_at: string;
  finished_at: string | null;
  force: boolean;
  id: string;
  last_error_code: string | null;
  last_error_message: string | null;
  max_attempts: number;
  priority: number;
  process_id: string;
  run_id: string | null;
  started_at: string | null;
  status: RequirementNormalizationStatus;
  updated_at: string;
}
export interface NormalizationRunSummary {
  accepted_requirement_count: number;
  batch_count: number;
  candidate_count: number;
  consolidation_prompt_version_id: string;
  created_at: string;
  error_code: string | null;
  error_message: string | null;
  finished_at: string | null;
  id: string;
  input_digest: string;
  input_tokens: number;
  job_id: string;
  model: string;
  output_tokens: number;
  process_id: string;
  prompt_version_id: string;
  provider: NormalizationProvider;
  provider_response_ids: string[];
  reasoning_effort: string;
  reasoning_tokens: number;
  rejected_candidate_count: number;
  segment_count: number;
  source_extraction_ids: string[];
  started_at: string | null;
  status: RequirementNormalizationStatus;
  updated_at: string;
  warning_count: number;
}
/**
 * Requisito persistido tras validacion deterministica de evidencia.
 */
export interface NormalizedRequirement {
  category: RequirementCategory;
  condition_text: string | null;
  confidence: number;
  created_at: string;
  criticality: RequirementCriticality;
  criticality_basis: RequirementBasis;
  description: string;
  evidence_status: RequirementEvidenceStatus;
  expected_value: ExpectedValue | null;
  id: string;
  is_active: boolean;
  modality: RequirementModality;
  normalization_run_id: string;
  process_id: string;
  requires_human_review: boolean;
  review_status: RequirementReviewStatus;
  scope: RequirementScope;
  stable_key: string;
  subsanability: RequirementSubsanability;
  subsanability_basis: RequirementBasis;
  updated_at: string;
}
export interface PromptVersionSummary {
  content_sha256: string;
  created_at: string;
  id: string;
  is_active: boolean;
  prompt_name: string;
  provider: string;
  semantic_version: string;
}
export interface RejectedRequirementCandidate {
  batch_id: string | null;
  candidate_id: string | null;
  created_at: string;
  id: string;
  raw_candidate: {
    [k: string]: unknown;
  };
  rejection_message: string;
  rejection_reason: RejectedCandidateReason;
  run_id: string;
}
export interface RequirementDetail {
  category: RequirementCategory;
  condition_text: string | null;
  confidence: number;
  created_at: string;
  criticality: RequirementCriticality;
  criticality_basis: RequirementBasis;
  description: string;
  documents: {
    [k: string]: unknown;
  }[];
  evidence: RequirementEvidence[];
  evidence_status: RequirementEvidenceStatus;
  expected_value: ExpectedValue | null;
  id: string;
  is_active: boolean;
  modality: RequirementModality;
  normalization_run_id: string;
  process_id: string;
  prompt_version: PromptVersionSummary;
  relations: RequirementRelation[];
  requires_human_review: boolean;
  review_status: RequirementReviewStatus;
  run: NormalizationRunSummary;
  scope: RequirementScope;
  stable_key: string;
  subsanability: RequirementSubsanability;
  subsanability_basis: RequirementBasis;
  updated_at: string;
}
/**
 * Evidencia validada asociada a un requisito persistido.
 */
export interface RequirementEvidence {
  created_at: string;
  evidence_role: RequirementEvidenceRole;
  extraction_id: string;
  id: string;
  quote_end: number | null;
  quote_start: number | null;
  quoted_text: string;
  requirement_id: string;
  segment_id: string;
  source_location: SourceLocation;
  validation_status: RequirementEvidenceValidationStatus;
}
/**
 * Relacion entre requisitos que requiere revision humana cuando es potencial.
 */
export interface RequirementRelation {
  confidence: number;
  created_at: string;
  explanation: string;
  id: string;
  normalization_run_id: string;
  process_id: string;
  relation_type: RequirementRelationType;
  requires_human_review: boolean;
  source_requirement_id: string;
  target_requirement_id: string;
}
export interface RequirementList {
  items: NormalizedRequirement[];
  limit: number;
  offset: number;
  process_id: string;
  total: number;
}
export interface NormalizationRetryResponse {
  job: NormalizationJobSummary;
  message: string;
  run: NormalizationRunSummary;
}
export interface NormalizationRunDetail {
  accepted_requirement_count: number;
  batch_count: number;
  batches: NormalizationBatchSummary[];
  candidate_count: number;
  consolidation_prompt_version: PromptVersionSummary;
  consolidation_prompt_version_id: string;
  created_at: string;
  documents_used: {
    [k: string]: unknown;
  }[];
  error_code: string | null;
  error_message: string | null;
  finished_at: string | null;
  id: string;
  input_digest: string;
  input_tokens: number;
  job_id: string;
  model: string;
  omitted_documents: {
    [k: string]: unknown;
  }[];
  output_tokens: number;
  process_id: string;
  prompt_version: PromptVersionSummary;
  prompt_version_id: string;
  provider: NormalizationProvider;
  provider_response_ids: string[];
  reasoning_effort: string;
  reasoning_tokens: number;
  rejected_candidate_count: number;
  segment_count: number;
  source_extraction_ids: string[];
  started_at: string | null;
  status: RequirementNormalizationStatus;
  updated_at: string;
  warning_count: number;
  warnings: string[];
}
export interface NormalizationRunList {
  items: NormalizationRunSummary[];
  limit: number;
  offset: number;
  process_id: string;
  total: number;
}
