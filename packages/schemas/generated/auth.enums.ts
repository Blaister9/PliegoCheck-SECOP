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
  "external:read",
  "external:sync",
  "external:download",
  "opportunity:read",
  "opportunity:discover",
  "opportunity:assess",
  "opportunity:review",
  "opportunity:import",
  "monitor:read",
  "monitor:write",
  "monitor:run",
  "alert:read",
  "alert:manage",
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
  "EXTERNAL_SYNC_QUEUED",
  "EXTERNAL_DOCUMENT_DOWNLOAD_QUEUED",
  "EXTERNAL_DOCUMENT_EXTRACTION_QUEUED",
  "OPPORTUNITY_DISCOVERY_REQUESTED",
  "OPPORTUNITY_DISCOVERY_COMPLETED",
  "OPPORTUNITY_ASSESSED",
  "OPPORTUNITY_REASSESSED",
  "OPPORTUNITY_SHORTLISTED",
  "OPPORTUNITY_DISMISSED",
  "OPPORTUNITY_PARTNER_REVIEW_REQUESTED",
  "OPPORTUNITY_IMPORTED",
  "OPPORTUNITY_DEEP_ANALYSIS_REQUESTED",
  "OPPORTUNITY_MONITOR_CREATED",
  "OPPORTUNITY_MONITOR_UPDATED",
  "OPPORTUNITY_MONITOR_PAUSED",
  "OPPORTUNITY_MONITOR_RESUMED",
  "OPPORTUNITY_MONITOR_RUN_REQUESTED",
  "OPPORTUNITY_MONITOR_RUN_COMPLETED",
  "OPPORTUNITY_MONITOR_RUN_FAILED",
  "OPPORTUNITY_ALERT_CREATED",
  "OPPORTUNITY_ALERT_READ",
  "OPPORTUNITY_ALERT_ARCHIVED",
  "OPPORTUNITY_ALERT_RESOLVED",
] as const;
export type OperationalAuditEventTypeValue = (typeof OPERATIONAL_AUDIT_EVENT_TYPE_VALUES)[number];
