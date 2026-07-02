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
  code: UploadErrorCode;
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
