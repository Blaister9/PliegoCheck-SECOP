// Archivo generado automaticamente desde normalized-requirement.schema.json
// (pnpm schemas:generate). No editar a mano: la definicion canonica son los
// modelos Pydantic de packages/schemas/src/pliegocheck_schemas/.

/**
 * Categorias iniciales de requisitos.
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
export type RequirementCriticality =
  "BLOCKING" | "HIGH" | "MEDIUM" | "LOW" | "INFORMATIONAL" | "UNKNOWN";
export type RequirementBasis = "EXPLICIT" | "INFERRED" | "UNKNOWN";
export type RequirementEvidenceStatus =
  "VALIDATED" | "PARTIALLY_VALIDATED" | "REJECTED_UNSUPPORTED" | "UNKNOWN";
export type RequirementModality =
  "MANDATORY" | "OPTIONAL" | "CONDITIONAL" | "PROHIBITED" | "UNKNOWN";
export type RequirementReviewStatus = "PENDING" | "IN_REVIEW" | "ACCEPTED" | "REJECTED";
export type RequirementScope =
  | "PROPOSAL_SUBMISSION"
  | "HABILITATING"
  | "SCORING"
  | "CONTRACT_EXECUTION"
  | "INFORMATIONAL"
  | "UNKNOWN";
export type RequirementSubsanability = "SUBSANABLE" | "NON_SUBSANABLE" | "CONDITIONAL" | "UNKNOWN";

/**
 * Requisito persistido tras validacion deterministica de evidencia.
 */
export interface NormalizedRequirement {
  category: RequirementCategory;
  condition_text: string | null;
  confidence: number;
  created_at: string;
  criticality: RequirementCriticality;
  criticality_basis: RequirementBasis;
  description: string;
  evidence_status: RequirementEvidenceStatus;
  expected_value: ExpectedValue | null;
  id: string;
  is_active: boolean;
  modality: RequirementModality;
  normalization_run_id: string;
  process_id: string;
  requires_human_review: boolean;
  review_status: RequirementReviewStatus;
  scope: RequirementScope;
  stable_key: string;
  subsanability: RequirementSubsanability;
  subsanability_basis: RequirementBasis;
  updated_at: string;
}
/**
 * Valor exigido por el pliego cuando existe soporte explicito.
 */
export interface ExpectedValue {
  raw_text: string | null;
  unit: string | null;
  value: string | number | boolean | null;
}
