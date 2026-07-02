// Archivo generado automaticamente desde normalized-requirement.schema.json
// (pnpm schemas:generate). No editar a mano: la definicion canonica es el
// modelo Pydantic packages/schemas/src/pliegocheck_schemas/normalized_requirement.py.

/**
 * Categoria del requisito.
 */
export type RequirementCategory =
  | "LEGAL"
  | "FINANCIAL"
  | "ORGANIZATIONAL"
  | "EXPERIENCE"
  | "TECHNICAL"
  | "WORKFORCE"
  | "GUARANTEE"
  | "SCHEDULE"
  | "ECONOMIC"
  | "OPERATIONAL"
  | "DOCUMENTARY"
  | "RISK_AND_INELIGIBILITY";
/**
 * Valor acreditado por la empresa con evidencia; null cuando no se conoce. Nunca se rellena con valores plausibles.
 */
export type CompanyValue = string | number | boolean | null;
/**
 * Confianza del agente (0 a 1). Informativa: nunca sustituye la evidencia.
 */
export type Confidence = number;
/**
 * Criticidad del requisito para la decision.
 */
export type RequirementCriticality = "BLOCKING" | "HIGH" | "MEDIUM" | "LOW" | "INFORMATIONAL";
/**
 * Texto normalizado del requisito, fiel al documento de origen.
 */
export type Description = string;
/**
 * Identificadores de las evidencias que respaldan el status.
 */
export type EvidenceIds = string[];
/**
 * Valor exigido por el pliego cuando el requisito es cuantificable; null cuando no aplica o no esta escrito explicitamente.
 */
export type ExpectedValue = string | number | boolean | null;
/**
 * Identificador unico del requisito dentro del proceso (por ejemplo 'REQ-001').
 */
export type RequirementId = string;
/**
 * Marca el requisito para revision humana obligatoria.
 */
export type RequiresHumanReview = boolean;
/**
 * Version del contrato NormalizedRequirement.
 */
export type SchemaVersion = "1.0.0";
/**
 * Identificador del documento del que proviene el requisito.
 */
export type SourceDocumentId = string;
/**
 * Pagina del documento de origen; cuando existe, debe ser mayor que cero.
 */
export type Page = number | null;
/**
 * Seccion o numeral del documento de origen (por ejemplo '3.2').
 */
export type Section = string | null;
/**
 * Estado de cumplimiento; UNKNOWN cuando no hay evidencia suficiente.
 */
export type RequirementStatus =
  | "COMPLIES"
  | "DOES_NOT_COMPLY"
  | "PARTIAL"
  | "UNKNOWN"
  | "NOT_APPLICABLE"
  | "CONFLICTING_EVIDENCE";
/**
 * Subsanabilidad segun el pliego; UNKNOWN cuando no es determinable.
 */
export type RequirementSubsanability = "SUBSANABLE" | "NON_SUBSANABLE" | "CONDITIONAL" | "UNKNOWN";

/**
 * Requisito normalizado de un proceso, entrada del motor deterministico.
 */
export interface NormalizedRequirement {
  category: RequirementCategory;
  company_value: CompanyValue;
  confidence: Confidence;
  criticality: RequirementCriticality;
  description: Description;
  evidence_ids: EvidenceIds;
  expected_value: ExpectedValue;
  requirement_id: RequirementId;
  requires_human_review: RequiresHumanReview;
  schema_version: SchemaVersion;
  source_document_id: SourceDocumentId;
  source_location: SourceLocation;
  status: RequirementStatus;
  subsanability: RequirementSubsanability;
}
/**
 * Ubicacion exacta del requisito en el documento de origen.
 */
export interface SourceLocation {
  page?: Page;
  section?: Section;
}
