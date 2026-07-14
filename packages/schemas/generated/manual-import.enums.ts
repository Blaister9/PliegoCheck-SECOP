// Archivo generado automaticamente por packages/schemas/scripts/generate.py.
// No editar a mano: la definicion canonica son los modelos Pydantic de
// packages/schemas/src/pliegocheck_schemas/.

export const MANUAL_IMPORT_SCHEMA_VERSION = "1.0.0";

export const PROCESS_SOURCE_VALUES = ["MANUAL", "SECOP_IMPORT"] as const;
export type ProcessSourceValue = (typeof PROCESS_SOURCE_VALUES)[number];

export const PROCESS_STATUS_VALUES = ["DRAFT", "DOCUMENTS_PENDING", "READY_FOR_INVENTORY"] as const;
export type ProcessStatusValue = (typeof PROCESS_STATUS_VALUES)[number];

export const DOCUMENT_TYPE_VALUES = [
  "UNKNOWN",
  "TERMS",
  "TECHNICAL_ANNEX",
  "FINANCIAL_ANNEX",
  "EXPERIENCE_ANNEX",
  "RISK_MATRIX",
  "SCHEDULE",
  "FORM",
  "ADDENDUM",
  "SUPPORTING_DOCUMENT",
] as const;
export type DocumentTypeValue = (typeof DOCUMENT_TYPE_VALUES)[number];

export const DOCUMENT_UPLOAD_STATUS_VALUES = ["STORED", "REJECTED"] as const;
export type DocumentUploadStatusValue = (typeof DOCUMENT_UPLOAD_STATUS_VALUES)[number];

export const UPLOAD_ERROR_CODE_VALUES = [
  "PROCESS_NOT_FOUND",
  "DOCUMENT_NOT_FOUND",
  "INVALID_PROCESS_DATA",
  "FILE_EMPTY",
  "FILE_TOO_LARGE",
  "FILE_TYPE_NOT_ALLOWED",
  "FILE_CONTENT_MISMATCH",
  "DUPLICATE_DOCUMENT",
  "STORAGE_ERROR",
  "DATABASE_ERROR",
] as const;
export type UploadErrorCodeValue = (typeof UPLOAD_ERROR_CODE_VALUES)[number];
