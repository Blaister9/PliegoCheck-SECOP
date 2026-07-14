// Archivo generado automaticamente por packages/schemas/scripts/generate.py.
// No editar a mano: la definicion canonica son los modelos Pydantic de
// packages/schemas/src/pliegocheck_schemas/.

export const AUTH_SCHEMA_VERSION = "1.0.0";

export const AUTH_USER_STATUS_VALUES = ["ACTIVE", "DISABLED", "LOCKED", "PENDING"] as const;
export type AuthUserStatusValue = (typeof AUTH_USER_STATUS_VALUES)[number];

export const AUTH_ROLE_NAME_VALUES = ["ADMIN", "ANALYST", "REVIEWER", "VIEWER"] as const;
export type AuthRoleNameValue = (typeof AUTH_ROLE_NAME_VALUES)[number];

export const AUTH_PERMISSION_VALUES = [
  "process:read",
  "process:write",
  "document:write",
  "normalization:run",
  "company:read",
  "company:write",
  "evaluation:run",
  "decision:run",
  "decision:review",
  "report:generate",
  "report:download",
  "admin:users",
  "admin:settings",
  "audit:read",
  "external:search",
  "external:import",
] as const;
export type AuthPermissionValue = (typeof AUTH_PERMISSION_VALUES)[number];

export const AUTH_ERROR_CODE_VALUES = [
  "AUTH_REQUIRED",
  "AUTH_INVALID_CREDENTIALS",
  "AUTH_SESSION_EXPIRED",
  "AUTH_PERMISSION_DENIED",
  "AUTH_USER_DISABLED",
  "AUTH_USER_LOCKED",
  "AUTH_PASSWORD_TOO_SHORT",
  "AUTH_INVALID_CURRENT_PASSWORD",
  "AUTH_CONFIG_INVALID",
  "AUTH_USER_NOT_FOUND",
  "AUTH_EMAIL_ALREADY_EXISTS",
] as const;
export type AuthErrorCodeValue = (typeof AUTH_ERROR_CODE_VALUES)[number];

export const OPERATIONAL_AUDIT_EVENT_TYPE_VALUES = [
  "AUTH_LOGIN_SUCCEEDED",
  "AUTH_LOGIN_FAILED",
  "AUTH_LOGOUT",
  "AUTH_PASSWORD_CHANGED",
  "AUTH_USER_CREATED",
  "AUTH_USER_DISABLED",
  "AUTH_USER_ENABLED",
  "AUTH_ROLES_UPDATED",
  "PROCESS_CREATED",
  "DOCUMENT_UPLOADED",
  "NORMALIZATION_QUEUED",
  "EVALUATION_QUEUED",
  "DECISION_QUEUED",
  "DECISION_REVIEWED",
  "REPORT_GENERATED",
  "ARTIFACT_DOWNLOADED",
  "PERMISSION_DENIED",
  "EXTERNAL_SEARCH_COMPLETED",
  "EXTERNAL_SEARCH_FAILED",
  "EXTERNAL_PROCESS_IMPORTED",
  "EXTERNAL_IMPORT_SKIPPED_DUPLICATE",
] as const;
export type OperationalAuditEventTypeValue = (typeof OPERATIONAL_AUDIT_EVENT_TYPE_VALUES)[number];
