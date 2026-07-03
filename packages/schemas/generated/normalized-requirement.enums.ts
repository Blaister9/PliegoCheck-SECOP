// Archivo generado automaticamente por packages/schemas/scripts/generate.py.
// No editar a mano: la definicion canonica son los modelos Pydantic de
// packages/schemas/src/pliegocheck_schemas/.

export const NORMALIZED_REQUIREMENT_SCHEMA_VERSION = "2.0.0";

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

export const REQUIREMENT_SCOPE_VALUES = [
  "PROPOSAL_SUBMISSION",
  "HABILITATING",
  "SCORING",
  "CONTRACT_EXECUTION",
  "INFORMATIONAL",
  "UNKNOWN",
] as const;
export type RequirementScopeValue = (typeof REQUIREMENT_SCOPE_VALUES)[number];

export const REQUIREMENT_MODALITY_VALUES = [
  "MANDATORY",
  "OPTIONAL",
  "CONDITIONAL",
  "PROHIBITED",
  "UNKNOWN",
] as const;
export type RequirementModalityValue = (typeof REQUIREMENT_MODALITY_VALUES)[number];

export const REQUIREMENT_CRITICALITY_VALUES = [
  "BLOCKING",
  "HIGH",
  "MEDIUM",
  "LOW",
  "INFORMATIONAL",
  "UNKNOWN",
] as const;
export type RequirementCriticalityValue = (typeof REQUIREMENT_CRITICALITY_VALUES)[number];

export const REQUIREMENT_BASIS_VALUES = ["EXPLICIT", "INFERRED", "UNKNOWN"] as const;
export type RequirementBasisValue = (typeof REQUIREMENT_BASIS_VALUES)[number];

export const REQUIREMENT_SUBSANABILITY_VALUES = [
  "SUBSANABLE",
  "NON_SUBSANABLE",
  "CONDITIONAL",
  "UNKNOWN",
] as const;
export type RequirementSubsanabilityValue = (typeof REQUIREMENT_SUBSANABILITY_VALUES)[number];

export const REQUIREMENT_EVIDENCE_STATUS_VALUES = [
  "VALIDATED",
  "PARTIALLY_VALIDATED",
  "REJECTED_UNSUPPORTED",
  "UNKNOWN",
] as const;
export type RequirementEvidenceStatusValue = (typeof REQUIREMENT_EVIDENCE_STATUS_VALUES)[number];

export const REQUIREMENT_REVIEW_STATUS_VALUES = [
  "PENDING",
  "IN_REVIEW",
  "ACCEPTED",
  "REJECTED",
] as const;
export type RequirementReviewStatusValue = (typeof REQUIREMENT_REVIEW_STATUS_VALUES)[number];

export const REQUIREMENT_EVIDENCE_ROLE_VALUES = ["PRIMARY", "SUPPORTING", "CONFLICTING"] as const;
export type RequirementEvidenceRoleValue = (typeof REQUIREMENT_EVIDENCE_ROLE_VALUES)[number];

export const REQUIREMENT_EVIDENCE_VALIDATION_STATUS_VALUES = [
  "VALID",
  "INVALID_SEGMENT",
  "QUOTE_NOT_FOUND",
  "OUTSIDE_SNAPSHOT",
  "LOCATION_MISMATCH",
] as const;
export type RequirementEvidenceValidationStatusValue =
  (typeof REQUIREMENT_EVIDENCE_VALIDATION_STATUS_VALUES)[number];

export const REQUIREMENT_RELATION_TYPE_VALUES = [
  "INDEPENDENT",
  "EXACT_DUPLICATE",
  "POTENTIAL_DUPLICATE",
  "POTENTIAL_CONFLICT",
  "POTENTIAL_AMENDMENT",
] as const;
export type RequirementRelationTypeValue = (typeof REQUIREMENT_RELATION_TYPE_VALUES)[number];

export const NORMALIZATION_PROVIDER_VALUES = ["openai", "fake"] as const;
export type NormalizationProviderValue = (typeof NORMALIZATION_PROVIDER_VALUES)[number];

export const REQUIREMENT_NORMALIZATION_STATUS_VALUES = [
  "PENDING",
  "PROCESSING",
  "COMPLETED",
  "COMPLETED_WITH_WARNINGS",
  "FAILED",
  "CANCELLED",
] as const;
export type RequirementNormalizationStatusValue =
  (typeof REQUIREMENT_NORMALIZATION_STATUS_VALUES)[number];

export const REJECTED_CANDIDATE_REASON_VALUES = [
  "SCHEMA_INVALID",
  "REJECTED_UNSUPPORTED",
  "INVALID_SEGMENT",
  "QUOTE_NOT_FOUND",
  "OUTSIDE_SNAPSHOT",
  "LOCATION_MISMATCH",
  "FORBIDDEN_DECISION",
  "EXACT_DUPLICATE",
] as const;
export type RejectedCandidateReasonValue = (typeof REJECTED_CANDIDATE_REASON_VALUES)[number];

export const NORMALIZATION_ERROR_CODE_VALUES = [
  "NORMALIZATION_DISABLED",
  "OPENAI_API_KEY_MISSING",
  "PROCESS_NOT_FOUND",
  "NORMALIZATION_RUN_NOT_FOUND",
  "REQUIREMENT_NOT_FOUND",
  "NO_ELIGIBLE_EXTRACTIONS",
  "NO_ELIGIBLE_SEGMENTS",
  "NORMALIZATION_ALREADY_ACTIVE",
  "NORMALIZATION_NOT_RETRYABLE",
  "NORMALIZATION_JOB_NOT_FOUND",
  "PROMPT_VERSION_NOT_FOUND",
  "PROMPT_INVALID",
  "PROVIDER_CONFIGURATION_ERROR",
  "PROVIDER_TRANSIENT_ERROR",
  "PROVIDER_RESPONSE_INVALID",
  "PROVIDER_REFUSAL",
  "PROVIDER_INCOMPLETE",
  "EVIDENCE_VALIDATION_FAILED",
  "DATABASE_ERROR",
] as const;
export type NormalizationErrorCodeValue = (typeof NORMALIZATION_ERROR_CODE_VALUES)[number];
