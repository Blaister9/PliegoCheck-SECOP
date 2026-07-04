// Archivo generado automaticamente desde pilot.schema.json
// (pnpm schemas:generate). No editar a mano: la definicion canonica son los
// modelos Pydantic de packages/schemas/src/pliegocheck_schemas/.

/**
 * Estado de un paso del piloto.
 */
export type PilotStepState =
  "PENDING" | "RUNNING" | "COMPLETED" | "COMPLETED_WITH_WARNINGS" | "SKIPPED" | "FAILED";
/**
 * Pasos del flujo end-to-end del piloto.
 */
export type PilotStepName =
  | "SEED_USERS"
  | "SEED_PROCESS"
  | "UPLOAD_DOCUMENTS"
  | "EXTRACTION"
  | "NORMALIZATION"
  | "SEED_COMPANY"
  | "PUBLISH_SNAPSHOT"
  | "FINANCIAL_EVALUATION"
  | "LEGAL_EVALUATION"
  | "EXPERIENCE_EVALUATION"
  | "TECHNICAL_EVALUATION"
  | "DECISION"
  | "REPORT_PACKAGE"
  | "PACKAGE_DOWNLOAD"
  | "AUDIT";

/**
 * Contenedor para generar JSON Schema con defs compartidos.
 */
export interface Pilot {
  dataset_user: PilotDatasetUser;
  expected_outcome: PilotExpectedOutcome;
  readiness: PilotReadiness;
  run_summary: PilotRunSummary;
  schema_version?: "1.0.0";
  step_status: PilotStepStatus;
}
/**
 * Usuario sintetico del dataset de piloto (sin contrasena versionada).
 */
export interface PilotDatasetUser {
  display_name: string;
  email: string;
  /**
   * @minItems 1
   */
  roles: [string, ...string[]];
}
/**
 * Resultado esperado del dataset sintetico, sin depender de IA real.
 */
export interface PilotExpectedOutcome {
  action_min: number;
  decision_outcome: string;
  financial_complies_min: number;
  financial_does_not_comply_min: number;
  not_evaluated_expected: boolean;
  notes?: string | null;
  report_artifact_count: number;
  unknown_min: number;
}
/**
 * Estado de preparacion del entorno de piloto. Solo diagnostico.
 */
export interface PilotReadiness {
  admin_user_exists: boolean;
  auth_enabled: boolean;
  dataset_available: boolean;
  environment: string;
  is_local_environment: boolean;
  pilot_company_present: boolean;
  pilot_mode: boolean;
  pilot_process_present: boolean;
  pilot_users_present?: string[];
  ready: boolean;
  schema_version?: "1.0.0";
  warnings?: string[];
}
/**
 * Resumen estructurado de una corrida end-to-end del piloto.
 */
export interface PilotRunSummary {
  artifact_count: number;
  audit_event_count: number;
  company_id?: string | null;
  decision_outcome?: string | null;
  decision_run_id?: string | null;
  duration_seconds: number;
  financial_run_id?: string | null;
  normalization_run_id?: string | null;
  process_id?: string | null;
  report_package_id?: string | null;
  schema_version?: "1.0.0";
  snapshot_id?: string | null;
  specialized_run_ids?: string[];
  steps?: PilotStepStatus[];
  steps_failed: number;
  steps_succeeded: number;
  steps_total: number;
  synthetic_data_only?: true;
  warnings?: string[];
}
/**
 * Resultado de un paso individual del flujo de piloto.
 */
export interface PilotStepStatus {
  detail?: string | null;
  state: PilotStepState;
  step: PilotStepName;
  warnings?: string[];
}
