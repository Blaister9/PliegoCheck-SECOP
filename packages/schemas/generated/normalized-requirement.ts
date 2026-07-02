// Archivo generado automaticamente desde normalized-requirement.schema.json
// (pnpm schemas:generate). No editar a mano: la definicion canonica son los
// modelos Pydantic de packages/schemas/src/pliegocheck_schemas/.

/**
 * Requisito normalizado de un proceso, entrada del motor deterministico.
 */
export interface NormalizedRequirement {
  /**
   * Categoria del requisito.
   */
  category:
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
  company_value: string | number | boolean | null;
  /**
   * Confianza del agente (0 a 1). Informativa: nunca sustituye la evidencia.
   */
  confidence: number;
  /**
   * Criticidad del requisito para la decision.
   */
  criticality: "BLOCKING" | "HIGH" | "MEDIUM" | "LOW" | "INFORMATIONAL";
  /**
   * Texto normalizado del requisito, fiel al documento de origen.
   */
  description: string;
  /**
   * Identificadores de las evidencias que respaldan el status.
   */
  evidence_ids: string[];
  /**
   * Valor exigido por el pliego cuando el requisito es cuantificable; null cuando no aplica o no esta escrito explicitamente.
   */
  expected_value: string | number | boolean | null;
  /**
   * Identificador unico del requisito dentro del proceso (por ejemplo 'REQ-001').
   */
  requirement_id: string;
  /**
   * Marca el requisito para revision humana obligatoria.
   */
  requires_human_review: boolean;
  /**
   * Version del contrato NormalizedRequirement.
   */
  schema_version: "1.0.0";
  /**
   * Identificador del documento del que proviene el requisito.
   */
  source_document_id: string;
  source_location: SourceLocation;
  /**
   * Estado de cumplimiento; UNKNOWN cuando no hay evidencia suficiente.
   */
  status:
    | "COMPLIES"
    | "DOES_NOT_COMPLY"
    | "PARTIAL"
    | "UNKNOWN"
    | "NOT_APPLICABLE"
    | "CONFLICTING_EVIDENCE";
  /**
   * Subsanabilidad segun el pliego; UNKNOWN cuando no es determinable.
   */
  subsanability: "SUBSANABLE" | "NON_SUBSANABLE" | "CONDITIONAL" | "UNKNOWN";
}
/**
 * Ubicacion exacta del requisito en el documento de origen.
 */
export interface SourceLocation {
  /**
   * Pagina del documento de origen; cuando existe, debe ser mayor que cero.
   */
  page?: number | null;
  /**
   * Seccion o numeral del documento de origen (por ejemplo '3.2').
   */
  section?: string | null;
}
