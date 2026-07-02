// Archivo generado automaticamente desde document-extraction.schema.json
// (pnpm schemas:generate). No editar a mano: la definicion canonica son los
// modelos Pydantic de packages/schemas/src/pliegocheck_schemas/.

export type ExtractedSegmentType = "PAGE_TEXT" | "PARAGRAPH" | "TABLE" | "SHEET_ROW" | "TEXT_LINES";
export type ExtractionErrorCode =
  | "PROCESSING_JOB_NOT_FOUND"
  | "EXTRACTION_NOT_FOUND"
  | "EXTRACTION_ALREADY_QUEUED"
  | "EXTRACTION_ALREADY_COMPLETED"
  | "UNSUPPORTED_FORMAT"
  | "ENCRYPTED_DOCUMENT"
  | "NEEDS_OCR"
  | "SOURCE_FILE_NOT_FOUND"
  | "SOURCE_HASH_MISMATCH"
  | "EXTRACTION_TIMEOUT"
  | "EXTRACTION_LIMIT_EXCEEDED"
  | "EXTRACTION_FAILED"
  | "DATABASE_ERROR";
export type DocumentExtractionStatus =
  | "PENDING"
  | "PROCESSING"
  | "COMPLETED"
  | "COMPLETED_WITH_WARNINGS"
  | "NEEDS_OCR"
  | "UNSUPPORTED"
  | "ENCRYPTED"
  | "FAILED";
export type DocumentProcessingStatus =
  | "NOT_QUEUED"
  | "QUEUED"
  | "PROCESSING"
  | "COMPLETED"
  | "COMPLETED_WITH_WARNINGS"
  | "NEEDS_OCR"
  | "UNSUPPORTED"
  | "ENCRYPTED"
  | "FAILED";
export type DocumentProcessingJobType = "EXTRACT_DOCUMENT";
export type DocumentProcessingJobStatus =
  "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED" | "CANCELLED";

export interface DocumentExtraction {
  extracted_segment: ExtractedSegment;
  extracted_segment_list: ExtractedSegmentList;
  extraction_detail: DocumentExtractionDetail;
  extraction_request: ExtractionRequest;
  extraction_retry_response: ExtractionRetryResponse;
  extraction_summary: DocumentExtractionSummary;
  extraction_warning: ExtractionWarning;
  inventory_item: DocumentInventoryItem;
  process_inventory: ProcessInventory;
  processing_job_summary: ProcessingJobSummary;
}
export interface ExtractedSegment {
  created_at: string;
  extraction_id: string;
  id: string;
  line_end?: number | null;
  line_start?: number | null;
  metadata?: {
    [k: string]: unknown;
  };
  page_number?: number | null;
  paragraph_index?: number | null;
  row_end?: number | null;
  row_start?: number | null;
  segment_type: ExtractedSegmentType;
  sequence: number;
  sheet_name?: string | null;
  source_location: {
    [k: string]: unknown;
  };
  table_index?: number | null;
  text: string;
}
export interface ExtractedSegmentList {
  extraction_id: string;
  limit: number;
  offset: number;
  segments: ExtractedSegment[];
  total: number;
}
export interface DocumentExtractionDetail {
  character_count: number;
  created_at: string;
  detected_format: string;
  document_id: string;
  error_code?: ExtractionErrorCode | null;
  error_message?: string | null;
  extractor_name: string;
  extractor_version: string;
  finished_at?: string | null;
  id: string;
  job_id: string;
  language_hint?: string | null;
  page_count?: number | null;
  segment_count: number;
  segments_preview?: ExtractedSegment[];
  sheet_count?: number | null;
  source_sha256: string;
  started_at?: string | null;
  status: DocumentExtractionStatus;
  updated_at: string;
  warnings?: ExtractionWarning[];
}
export interface ExtractionWarning {
  code: string;
  location?: {
    [k: string]: unknown;
  };
  message: string;
}
export interface ExtractionRequest {
  force?: boolean;
}
export interface ExtractionRetryResponse {
  document_id: string;
  job_id?: string | null;
  message: string;
  processing_status: DocumentProcessingStatus;
}
export interface DocumentExtractionSummary {
  character_count: number;
  created_at: string;
  detected_format: string;
  document_id: string;
  error_code?: ExtractionErrorCode | null;
  error_message?: string | null;
  extractor_name: string;
  extractor_version: string;
  finished_at?: string | null;
  id: string;
  job_id: string;
  language_hint?: string | null;
  page_count?: number | null;
  segment_count: number;
  sheet_count?: number | null;
  source_sha256: string;
  started_at?: string | null;
  status: DocumentExtractionStatus;
  updated_at: string;
  warnings?: ExtractionWarning[];
}
export interface DocumentInventoryItem {
  character_count: number;
  contains_macros?: boolean;
  created_at: string;
  declared_content_type: string | null;
  detected_content_type: string | null;
  detected_format?: string | null;
  document_id: string;
  document_type: string;
  extension: string;
  has_text?: boolean;
  is_encrypted?: boolean;
  latest_extraction?: DocumentExtractionSummary | null;
  needs_ocr?: boolean;
  original_filename: string;
  page_count?: number | null;
  processing_status: DocumentProcessingStatus;
  segment_count: number;
  sha256: string;
  sheet_count?: number | null;
  size_bytes: number;
  upload_status: string;
  warnings?: ExtractionWarning[];
}
export interface ProcessInventory {
  documents: DocumentInventoryItem[];
  process_id: string;
  total: number;
}
export interface ProcessingJobSummary {
  attempt_count: number;
  available_at: string;
  created_at: string;
  document_id: string;
  finished_at: string | null;
  id: string;
  job_type: DocumentProcessingJobType;
  last_error_code: string | null;
  last_error_message: string | null;
  locked_at: string | null;
  locked_by: string | null;
  max_attempts: number;
  priority: number;
  started_at: string | null;
  status: DocumentProcessingJobStatus;
  updated_at: string;
}
