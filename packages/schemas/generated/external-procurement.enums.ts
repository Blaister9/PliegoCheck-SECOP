// Archivo generado automaticamente por packages/schemas/scripts/generate.py.
// No editar a mano: la definicion canonica son los modelos Pydantic de
// packages/schemas/src/pliegocheck_schemas/.

export const EXTERNAL_PROCUREMENT_SCHEMA_VERSION = "1.0.0";

export const EXTERNAL_PROCUREMENT_SOURCE_STATUS_VALUES = [
  "AVAILABLE",
  "PARTIAL",
  "STALE",
  "ERROR",
  "UNSUPPORTED",
] as const;
export type ExternalProcurementSourceStatusValue =
  (typeof EXTERNAL_PROCUREMENT_SOURCE_STATUS_VALUES)[number];

export const EXTERNAL_PROCUREMENT_SEARCH_STATUS_VALUES = [
  "PENDING",
  "RUNNING",
  "COMPLETED",
  "COMPLETED_WITH_WARNINGS",
  "FAILED",
] as const;
export type ExternalProcurementSearchStatusValue =
  (typeof EXTERNAL_PROCUREMENT_SEARCH_STATUS_VALUES)[number];

export const EXTERNAL_PROCUREMENT_IMPORT_STATUS_VALUES = [
  "PENDING",
  "IMPORTED",
  "SKIPPED_DUPLICATE",
  "FAILED",
] as const;
export type ExternalProcurementImportStatusValue =
  (typeof EXTERNAL_PROCUREMENT_IMPORT_STATUS_VALUES)[number];

export const EXTERNAL_PROCUREMENT_PROVIDER_VALUES = ["datos_abiertos"] as const;
export type ExternalProcurementProviderValue =
  (typeof EXTERNAL_PROCUREMENT_PROVIDER_VALUES)[number];

export const EXTERNAL_PROCUREMENT_SOURCE_SYSTEM_VALUES = ["SECOP_II", "SECOP_I"] as const;
export type ExternalProcurementSourceSystemValue =
  (typeof EXTERNAL_PROCUREMENT_SOURCE_SYSTEM_VALUES)[number];

export const EXTERNAL_PROCUREMENT_FIELD_STATUS_VALUES = [
  "PRESENT",
  "MISSING",
  "NORMALIZED",
  "UNMAPPED",
  "CONFLICTING",
] as const;
export type ExternalProcurementFieldStatusValue =
  (typeof EXTERNAL_PROCUREMENT_FIELD_STATUS_VALUES)[number];

export const EXTERNAL_PROCUREMENT_DOCUMENT_STATUS_VALUES = [
  "DOCUMENTS_NOT_AVAILABLE",
  "DOCUMENT_LINKS_AVAILABLE",
  "DOCUMENT_DOWNLOAD_UNSUPPORTED",
  "DOCUMENT_DOWNLOAD_FAILED",
  "DOCUMENTS_IMPORTED",
] as const;
export type ExternalProcurementDocumentStatusValue =
  (typeof EXTERNAL_PROCUREMENT_DOCUMENT_STATUS_VALUES)[number];

export const EXTERNAL_PROCUREMENT_ERROR_CODE_VALUES = [
  "SOURCE_DISABLED",
  "SOURCE_NOT_FOUND",
  "SOURCE_UNAVAILABLE",
  "SOURCE_TIMEOUT",
  "SOURCE_INVALID_RESPONSE",
  "RATE_LIMITED",
  "UNSUPPORTED_FILTER",
  "SEARCH_NOT_FOUND",
  "RESULT_NOT_FOUND",
  "IMPORT_NOT_FOUND",
  "INVALID_EXTERNAL_PROCESS",
  "EXTERNAL_DATABASE_ERROR",
] as const;
export type ExternalProcurementErrorCodeValue =
  (typeof EXTERNAL_PROCUREMENT_ERROR_CODE_VALUES)[number];
