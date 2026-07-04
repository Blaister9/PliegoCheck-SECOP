// Archivo generado automaticamente desde decision-report.schema.json
// (pnpm schemas:generate). No editar a mano: la definicion canonica son los
// modelos Pydantic de packages/schemas/src/pliegocheck_schemas/.

export type DecisionReportArtifactType =
  | "EXECUTIVE_HTML"
  | "EXECUTIVE_MARKDOWN"
  | "REQUIREMENTS_MATRIX_JSON"
  | "REQUIREMENTS_MATRIX_CSV"
  | "EVIDENCE_INDEX_JSON"
  | "ACTIONS_JSON"
  | "DECISION_MANIFEST_JSON"
  | "PACKAGE_MANIFEST_JSON"
  | "PACKAGE_ZIP";
export type DecisionReportJobStatus =
  "PENDING" | "PROCESSING" | "COMPLETED" | "COMPLETED_WITH_WARNINGS" | "FAILED" | "CANCELLED";
export type DecisionReportPackageStatus =
  "DRAFT" | "GENERATING" | "COMPLETED" | "COMPLETED_WITH_WARNINGS" | "FAILED" | "ARCHIVED";

export interface DecisionReport {
  action_export_row: DecisionActionExportRow;
  artifact: DecisionReportArtifactMetadata;
  artifact_manifest: DecisionReportArtifactManifest;
  evidence_index_entry: EvidenceIndexEntry;
  job: DecisionReportJobSummary;
  manifest: DecisionReportManifest;
  package_detail: DecisionReportPackageDetail;
  package_list: DecisionReportPackageList;
  package_summary: DecisionReportPackageSummary;
  preview: DecisionReportPreview;
  queue_response: DecisionReportQueueResponse;
  request: DecisionReportRequest;
  requirement_matrix_row: RequirementMatrixRow;
  retry_request: DecisionReportRetryRequest;
  schema_version?: "1.0.0";
  section: DecisionReportSectionSummary;
}
export interface DecisionActionExportRow {
  action_type: string;
  description_code: string;
  due_at: string | null;
  finding_ids?: string[];
  id: string;
  parameters?: {
    [k: string]: unknown;
  };
  priority: string;
  requirement_ids?: string[];
  status: string;
  title_code: string;
}
export interface DecisionReportArtifactMetadata {
  artifact_type: DecisionReportArtifactType;
  content_type: string;
  created_at: string;
  filename: string;
  id: string;
  package_id: string;
  sha256: string;
  size_bytes: number;
  source_digest: string;
  template_version: string;
}
export interface DecisionReportArtifactManifest {
  artifact_type: DecisionReportArtifactType;
  content_type: string;
  filename: string;
  sha256: string;
  size_bytes: number;
}
export interface EvidenceIndexEntry {
  document_id: string | null;
  document_sha256: string | null;
  evidence_type: string;
  quoted_text: string | null;
  requirement_id: string | null;
  segment_id: string | null;
  source_label: string | null;
  source_location?: {
    [k: string]: unknown;
  };
  validation_status: string | null;
}
export interface DecisionReportJobSummary {
  attempt_count: number;
  created_at: string;
  decision_run_id: string;
  force: boolean;
  id: string;
  last_error_code?: string | null;
  max_attempts: number;
  process_id: string;
  status: DecisionReportJobStatus;
  updated_at: string;
}
export interface DecisionReportManifest {
  artifacts?: DecisionReportArtifactManifest[];
  input_digest: string;
  package_digest: string | null;
  package_id: string;
  package_version: string;
}
export interface DecisionReportPackageDetail {
  artifact_count: number;
  artifacts?: DecisionReportArtifactMetadata[];
  created_at: string;
  created_by: string;
  decision_run_id: string;
  error_code: string | null;
  error_message: string | null;
  id: string;
  input_digest: string;
  input_manifest?: {
    [k: string]: unknown;
  };
  manifest_summary?: {
    [k: string]: unknown;
  };
  package_digest: string | null;
  package_version: string;
  process_id: string;
  published_at: string | null;
  sections?: DecisionReportSectionSummary[];
  status: DecisionReportPackageStatus;
  template_version: string;
  updated_at: string;
  warning_count: number;
}
export interface DecisionReportSectionSummary {
  created_at: string;
  id: string;
  package_id: string;
  section_code: string;
  sequence: number;
  summary_payload?: {
    [k: string]: unknown;
  };
  title: string;
  warning_codes?: string[];
}
export interface DecisionReportPackageList {
  items: DecisionReportPackageSummary[];
  limit: number;
  offset: number;
  total: number;
}
export interface DecisionReportPackageSummary {
  artifact_count: number;
  created_at: string;
  created_by: string;
  decision_run_id: string;
  error_code: string | null;
  error_message: string | null;
  id: string;
  input_digest: string;
  package_digest: string | null;
  package_version: string;
  process_id: string;
  published_at: string | null;
  status: DecisionReportPackageStatus;
  template_version: string;
  updated_at: string;
  warning_count: number;
}
export interface DecisionReportPreview {
  content_type: "text/markdown";
  package_id: string;
  sha256: string;
  text: string;
}
export interface DecisionReportQueueResponse {
  job?: DecisionReportJobSummary | null;
  package: DecisionReportPackageSummary;
  reused_existing_package?: boolean;
}
export interface DecisionReportRequest {
  decision_run_id: string;
  force?: boolean;
}
export interface RequirementMatrixRow {
  action_count: number;
  category: string;
  decision_finding_outcome: string;
  description: string;
  evidence_count: number;
  modality: string;
  requirement_id: string;
  requires_human_review: boolean;
  review_status: string | null;
  scope: string;
  source_domain: string;
  source_result_id: string | null;
  source_run_id: string | null;
  stable_key: string;
  warning_codes?: string[];
}
export interface DecisionReportRetryRequest {
  force?: boolean;
}
