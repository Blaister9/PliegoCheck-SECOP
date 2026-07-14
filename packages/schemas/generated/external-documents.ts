// Archivo generado automaticamente desde external-documents.schema.json
// (pnpm schemas:generate). No editar a mano: la definicion canonica son los
// modelos Pydantic de packages/schemas/src/pliegocheck_schemas/.

export type ExternalProcessChangeEventType =
  | "PROCESS_STATUS_CHANGED"
  | "CLOSING_DATE_CHANGED"
  | "ESTIMATED_VALUE_CHANGED"
  | "DOCUMENT_DISCOVERED"
  | "DOCUMENT_UPDATED"
  | "DOCUMENT_REMOVED_FROM_SOURCE"
  | "POTENTIAL_ADDENDUM_DISCOVERED"
  | "CONFIRMED_ADDENDUM_DISCOVERED"
  | "DOWNLOAD_FAILED";
export type ExternalDocumentAddendumStatus =
  "CONFIRMED_ADDENDUM" | "POTENTIAL_ADDENDUM" | "NOT_ADDENDUM" | "UNKNOWN";
export type ExternalDocumentDiscoveryStatus =
  "DISCOVERED" | "LINK_AVAILABLE" | "METADATA_ONLY" | "UNSUPPORTED" | "MISSING" | "ERROR";
export type ExternalDocumentDownloadStatus =
  | "NOT_REQUESTED"
  | "PENDING"
  | "DOWNLOADING"
  | "DOWNLOADED"
  | "UNCHANGED"
  | "UPDATED"
  | "UNSUPPORTED"
  | "FAILED"
  | "REJECTED";
export type ExternalDocumentErrorCode =
  | "EXTERNAL_SYNC_NOT_AVAILABLE"
  | "EXTERNAL_SYNC_ALREADY_QUEUED"
  | "EXTERNAL_SYNC_NOT_FOUND"
  | "EXTERNAL_SOURCE_UNAVAILABLE"
  | "EXTERNAL_PROCESS_LINK_NOT_FOUND"
  | "EXTERNAL_DOCUMENT_NOT_FOUND"
  | "EXTERNAL_DOCUMENT_DOWNLOAD_UNSUPPORTED"
  | "EXTERNAL_DOCUMENT_URL_REJECTED"
  | "EXTERNAL_DOCUMENT_HOST_REJECTED"
  | "EXTERNAL_DOCUMENT_TOO_LARGE"
  | "EXTERNAL_DOCUMENT_CONTENT_TYPE_REJECTED"
  | "EXTERNAL_DOCUMENT_HTML_RESPONSE"
  | "EXTERNAL_DOCUMENT_DOWNLOAD_FAILED"
  | "EXTERNAL_DOCUMENT_HASH_MISMATCH"
  | "EXTERNAL_DOCUMENT_ALREADY_DOWNLOADED"
  | "EXTERNAL_DOCUMENT_VERSION_CONFLICT"
  | "EXTERNAL_DOCUMENT_EXTRACTION_NOT_READY";
export type ExternalProcessSyncStatus =
  "PENDING" | "PROCESSING" | "COMPLETED" | "COMPLETED_WITH_WARNINGS" | "FAILED" | "CANCELLED";

export interface ExternalDocuments {
  change_event: ExternalProcessChangeEvent;
  document_detail: ExternalProcessDocumentDetail;
  document_list: ExternalProcessDocumentList;
  document_summary: ExternalProcessDocumentSummary;
  document_version: ExternalProcessDocumentVersion;
  download_request: ExternalDocumentDownloadRequest;
  download_response: ExternalDocumentDownloadResponse;
  extract_response: ExternalDocumentExtractResponse;
  sync_detail: ExternalProcessSyncRunDetail;
  sync_list: ExternalProcessSyncRunList;
  sync_queue_response: ExternalProcessSyncQueueResponse;
  sync_readiness: ExternalProcessSyncReadiness;
  sync_request: ExternalProcessSyncRequest;
  sync_summary: ExternalProcessSyncRunSummary;
}
export interface ExternalProcessChangeEvent {
  created_at: string;
  event_type: ExternalProcessChangeEventType;
  external_document_id: string | null;
  id: string;
  metadata?: {
    [k: string]: unknown;
  };
  new_value: string | null;
  old_value: string | null;
  process_id: string;
  sync_run_id: string;
}
export interface ExternalProcessDocumentDetail {
  addendum_status: ExternalDocumentAddendumStatus;
  current_version_id: string | null;
  discovery_status: ExternalDocumentDiscoveryStatus;
  document_category: string | null;
  document_type: string | null;
  download_status: ExternalDocumentDownloadStatus;
  first_seen_at: string;
  id: string;
  last_seen_at: string;
  process_id: string;
  published_at: string | null;
  reported_content_type: string | null;
  reported_size_bytes?: number | null;
  requires_human_review: boolean;
  source_document_id: string;
  source_document_reference: string | null;
  source_public_url: string | null;
  source_system: string;
  source_url: string | null;
  title: string;
  updated_at_source: string | null;
  version_count: number;
  versions?: ExternalProcessDocumentVersion[];
}
export interface ExternalProcessDocumentVersion {
  created_at: string;
  detected_content_type: string;
  downloaded_at: string;
  external_document_id: string;
  id: string;
  previous_version_id: string | null;
  process_document_id: string;
  reported_content_type: string | null;
  reported_size_bytes?: number | null;
  sha256: string;
  size_bytes: number;
  source_updated_at: string | null;
  source_url: string | null;
  version_number: number;
}
export interface ExternalProcessDocumentList {
  items: ExternalProcessDocumentSummary[];
  process_id: string;
  total: number;
}
export interface ExternalProcessDocumentSummary {
  addendum_status: ExternalDocumentAddendumStatus;
  current_version_id: string | null;
  discovery_status: ExternalDocumentDiscoveryStatus;
  document_category: string | null;
  document_type: string | null;
  download_status: ExternalDocumentDownloadStatus;
  first_seen_at: string;
  id: string;
  last_seen_at: string;
  process_id: string;
  published_at: string | null;
  reported_content_type: string | null;
  reported_size_bytes?: number | null;
  requires_human_review: boolean;
  source_document_id: string;
  source_document_reference: string | null;
  source_public_url: string | null;
  source_system: string;
  source_url: string | null;
  title: string;
  updated_at_source: string | null;
  version_count: number;
}
export interface ExternalDocumentDownloadRequest {
  confirm_public_download: boolean;
}
export interface ExternalDocumentDownloadResponse {
  external_document_id: string;
  message: string;
  process_document_id: string | null;
  process_id: string;
  sha256: string | null;
  status: ExternalDocumentDownloadStatus;
  version_id: string | null;
}
export interface ExternalDocumentExtractResponse {
  external_document_id: string;
  extraction_job_id: string | null;
  message: string;
  process_document_id: string;
  process_id: string;
}
export interface ExternalProcessSyncRunDetail {
  created_at: string;
  documents_added: number;
  documents_discovered: number;
  documents_failed: number;
  documents_unchanged: number;
  documents_updated: number;
  error_code: ExternalDocumentErrorCode | null;
  error_message: string | null;
  events?: ExternalProcessChangeEvent[];
  external_process_link_id: string;
  finished_at: string | null;
  id: string;
  input_digest: string;
  metadata_changed: boolean;
  process_id: string;
  source_system: string;
  source_updated_at: string | null;
  started_at: string | null;
  status: ExternalProcessSyncStatus;
  warnings?: {
    [k: string]: unknown;
  }[];
}
export interface ExternalProcessSyncRunList {
  items: ExternalProcessSyncRunSummary[];
  process_id: string;
  total: number;
}
export interface ExternalProcessSyncRunSummary {
  created_at: string;
  documents_added: number;
  documents_discovered: number;
  documents_failed: number;
  documents_unchanged: number;
  documents_updated: number;
  error_code: ExternalDocumentErrorCode | null;
  error_message: string | null;
  external_process_link_id: string;
  finished_at: string | null;
  id: string;
  metadata_changed: boolean;
  process_id: string;
  source_system: string;
  source_updated_at: string | null;
  started_at: string | null;
  status: ExternalProcessSyncStatus;
  warnings?: {
    [k: string]: unknown;
  }[];
}
export interface ExternalProcessSyncQueueResponse {
  message: string;
  process_id: string;
  status: ExternalProcessSyncStatus;
  sync_run_id: string;
}
export interface ExternalProcessSyncReadiness {
  active_sync_run_id: string | null;
  available: boolean;
  enabled: boolean;
  external_process_link_id: string | null;
  last_sync_at: string | null;
  process_id: string;
  reason: string | null;
  source_system: string | null;
}
export interface ExternalProcessSyncRequest {
  discover_documents?: boolean;
}
