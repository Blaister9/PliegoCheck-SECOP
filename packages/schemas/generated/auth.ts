// Archivo generado automaticamente desde auth.schema.json
// (pnpm schemas:generate). No editar a mano: la definicion canonica son los
// modelos Pydantic de packages/schemas/src/pliegocheck_schemas/.

export type OperationalAuditEventType =
  | "AUTH_LOGIN_SUCCEEDED"
  | "AUTH_LOGIN_FAILED"
  | "AUTH_LOGOUT"
  | "AUTH_PASSWORD_CHANGED"
  | "AUTH_USER_CREATED"
  | "AUTH_USER_DISABLED"
  | "AUTH_USER_ENABLED"
  | "AUTH_ROLES_UPDATED"
  | "PROCESS_CREATED"
  | "DOCUMENT_UPLOADED"
  | "NORMALIZATION_QUEUED"
  | "EVALUATION_QUEUED"
  | "DECISION_QUEUED"
  | "DECISION_REVIEWED"
  | "REPORT_GENERATED"
  | "ARTIFACT_DOWNLOADED"
  | "PERMISSION_DENIED"
  | "EXTERNAL_SEARCH_COMPLETED"
  | "EXTERNAL_SEARCH_FAILED"
  | "EXTERNAL_PROCESS_IMPORTED"
  | "EXTERNAL_IMPORT_SKIPPED_DUPLICATE";
export type AuthPermission =
  | "process:read"
  | "process:write"
  | "document:write"
  | "normalization:run"
  | "company:read"
  | "company:write"
  | "evaluation:run"
  | "decision:run"
  | "decision:review"
  | "report:generate"
  | "report:download"
  | "admin:users"
  | "admin:settings"
  | "audit:read"
  | "external:search"
  | "external:import";
export type AuthRoleName = "ADMIN" | "ANALYST" | "REVIEWER" | "VIEWER";
export type AuthUserStatus = "ACTIVE" | "DISABLED" | "LOCKED" | "PENDING";

/**
 * Contenedor para generacion conjunta de esquemas de auth.
 */
export interface Auth {
  audit_event_list: OperationalAuditEventList;
  change_password_request: AuthChangePasswordRequest;
  current_user: AuthCurrentUser;
  health_ready: HealthReadyDetail;
  login_request: AuthLoginRequest;
  login_response: AuthLoginResponse;
  permission_denied: PermissionDeniedError;
  session_summary: AuthSessionSummary;
  system_config: SystemConfigSummary;
  user_create_request: AuthUserCreateRequest;
  user_list: AuthUserList;
  user_role_update_request: AuthUserRoleUpdateRequest;
}
export interface OperationalAuditEventList {
  items: OperationalAuditEvent[];
  limit: number;
  offset: number;
  total: number;
}
export interface OperationalAuditEvent {
  action: string;
  actor_email_hash: string | null;
  actor_user_id: string | null;
  created_at: string;
  entity_id: string | null;
  entity_type: string | null;
  event_type: OperationalAuditEventType;
  id: string;
  ip_hash: string | null;
  metadata?: {
    [k: string]: unknown;
  };
  status: string;
  user_agent_hash: string | null;
}
export interface AuthChangePasswordRequest {
  current_password: string;
  new_password: string;
}
export interface AuthCurrentUser {
  auth_enabled?: boolean;
  permissions: AuthPermission[];
  roles: AuthRoleName[];
  user: AuthUserSummary;
}
export interface AuthUserSummary {
  created_at: string;
  display_name: string;
  email: string;
  id: string;
  last_login_at?: string | null;
  permissions?: AuthPermission[];
  roles?: AuthRoleName[];
  status: AuthUserStatus;
  updated_at: string;
}
export interface HealthReadyDetail {
  checks: {
    [k: string]: string;
  };
  service: string;
  status: string;
  version: string;
}
export interface AuthLoginRequest {
  email: string;
  password: string;
}
export interface AuthLoginResponse {
  permissions: AuthPermission[];
  roles: AuthRoleName[];
  user: AuthUserSummary;
}
export interface PermissionDeniedError {
  code?:
    | "AUTH_REQUIRED"
    | "AUTH_INVALID_CREDENTIALS"
    | "AUTH_SESSION_EXPIRED"
    | "AUTH_PERMISSION_DENIED"
    | "AUTH_USER_DISABLED"
    | "AUTH_USER_LOCKED"
    | "AUTH_PASSWORD_TOO_SHORT"
    | "AUTH_INVALID_CURRENT_PASSWORD"
    | "AUTH_CONFIG_INVALID"
    | "AUTH_USER_NOT_FOUND"
    | "AUTH_EMAIL_ALREADY_EXISTS";
  request_id?: string | null;
  required_permission?: AuthPermission | null;
}
export interface AuthSessionSummary {
  created_at: string;
  expires_at: string;
  id: string;
  last_seen_at?: string | null;
  revoked_at?: string | null;
  user_id: string;
}
export interface SystemConfigSummary {
  ai_enabled: boolean;
  allowed_origins_count: number;
  auth_enabled: boolean;
  commit?: string | null;
  environment: string;
  pilot_mode: boolean;
  redacted?: {
    [k: string]: string;
  };
  security_headers_enabled: boolean;
  storage_mode: string;
  upload_max_file_size_mb: number;
  version: string;
  worker_capabilities: string[];
}
export interface AuthUserCreateRequest {
  display_name: string;
  email: string;
  password: string;
  roles?: AuthRoleName[];
}
export interface AuthUserList {
  items: AuthUserSummary[];
  limit: number;
  offset: number;
  total: number;
}
export interface AuthUserRoleUpdateRequest {
  roles: AuthRoleName[];
}
