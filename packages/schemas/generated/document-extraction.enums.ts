// Archivo generado automaticamente por packages/schemas/scripts/generate.py.
// No editar a mano: la definicion canonica son los modelos Pydantic de
// packages/schemas/src/pliegocheck_schemas/.

export const DOCUMENT_EXTRACTION_SCHEMA_VERSION = "1.0.0";

export const DOCUMENT_PROCESSING_STATUS_VALUES = [
  "NOT_QUEUED",
  "QUEUED",
  "PROCESSING",
  "COMPLETED",
  "COMPLETED_WITH_WARNINGS",
  "NEEDS_OCR",
  "UNSUPPORTED",
  "ENCRYPTED",
  "FAILED",
] as const;
export type DocumentProcessingStatusValue = (typeof DOCUMENT_PROCESSING_STATUS_VALUES)[number];

export const DOCUMENT_PROCESSING_JOB_STATUS_VALUES = [
  "PENDING",
  "PROCESSING",
  "COMPLETED",
  "FAILED",
  "CANCELLED",
] as const;
export type DocumentProcessingJobStatusValue =
  (typeof DOCUMENT_PROCESSING_JOB_STATUS_VALUES)[number];

export const DOCUMENT_PROCESSING_JOB_TYPE_VALUES = ["EXTRACT_DOCUMENT"] as const;
export type DocumentProcessingJobTypeValue = (typeof DOCUMENT_PROCESSING_JOB_TYPE_VALUES)[number];

export const DOCUMENT_EXTRACTION_STATUS_VALUES = [
  "PENDING",
  "PROCESSING",
  "COMPLETED",
  "COMPLETED_WITH_WARNINGS",
  "NEEDS_OCR",
  "UNSUPPORTED",
  "ENCRYPTED",
  "FAILED",
] as const;
export type DocumentExtractionStatusValue = (typeof DOCUMENT_EXTRACTION_STATUS_VALUES)[number];

export const EXTRACTED_SEGMENT_TYPE_VALUES = [
  "PAGE_TEXT",
  "PARAGRAPH",
  "TABLE",
  "SHEET_ROW",
  "TEXT_LINES",
] as const;
export type ExtractedSegmentTypeValue = (typeof EXTRACTED_SEGMENT_TYPE_VALUES)[number];

export const EXTRACTION_ERROR_CODE_VALUES = [
  "PROCESSING_JOB_NOT_FOUND",
  "EXTRACTION_NOT_FOUND",
  "EXTRACTION_ALREADY_QUEUED",
  "EXTRACTION_ALREADY_COMPLETED",
  "UNSUPPORTED_FORMAT",
  "ENCRYPTED_DOCUMENT",
  "NEEDS_OCR",
  "SOURCE_FILE_NOT_FOUND",
  "SOURCE_HASH_MISMATCH",
  "EXTRACTION_TIMEOUT",
  "EXTRACTION_LIMIT_EXCEEDED",
  "EXTRACTION_FAILED",
  "DATABASE_ERROR",
] as const;
export type ExtractionErrorCodeValue = (typeof EXTRACTION_ERROR_CODE_VALUES)[number];
