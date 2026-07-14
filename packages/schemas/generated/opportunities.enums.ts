// Archivo generado automaticamente por packages/schemas/scripts/generate.py.
// No editar a mano: la definicion canonica son los modelos Pydantic de
// packages/schemas/src/pliegocheck_schemas/.

export const OPPORTUNITIES_SCHEMA_VERSION = "1.0.0";

export const OPPORTUNITY_DISCOVERY_STATUS_VALUES = [
  "PENDING",
  "PROCESSING",
  "COMPLETED",
  "COMPLETED_WITH_WARNINGS",
  "FAILED",
  "CANCELLED",
] as const;
export type OpportunityDiscoveryStatusValue = (typeof OPPORTUNITY_DISCOVERY_STATUS_VALUES)[number];

export const OPPORTUNITY_ANALYSIS_LEVEL_VALUES = [
  "METADATA_SCREENING",
  "DOCUMENT_SCREENING",
  "DEEP_ANALYSIS",
] as const;
export type OpportunityAnalysisLevelValue = (typeof OPPORTUNITY_ANALYSIS_LEVEL_VALUES)[number];

export const OPPORTUNITY_OUTCOME_VALUES = [
  "REVISAR_PRIMERO",
  "OPORTUNIDAD_POTENCIAL",
  "REQUIERE_ALIADO",
  "INFORMACION_INSUFICIENTE",
  "POCO_COMPATIBLE",
  "DESCARTAR",
] as const;
export type OpportunityOutcomeValue = (typeof OPPORTUNITY_OUTCOME_VALUES)[number];

export const OPPORTUNITY_URGENCY_STATUS_VALUES = [
  "CLOSED",
  "EXPIRED",
  "CRITICAL",
  "URGENT",
  "NORMAL",
  "LONG_HORIZON",
  "UNKNOWN",
] as const;
export type OpportunityUrgencyStatusValue = (typeof OPPORTUNITY_URGENCY_STATUS_VALUES)[number];

export const OPPORTUNITY_COMPONENT_VALUES = [
  "RELEVANCE",
  "UNSPSC_MATCH",
  "EXPERIENCE_MATCH",
  "FINANCIAL_FIT",
  "TECHNICAL_FIT",
  "LEGAL_READINESS",
  "GEOGRAPHIC_FIT",
  "VALUE_FIT",
  "DEADLINE_URGENCY",
  "DOCUMENT_READINESS",
  "INFORMATION_COMPLETENESS",
  "PARTNER_NEED",
] as const;
export type OpportunityComponentValue = (typeof OPPORTUNITY_COMPONENT_VALUES)[number];

export const OPPORTUNITY_COMPONENT_STATUS_VALUES = [
  "STRONG_MATCH",
  "MATCH",
  "PARTIAL_MATCH",
  "MISMATCH",
  "UNKNOWN",
  "NOT_APPLICABLE",
  "CONFLICTING",
] as const;
export type OpportunityComponentStatusValue = (typeof OPPORTUNITY_COMPONENT_STATUS_VALUES)[number];

export const OPPORTUNITY_REVIEW_ACTION_VALUES = [
  "ACKNOWLEDGE",
  "SHORTLIST",
  "DISMISS",
  "SEEK_PARTNER",
  "REQUEST_DEEP_ANALYSIS",
] as const;
export type OpportunityReviewActionValue = (typeof OPPORTUNITY_REVIEW_ACTION_VALUES)[number];

export const OPPORTUNITY_ERROR_CODE_VALUES = [
  "COMPANY_SNAPSHOT_REQUIRED",
  "COMPANY_SNAPSHOT_NOT_PUBLISHED",
  "DISCOVERY_RUN_NOT_FOUND",
  "OPPORTUNITY_NOT_FOUND",
  "INVALID_POLICY",
  "DEEP_ANALYSIS_BLOCKED",
  "INVALID_FILTER",
] as const;
export type OpportunityErrorCodeValue = (typeof OPPORTUNITY_ERROR_CODE_VALUES)[number];
