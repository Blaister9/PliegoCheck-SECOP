// Archivo generado automaticamente por packages/schemas/scripts/generate.py.
// No editar a mano: la definicion canonica son los modelos Pydantic de
// packages/schemas/src/pliegocheck_schemas/.

export const PILOT_SCHEMA_VERSION = "1.0.0";

export const PILOT_STEP_NAME_VALUES = [
  "SEED_USERS",
  "SEED_PROCESS",
  "UPLOAD_DOCUMENTS",
  "EXTRACTION",
  "NORMALIZATION",
  "SEED_COMPANY",
  "PUBLISH_SNAPSHOT",
  "FINANCIAL_EVALUATION",
  "LEGAL_EVALUATION",
  "EXPERIENCE_EVALUATION",
  "TECHNICAL_EVALUATION",
  "DECISION",
  "REPORT_PACKAGE",
  "PACKAGE_DOWNLOAD",
  "AUDIT",
] as const;
export type PilotStepNameValue = (typeof PILOT_STEP_NAME_VALUES)[number];

export const PILOT_STEP_STATE_VALUES = [
  "PENDING",
  "RUNNING",
  "COMPLETED",
  "COMPLETED_WITH_WARNINGS",
  "SKIPPED",
  "FAILED",
] as const;
export type PilotStepStateValue = (typeof PILOT_STEP_STATE_VALUES)[number];
