// Archivo generado automaticamente por packages/schemas/scripts/generate.py.
// No editar a mano: la definicion canonica es el modelo Pydantic
// packages/schemas/src/pliegocheck_schemas/normalized_requirement.py.

export const NORMALIZED_REQUIREMENT_SCHEMA_VERSION = "1.0.0";

export const REQUIREMENT_CATEGORY_VALUES = [
  "LEGAL",
  "FINANCIAL",
  "ORGANIZATIONAL",
  "EXPERIENCE",
  "TECHNICAL",
  "WORKFORCE",
  "GUARANTEE",
  "SCHEDULE",
  "ECONOMIC",
  "OPERATIONAL",
  "DOCUMENTARY",
  "RISK_AND_INELIGIBILITY",
] as const;
export type RequirementCategoryValue = (typeof REQUIREMENT_CATEGORY_VALUES)[number];

export const REQUIREMENT_STATUS_VALUES = [
  "COMPLIES",
  "DOES_NOT_COMPLY",
  "PARTIAL",
  "UNKNOWN",
  "NOT_APPLICABLE",
  "CONFLICTING_EVIDENCE",
] as const;
export type RequirementStatusValue = (typeof REQUIREMENT_STATUS_VALUES)[number];

export const REQUIREMENT_CRITICALITY_VALUES = [
  "BLOCKING",
  "HIGH",
  "MEDIUM",
  "LOW",
  "INFORMATIONAL",
] as const;
export type RequirementCriticalityValue = (typeof REQUIREMENT_CRITICALITY_VALUES)[number];

export const REQUIREMENT_SUBSANABILITY_VALUES = [
  "SUBSANABLE",
  "NON_SUBSANABLE",
  "CONDITIONAL",
  "UNKNOWN",
] as const;
export type RequirementSubsanabilityValue = (typeof REQUIREMENT_SUBSANABILITY_VALUES)[number];
