// Archivo generado automaticamente desde manual-import.schema.json
// (pnpm schemas:generate). No editar a mano: la definicion canonica son los
// modelos Pydantic de packages/schemas/src/pliegocheck_schemas/.

/**
 * Codigos de error de dominio de la importacion manual.
 */
export type UploadErrorCode =
  | "PROCESS_NOT_FOUND"
  | "DOCUMENT_NOT_FOUND"
  | "INVALID_PROCESS_DATA"
  | "FILE_EMPTY"
  | "FILE_TOO_LARGE"
  | "FILE_TYPE_NOT_ALLOWED"
  | "FILE_CONTENT_MISMATCH"
  | "DUPLICATE_DOCUMENT"
  | "STORAGE_ERROR"
  | "DATABASE_ERROR";
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
export type NormalizationErrorCode =
  | "NORMALIZATION_DISABLED"
  | "OPENAI_API_KEY_MISSING"
  | "PROCESS_NOT_FOUND"
  | "NORMALIZATION_RUN_NOT_FOUND"
  | "REQUIREMENT_NOT_FOUND"
  | "NO_ELIGIBLE_EXTRACTIONS"
  | "NO_ELIGIBLE_SEGMENTS"
  | "NORMALIZATION_ALREADY_ACTIVE"
  | "NORMALIZATION_NOT_RETRYABLE"
  | "NORMALIZATION_JOB_NOT_FOUND"
  | "PROMPT_VERSION_NOT_FOUND"
  | "PROMPT_INVALID"
  | "PROVIDER_CONFIGURATION_ERROR"
  | "PROVIDER_TRANSIENT_ERROR"
  | "PROVIDER_RESPONSE_INVALID"
  | "PROVIDER_REFUSAL"
  | "PROVIDER_INCOMPLETE"
  | "EVIDENCE_VALIDATION_FAILED"
  | "DATABASE_ERROR";
export type CompanyErrorCode =
  | "COMPANY_NOT_FOUND"
  | "COMPANY_ARCHIVED"
  | "DUPLICATE_TAX_ID"
  | "INVALID_COMPANY_DATA"
  | "LEGAL_REGISTRATION_NOT_FOUND"
  | "RUP_SNAPSHOT_NOT_FOUND"
  | "FINANCIAL_PERIOD_NOT_FOUND"
  | "FINANCIAL_METRIC_NOT_FOUND"
  | "EXPERIENCE_RECORD_NOT_FOUND"
  | "PERSON_NOT_FOUND"
  | "CERTIFICATION_NOT_FOUND"
  | "CAPABILITY_NOT_FOUND"
  | "EVIDENCE_DOCUMENT_NOT_FOUND"
  | "EVIDENCE_LINK_NOT_FOUND"
  | "EVIDENCE_SUBJECT_NOT_FOUND"
  | "EVIDENCE_SUBJECT_COMPANY_MISMATCH"
  | "EVIDENCE_DOCUMENT_COMPANY_MISMATCH"
  | "EVIDENCE_QUOTE_NOT_FOUND"
  | "EVIDENCE_EXPIRED"
  | "PROFILE_INCOMPLETE"
  | "SNAPSHOT_NOT_FOUND"
  | "SNAPSHOT_ALREADY_PUBLISHED"
  | "SNAPSHOT_IMMUTABLE"
  | "SNAPSHOT_DIGEST_MISMATCH"
  | "DATABASE_ERROR";
export type FinancialErrorCode =
  | "FINANCIAL_EVALUATION_ALREADY_QUEUED"
  | "FINANCIAL_EVALUATION_ALREADY_COMPLETED"
  | "FINANCIAL_EVALUATION_NOT_FOUND"
  | "FINANCIAL_EVALUATION_INPUT_NOT_READY"
  | "FINANCIAL_REQUIREMENTS_NOT_FOUND"
  | "COMPANY_SNAPSHOT_NOT_FOUND"
  | "COMPANY_SNAPSHOT_NOT_PUBLISHED"
  | "FINANCIAL_RULE_AMBIGUOUS"
  | "FINANCIAL_RULE_UNSUPPORTED"
  | "FINANCIAL_METRIC_MISSING"
  | "FINANCIAL_PERIOD_NOT_RESOLVED"
  | "FINANCIAL_UNIT_MISMATCH"
  | "FINANCIAL_CURRENCY_MISMATCH"
  | "FINANCIAL_DIVISION_BY_ZERO"
  | "FINANCIAL_EVIDENCE_CONFLICT"
  | "FINANCIAL_CALCULATION_FAILED"
  | "FINANCIAL_EVALUATION_FAILED"
  | "INVALID_FINANCIAL_OVERRIDE"
  | "DATABASE_ERROR";
/**
 * Tipo documental declarado. La clasificacion automatica llega en Microfase 3.
 */
export type DocumentType =
  | "UNKNOWN"
  | "TERMS"
  | "TECHNICAL_ANNEX"
  | "FINANCIAL_ANNEX"
  | "EXPERIENCE_ANNEX"
  | "RISK_MATRIX"
  | "SCHEDULE"
  | "FORM"
  | "ADDENDUM"
  | "SUPPORTING_DOCUMENT";
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
/**
 * Resultado del intento de carga de un documento.
 */
export type DocumentUploadStatus = "STORED" | "REJECTED";
/**
 * Origen de un proceso. La ingesta automatica llegara en la Microfase 9.
 */
export type ProcessSource = "MANUAL";
/**
 * Estado operativo del proceso durante la importacion.
 *
 * ``READY_FOR_INVENTORY`` significa unicamente que hay al menos un documento
 * almacenado y el proceso puede pasar a inventario documental (Microfase 3).
 * No significa "listo para presentar oferta" ni es un resultado GO.
 */
export type ProcessStatus = "DRAFT" | "DOCUMENTS_PENDING" | "READY_FOR_INVENTORY";

/**
 * Contenedor exclusivamente para la generacion conjunta de esquemas.
 *
 * No es un contrato de intercambio: agrupa los contratos de importacion
 * manual para producir un unico JSON Schema con ``$defs`` compartidos.
 */
export interface ManualImport {
  api_error: ApiError;
  document_upload_response: DocumentUploadResponse;
  document_upload_result: DocumentUploadResult;
  process_create: ProcessCreate;
  process_detail: ProcessDetail;
  process_document_list: ProcessDocumentList;
  process_document_metadata: ProcessDocumentMetadata;
  process_list: ProcessList;
  process_summary: ProcessSummary;
}
/**
 * Error estructurado devuelto por la API. Nunca expone detalles internos.
 */
export interface ApiError {
  code:
    | UploadErrorCode
    | ExtractionErrorCode
    | NormalizationErrorCode
    | CompanyErrorCode
    | FinancialErrorCode;
  details?: {
    [k: string]: string;
  };
  message: string;
}
/**
 * Respuesta de la carga multiple: un resultado explicito por archivo.
 */
export interface DocumentUploadResponse {
  process_id: string;
  rejected_count: number;
  results: DocumentUploadResult[];
  stored_count: number;
}
/**
 * Resultado individual de la carga de un archivo (comportamiento parcial explicito).
 */
export interface DocumentUploadResult {
  document?: ProcessDocumentMetadata | null;
  error?: ApiError | null;
  original_filename: string;
  upload_status: DocumentUploadStatus;
}
/**
 * Metadata de un documento cargado. No incluye storage_key ni rutas fisicas.
 */
export interface ProcessDocumentMetadata {
  created_at: string;
  declared_content_type: string | null;
  detected_content_type: string | null;
  document_type: DocumentType;
  extension: string;
  id: string;
  original_filename: string;
  processing_status: DocumentProcessingStatus;
  sha256: string;
  size_bytes: number;
  upload_status: DocumentUploadStatus;
}
/**
 * Datos para registrar manualmente un proceso de contratacion.
 */
export interface ProcessCreate {
  closing_at?: string | null;
  contracting_entity: string;
  currency?: string;
  description?: string | null;
  estimated_value?: number | string | null;
  published_at?: string | null;
  secop_reference?: string | null;
  selection_method?: string | null;
  source_url?: string | null;
  title: string;
}
/**
 * Detalle completo de un proceso, incluido su inventario documental.
 */
export interface ProcessDetail {
  closing_at: string | null;
  contracting_entity: string;
  created_at: string;
  currency: string;
  description: string | null;
  document_count: number;
  documents: ProcessDocumentMetadata[];
  /**
   * Valor estimado serializado como string decimal para no perder precision.
   */
  estimated_value: string | null;
  id: string;
  internal_reference: string;
  published_at: string | null;
  secop_reference: string | null;
  selection_method: string | null;
  source: ProcessSource;
  source_url: string | null;
  status: ProcessStatus;
  title: string;
  updated_at: string;
}
/**
 * Inventario basico de documentos de un proceso.
 */
export interface ProcessDocumentList {
  documents: ProcessDocumentMetadata[];
  process_id: string;
  total: number;
}
/**
 * Pagina de procesos: los items de la pagina y el total real.
 */
export interface ProcessList {
  items: ProcessSummary[];
  limit: number;
  offset: number;
  total: number;
}
/**
 * Resumen de un proceso para listados.
 */
export interface ProcessSummary {
  closing_at: string | null;
  contracting_entity: string;
  created_at: string;
  document_count: number;
  id: string;
  internal_reference: string;
  secop_reference: string | null;
  status: ProcessStatus;
  title: string;
}
