// Archivo generado automaticamente desde external-procurement.schema.json
// (pnpm schemas:generate). No editar a mano: la definicion canonica son los
// modelos Pydantic de packages/schemas/src/pliegocheck_schemas/.

export type ExternalProcurementImportStatus =
  "PENDING" | "IMPORTED" | "SKIPPED_DUPLICATE" | "FAILED";
export type ExternalProcurementDocumentStatus =
  | "DOCUMENTS_NOT_AVAILABLE"
  | "DOCUMENT_LINKS_AVAILABLE"
  | "DOCUMENT_DOWNLOAD_UNSUPPORTED"
  | "DOCUMENT_DOWNLOAD_FAILED"
  | "DOCUMENTS_IMPORTED";
export type ExternalProcurementFieldStatus =
  "PRESENT" | "MISSING" | "NORMALIZED" | "UNMAPPED" | "CONFLICTING";
export type ExternalProcurementSourceSystem = "SECOP_II" | "SECOP_I";
export type ExternalProcurementErrorCode =
  | "SOURCE_DISABLED"
  | "SOURCE_NOT_FOUND"
  | "SOURCE_UNAVAILABLE"
  | "SOURCE_TIMEOUT"
  | "SOURCE_INVALID_RESPONSE"
  | "RATE_LIMITED"
  | "UNSUPPORTED_FILTER"
  | "SEARCH_NOT_FOUND"
  | "RESULT_NOT_FOUND"
  | "IMPORT_NOT_FOUND"
  | "INVALID_EXTERNAL_PROCESS"
  | "EXTERNAL_DATABASE_ERROR";
export type ExternalProcurementSearchStatus =
  "PENDING" | "RUNNING" | "COMPLETED" | "COMPLETED_WITH_WARNINGS" | "FAILED";
export type ExternalProcurementProvider = "datos_abiertos";
export type ExternalProcurementSourceStatus =
  "AVAILABLE" | "PARTIAL" | "STALE" | "ERROR" | "UNSUPPORTED";

export interface ExternalProcurement {
  import_list: ExternalProcurementImportList;
  import_request: ExternalProcurementImportRequest;
  import_response: ExternalProcurementImportResponse;
  normalized_process: SecopProcessNormalized;
  process_link_list: ExternalProcurementProcessLinkList;
  result_list: ExternalProcurementResultList;
  search_list: ExternalProcurementSearchList;
  search_request: ExternalProcurementSearchRequest;
  search_response: ExternalProcurementSearchResponse;
  source: ExternalProcurementSourceSummary;
}
export interface ExternalProcurementImportList {
  items: ExternalProcurementImportResponse[];
  limit: number;
  offset: number;
  total: number;
}
export interface ExternalProcurementImportResponse {
  created_at: string;
  deduplication_key: string;
  id: string;
  imported_at: string | null;
  message: string;
  process_id: string;
  source_result_id: string;
  status: ExternalProcurementImportStatus;
}
export interface ExternalProcurementImportRequest {
  expected_source_process_id?: string | null;
}
export interface SecopProcessNormalized {
  closing_date?: string | null;
  currency?: string | null;
  department?: string | null;
  description?: string | null;
  documents_status: ExternalProcurementDocumentStatus;
  documents_url?: string | null;
  entity_name: string;
  entity_nit?: string | null;
  estimated_value?: number | string | null;
  field_statuses?: {
    [k: string]: ExternalProcurementFieldStatus;
  };
  modality?: string | null;
  municipality?: string | null;
  publication_date?: string | null;
  raw_payload_hash: string;
  reference?: string | null;
  source_dataset: string;
  source_process_id: string;
  source_system: ExternalProcurementSourceSystem;
  source_url?: string | null;
  status?: string | null;
  title: string;
  warnings?: ExternalProcurementWarning[];
}
export interface ExternalProcurementWarning {
  code: string;
  field?: string | null;
  message: string;
}
export interface ExternalProcurementProcessLinkList {
  items: ExternalProcurementProcessLink[];
  process_id: string;
  total: number;
}
export interface ExternalProcurementProcessLink {
  created_at: string;
  documents_status: ExternalProcurementDocumentStatus;
  documents_url: string | null;
  external_metadata?: {
    [k: string]: unknown;
  };
  id: string;
  imported_at: string;
  process_id: string;
  source_dataset: string;
  source_process_id: string;
  source_process_reference: string | null;
  source_system: ExternalProcurementSourceSystem;
  source_url: string | null;
}
export interface ExternalProcurementResultList {
  items: ExternalProcurementSearchResult[];
  limit: number;
  offset: number;
  search_id: string;
  total: number;
}
export interface ExternalProcurementSearchResult {
  closing_date: string | null;
  created_at: string;
  currency: string | null;
  department: string | null;
  documents_status: ExternalProcurementDocumentStatus;
  entity_name: string;
  estimated_value: string | null;
  field_statuses?: {
    [k: string]: ExternalProcurementFieldStatus;
  };
  id: string;
  import_status: ExternalProcurementImportStatus;
  modality: string | null;
  municipality: string | null;
  process_id?: string | null;
  publication_date: string | null;
  raw_payload_hash: string;
  search_id: string;
  source_dataset: string;
  source_id: string;
  source_process_id: string;
  source_process_reference: string | null;
  source_system: ExternalProcurementSourceSystem;
  source_url: string | null;
  status: string | null;
  title: string;
  warnings?: ExternalProcurementWarning[];
}
export interface ExternalProcurementSearchList {
  items: ExternalProcurementSearchSummary[];
  limit: number;
  offset: number;
  total: number;
}
export interface ExternalProcurementSearchSummary {
  created_at: string;
  error_code: ExternalProcurementErrorCode | null;
  error_message: string | null;
  filters: {
    [k: string]: unknown;
  };
  finished_at: string | null;
  id: string;
  limit: number;
  offset: number;
  page_count: number;
  query: string | null;
  result_count: number;
  source_id: string;
  source_row_count: number;
  source_system: ExternalProcurementSourceSystem;
  started_at: string | null;
  status: ExternalProcurementSearchStatus;
  unsupported_filters?: string[];
  warnings?: ExternalProcurementWarning[];
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
export interface ExternalProcurementSearchResponse {
  items: ExternalProcurementSearchResult[];
  search: ExternalProcurementSearchSummary;
}
export interface ExternalProcurementSourceSummary {
  api_url: string;
  base_url: string;
  created_at: string;
  dataset_id: string;
  enabled: boolean;
  human_url: string;
  id: string;
  last_checked_at?: string | null;
  metadata?: {
    [k: string]: unknown;
  };
  name: string;
  provider: ExternalProcurementProvider;
  source_system: ExternalProcurementSourceSystem;
  status: ExternalProcurementSourceStatus;
  updated_at: string;
}
