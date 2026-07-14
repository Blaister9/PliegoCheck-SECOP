// Archivo generado automaticamente desde opportunities.schema.json
// (pnpm schemas:generate). No editar a mano: la definicion canonica son los
// modelos Pydantic de packages/schemas/src/pliegocheck_schemas/.

export type OpportunityComponent =
  | "RELEVANCE"
  | "UNSPSC_MATCH"
  | "EXPERIENCE_MATCH"
  | "FINANCIAL_FIT"
  | "TECHNICAL_FIT"
  | "LEGAL_READINESS"
  | "GEOGRAPHIC_FIT"
  | "VALUE_FIT"
  | "DEADLINE_URGENCY"
  | "DOCUMENT_READINESS"
  | "INFORMATION_COMPLETENESS"
  | "PARTNER_NEED";
export type OpportunityComponentStatus =
  | "STRONG_MATCH"
  | "MATCH"
  | "PARTIAL_MATCH"
  | "MISMATCH"
  | "UNKNOWN"
  | "NOT_APPLICABLE"
  | "CONFLICTING";
export type OpportunityAnalysisLevel =
  "METADATA_SCREENING" | "DOCUMENT_SCREENING" | "DEEP_ANALYSIS";
export type ExternalProcurementSourceSystem = "SECOP_II" | "SECOP_I";
export type OpportunityReviewAction =
  "ACKNOWLEDGE" | "SHORTLIST" | "DISMISS" | "SEEK_PARTNER" | "REQUEST_DEEP_ANALYSIS";
export type OpportunityOutcome =
  | "REVISAR_PRIMERO"
  | "OPORTUNIDAD_POTENCIAL"
  | "REQUIERE_ALIADO"
  | "INFORMACION_INSUFICIENTE"
  | "POCO_COMPATIBLE"
  | "DESCARTAR";
export type OpportunityUrgencyStatus =
  "CLOSED" | "EXPIRED" | "CRITICAL" | "URGENT" | "NORMAL" | "LONG_HORIZON" | "UNKNOWN";
export type OpportunityDiscoveryStatus =
  "PENDING" | "PROCESSING" | "COMPLETED" | "COMPLETED_WITH_WARNINGS" | "FAILED" | "CANCELLED";

export interface Opportunities {
  assessment_component: OpportunityAssessmentComponentDetail;
  assessment_detail: OpportunityAssessmentDetail;
  assessment_evidence: OpportunityAssessmentEvidence;
  assessment_summary: OpportunityAssessmentSummary;
  candidate_summary: OpportunityCandidateSummary;
  deep_analysis: OpportunityDeepAnalysisResponse;
  discovery_request: OpportunityDiscoveryRequest;
  discovery_response: OpportunityDiscoveryResponse;
  discovery_run_detail: OpportunityDiscoveryRunDetail;
  discovery_run_summary: OpportunityDiscoveryRunSummary;
  inbox_filters: OpportunityInboxFilters;
  inbox_response: OpportunityInboxResponse;
  readiness: OpportunityReadiness;
  review_request: OpportunityReviewRequest;
  review_response: OpportunityReviewResponse;
}
export interface OpportunityAssessmentComponentDetail {
  component: OpportunityComponent;
  evidence?: OpportunityAssessmentEvidence[];
  evidence_refs?: string[];
  explanation: string;
  explanation_parameters?: {
    [k: string]: unknown;
  };
  id?: string | null;
  reason_code: string;
  score: number | string;
  status: OpportunityComponentStatus;
  warnings?: string[];
  weight: number | string;
  weighted_score: number | string;
}
export interface OpportunityAssessmentEvidence {
  entity_id?: string | null;
  entity_type: string;
  evidence_type: string;
  excerpt?: string | null;
  id?: string | null;
  metadata?: {
    [k: string]: unknown;
  };
  source_reference?: string | null;
}
export interface OpportunityAssessmentDetail {
  analysis_level: OpportunityAnalysisLevel;
  candidate: OpportunityCandidateSummary;
  candidate_id: string;
  company_snapshot_id: string;
  compatibility_score: number | string;
  components: OpportunityAssessmentComponentDetail[];
  created_at: string;
  days_remaining?: number | string | null;
  effective_at: string;
  id: string;
  information_completeness: number | string;
  input_digest: string;
  latest_review_action?: OpportunityReviewAction | null;
  missing_information?: {
    [k: string]: string[];
  };
  outcome: OpportunityOutcome;
  partner_reasons?: {
    [k: string]: unknown;
  }[];
  policy_hash: string;
  policy_version: string;
  requires_human_review: boolean;
  summary: string;
  urgency_score: number | string;
  urgency_status: OpportunityUrgencyStatus;
  warnings?: string[];
}
export interface OpportunityCandidateSummary {
  closing_date?: string | null;
  created_at: string;
  currency?: string | null;
  department?: string | null;
  discovery_run_id: string;
  document_status: string;
  entity_name: string;
  estimated_value?: number | string | null;
  external_search_result_id: string;
  id: string;
  modality?: string | null;
  municipality?: string | null;
  process_id?: string | null;
  publication_date?: string | null;
  source_process_id: string;
  source_reference?: string | null;
  source_status?: string | null;
  source_system: ExternalProcurementSourceSystem;
  title: string;
}
export interface OpportunityAssessmentSummary {
  analysis_level: OpportunityAnalysisLevel;
  candidate_id: string;
  company_snapshot_id: string;
  compatibility_score: number | string;
  created_at: string;
  days_remaining?: number | string | null;
  effective_at: string;
  id: string;
  information_completeness: number | string;
  input_digest: string;
  missing_information?: {
    [k: string]: string[];
  };
  outcome: OpportunityOutcome;
  partner_reasons?: {
    [k: string]: unknown;
  }[];
  policy_hash: string;
  policy_version: string;
  requires_human_review: boolean;
  summary: string;
  urgency_score: number | string;
  urgency_status: OpportunityUrgencyStatus;
  warnings?: string[];
}
export interface OpportunityDeepAnalysisResponse {
  missing_inputs?: string[];
  opportunity_id: string;
  process_id?: string | null;
  steps_blocked?: string[];
  steps_queued?: string[];
  steps_ready?: string[];
}
export interface OpportunityDiscoveryRequest {
  /**
   * @maxItems 100
   */
  candidate_ids?: string[];
  company_profile_id: string;
  company_snapshot_id: string;
  effective_at?: string | null;
  force?: boolean;
  /**
   * @maxItems 2
   */
  search_requests?:
    | []
    | [ExternalProcurementSearchRequest]
    | [ExternalProcurementSearchRequest, ExternalProcurementSearchRequest];
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
export interface OpportunityDiscoveryResponse {
  reused?: boolean;
  run: OpportunityDiscoveryRunSummary;
}
export interface OpportunityDiscoveryRunSummary {
  assessed_count: number;
  candidate_count: number;
  company_profile_id: string;
  company_snapshot_id: string;
  created_at: string;
  effective_at: string;
  finished_at?: string | null;
  id: string;
  input_digest: string;
  policy_hash: string;
  policy_version: string;
  started_at?: string | null;
  status: OpportunityDiscoveryStatus;
  warning_count: number;
}
export interface OpportunityDiscoveryRunDetail {
  assessed_count: number;
  candidate_count: number;
  candidates?: OpportunityAssessmentDetail[];
  company_profile_id: string;
  company_snapshot_id: string;
  created_at: string;
  effective_at: string;
  finished_at?: string | null;
  id: string;
  input_digest: string;
  policy_hash: string;
  policy_version: string;
  started_at?: string | null;
  status: OpportunityDiscoveryStatus;
  warning_count: number;
  warnings?: string[];
}
export interface OpportunityInboxFilters {
  analysis_level?: OpportunityAnalysisLevel | null;
  closing_from?: string | null;
  closing_to?: string | null;
  company_snapshot_id?: string | null;
  department?: string | null;
  document_status?: string | null;
  entity?: string | null;
  limit?: number;
  max_value?: number | string | null;
  min_value?: number | string | null;
  modality?: string | null;
  municipality?: string | null;
  offset?: number;
  outcome?: OpportunityOutcome | null;
  review_action?: OpportunityReviewAction | null;
  sort?: string;
  source_system?: ExternalProcurementSourceSystem | null;
  urgency?: OpportunityUrgencyStatus | null;
}
export interface OpportunityInboxResponse {
  disclaimer: string;
  items: OpportunityAssessmentDetail[];
  limit: number;
  offset: number;
  total: number;
}
export interface OpportunityReadiness {
  companies_count: number;
  policy_hash: string;
  policy_version: string;
  published_snapshots_count: number;
  ready: boolean;
  reasons?: string[];
}
export interface OpportunityReviewRequest {
  action: OpportunityReviewAction;
  reason?: string | null;
}
export interface OpportunityReviewResponse {
  action: OpportunityReviewAction;
  assessment_id: string;
  created_at: string;
  previous_action?: OpportunityReviewAction | null;
}
