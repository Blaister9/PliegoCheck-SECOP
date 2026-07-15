"""Contratos de autenticacion, autorizacion y operacion piloto."""

from enum import StrEnum
from typing import Annotated, Any
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints

AUTH_SCHEMA_VERSION = "1.0.0"

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
EmailText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=320)]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]


class AuthUserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    LOCKED = "LOCKED"
    PENDING = "PENDING"


class AuthRoleName(StrEnum):
    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    REVIEWER = "REVIEWER"
    VIEWER = "VIEWER"


class AuthPermission(StrEnum):
    PROCESS_READ = "process:read"
    PROCESS_WRITE = "process:write"
    DOCUMENT_WRITE = "document:write"
    NORMALIZATION_RUN = "normalization:run"
    COMPANY_READ = "company:read"
    COMPANY_WRITE = "company:write"
    EVALUATION_RUN = "evaluation:run"
    DECISION_RUN = "decision:run"
    DECISION_REVIEW = "decision:review"
    REPORT_GENERATE = "report:generate"
    REPORT_DOWNLOAD = "report:download"
    ADMIN_USERS = "admin:users"
    ADMIN_SETTINGS = "admin:settings"
    AUDIT_READ = "audit:read"
    EXTERNAL_SEARCH = "external:search"
    EXTERNAL_IMPORT = "external:import"
    EXTERNAL_READ = "external:read"
    EXTERNAL_SYNC = "external:sync"
    EXTERNAL_DOWNLOAD = "external:download"
    OPPORTUNITY_READ = "opportunity:read"
    OPPORTUNITY_DISCOVER = "opportunity:discover"
    OPPORTUNITY_ASSESS = "opportunity:assess"
    OPPORTUNITY_REVIEW = "opportunity:review"
    OPPORTUNITY_IMPORT = "opportunity:import"
    MONITOR_READ = "monitor:read"
    MONITOR_WRITE = "monitor:write"
    MONITOR_RUN = "monitor:run"
    ALERT_READ = "alert:read"
    ALERT_MANAGE = "alert:manage"
    NOTIFICATION_READ = "notification:read"
    NOTIFICATION_MANAGE_OWN = "notification:manage-own"
    NOTIFICATION_TEST = "notification:test"
    NOTIFICATION_OPERATE = "notification:operate"
    NOTIFICATION_ADMIN = "notification:admin"


class AuthErrorCode(StrEnum):
    AUTH_REQUIRED = "AUTH_REQUIRED"
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    AUTH_SESSION_EXPIRED = "AUTH_SESSION_EXPIRED"
    AUTH_PERMISSION_DENIED = "AUTH_PERMISSION_DENIED"
    AUTH_USER_DISABLED = "AUTH_USER_DISABLED"
    AUTH_USER_LOCKED = "AUTH_USER_LOCKED"
    AUTH_PASSWORD_TOO_SHORT = "AUTH_PASSWORD_TOO_SHORT"
    AUTH_INVALID_CURRENT_PASSWORD = "AUTH_INVALID_CURRENT_PASSWORD"
    AUTH_CONFIG_INVALID = "AUTH_CONFIG_INVALID"
    AUTH_USER_NOT_FOUND = "AUTH_USER_NOT_FOUND"
    AUTH_EMAIL_ALREADY_EXISTS = "AUTH_EMAIL_ALREADY_EXISTS"


class OperationalAuditEventType(StrEnum):
    AUTH_LOGIN_SUCCEEDED = "AUTH_LOGIN_SUCCEEDED"
    AUTH_LOGIN_FAILED = "AUTH_LOGIN_FAILED"
    AUTH_LOGOUT = "AUTH_LOGOUT"
    AUTH_PASSWORD_CHANGED = "AUTH_PASSWORD_CHANGED"
    AUTH_USER_CREATED = "AUTH_USER_CREATED"
    AUTH_USER_DISABLED = "AUTH_USER_DISABLED"
    AUTH_USER_ENABLED = "AUTH_USER_ENABLED"
    AUTH_ROLES_UPDATED = "AUTH_ROLES_UPDATED"
    PROCESS_CREATED = "PROCESS_CREATED"
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    NORMALIZATION_QUEUED = "NORMALIZATION_QUEUED"
    EVALUATION_QUEUED = "EVALUATION_QUEUED"
    DECISION_QUEUED = "DECISION_QUEUED"
    DECISION_REVIEWED = "DECISION_REVIEWED"
    REPORT_GENERATED = "REPORT_GENERATED"
    ARTIFACT_DOWNLOADED = "ARTIFACT_DOWNLOADED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    EXTERNAL_SEARCH_COMPLETED = "EXTERNAL_SEARCH_COMPLETED"
    EXTERNAL_SEARCH_FAILED = "EXTERNAL_SEARCH_FAILED"
    EXTERNAL_PROCESS_IMPORTED = "EXTERNAL_PROCESS_IMPORTED"
    EXTERNAL_IMPORT_SKIPPED_DUPLICATE = "EXTERNAL_IMPORT_SKIPPED_DUPLICATE"
    EXTERNAL_SYNC_QUEUED = "EXTERNAL_SYNC_QUEUED"
    EXTERNAL_DOCUMENT_DOWNLOAD_QUEUED = "EXTERNAL_DOCUMENT_DOWNLOAD_QUEUED"
    EXTERNAL_DOCUMENT_EXTRACTION_QUEUED = "EXTERNAL_DOCUMENT_EXTRACTION_QUEUED"
    OPPORTUNITY_DISCOVERY_REQUESTED = "OPPORTUNITY_DISCOVERY_REQUESTED"
    OPPORTUNITY_DISCOVERY_COMPLETED = "OPPORTUNITY_DISCOVERY_COMPLETED"
    OPPORTUNITY_ASSESSED = "OPPORTUNITY_ASSESSED"
    OPPORTUNITY_REASSESSED = "OPPORTUNITY_REASSESSED"
    OPPORTUNITY_SHORTLISTED = "OPPORTUNITY_SHORTLISTED"
    OPPORTUNITY_DISMISSED = "OPPORTUNITY_DISMISSED"
    OPPORTUNITY_PARTNER_REVIEW_REQUESTED = "OPPORTUNITY_PARTNER_REVIEW_REQUESTED"
    OPPORTUNITY_IMPORTED = "OPPORTUNITY_IMPORTED"
    OPPORTUNITY_DEEP_ANALYSIS_REQUESTED = "OPPORTUNITY_DEEP_ANALYSIS_REQUESTED"
    OPPORTUNITY_MONITOR_CREATED = "OPPORTUNITY_MONITOR_CREATED"
    OPPORTUNITY_MONITOR_UPDATED = "OPPORTUNITY_MONITOR_UPDATED"
    OPPORTUNITY_MONITOR_PAUSED = "OPPORTUNITY_MONITOR_PAUSED"
    OPPORTUNITY_MONITOR_RESUMED = "OPPORTUNITY_MONITOR_RESUMED"
    OPPORTUNITY_MONITOR_RUN_REQUESTED = "OPPORTUNITY_MONITOR_RUN_REQUESTED"
    OPPORTUNITY_MONITOR_RUN_COMPLETED = "OPPORTUNITY_MONITOR_RUN_COMPLETED"
    OPPORTUNITY_MONITOR_RUN_FAILED = "OPPORTUNITY_MONITOR_RUN_FAILED"
    OPPORTUNITY_ALERT_CREATED = "OPPORTUNITY_ALERT_CREATED"
    OPPORTUNITY_ALERT_READ = "OPPORTUNITY_ALERT_READ"
    OPPORTUNITY_ALERT_ARCHIVED = "OPPORTUNITY_ALERT_ARCHIVED"
    OPPORTUNITY_ALERT_RESOLVED = "OPPORTUNITY_ALERT_RESOLVED"
    NOTIFICATION_DESTINATION_CREATED = "NOTIFICATION_DESTINATION_CREATED"
    NOTIFICATION_DESTINATION_UPDATED = "NOTIFICATION_DESTINATION_UPDATED"
    NOTIFICATION_DESTINATION_PAUSED = "NOTIFICATION_DESTINATION_PAUSED"
    NOTIFICATION_DESTINATION_RESUMED = "NOTIFICATION_DESTINATION_RESUMED"
    NOTIFICATION_TEST_REQUESTED = "NOTIFICATION_TEST_REQUESTED"
    NOTIFICATION_SUBSCRIPTION_CREATED = "NOTIFICATION_SUBSCRIPTION_CREATED"
    NOTIFICATION_SUBSCRIPTION_UPDATED = "NOTIFICATION_SUBSCRIPTION_UPDATED"
    NOTIFICATION_SUBSCRIPTION_PAUSED = "NOTIFICATION_SUBSCRIPTION_PAUSED"
    NOTIFICATION_SUBSCRIPTION_RESUMED = "NOTIFICATION_SUBSCRIPTION_RESUMED"
    NOTIFICATION_OUTBOX_CREATED = "NOTIFICATION_OUTBOX_CREATED"
    NOTIFICATION_DELIVERED = "NOTIFICATION_DELIVERED"
    NOTIFICATION_RETRY_SCHEDULED = "NOTIFICATION_RETRY_SCHEDULED"
    NOTIFICATION_FAILED_PERMANENT = "NOTIFICATION_FAILED_PERMANENT"
    NOTIFICATION_CANCELLED = "NOTIFICATION_CANCELLED"
    NOTIFICATION_SUPPRESSED = "NOTIFICATION_SUPPRESSED"
    NOTIFICATION_RETRIED_MANUALLY = "NOTIFICATION_RETRIED_MANUALLY"
    NOTIFICATION_DIGEST_CREATED = "NOTIFICATION_DIGEST_CREATED"
    NOTIFICATION_RETENTION_EXECUTED = "NOTIFICATION_RETENTION_EXECUTED"


class AuthUserSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    email: EmailText
    display_name: ShortText
    status: AuthUserStatus
    roles: list[AuthRoleName] = Field(default_factory=list)
    permissions: list[AuthPermission] = Field(default_factory=list)
    last_login_at: AwareDatetime | None = None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class AuthCurrentUser(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user: AuthUserSummary
    roles: list[AuthRoleName]
    permissions: list[AuthPermission]
    auth_enabled: bool = True


class AuthLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailText
    password: Annotated[str, StringConstraints(min_length=1, max_length=500)]


class AuthLoginResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user: AuthUserSummary
    roles: list[AuthRoleName]
    permissions: list[AuthPermission]


class AuthChangePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: Annotated[str, StringConstraints(min_length=1, max_length=500)]
    new_password: Annotated[str, StringConstraints(min_length=1, max_length=500)]


class AuthUserCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailText
    display_name: ShortText
    password: Annotated[str, StringConstraints(min_length=1, max_length=500)]
    roles: list[AuthRoleName] = Field(default_factory=lambda: [AuthRoleName.VIEWER])


class AuthUserRoleUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    roles: list[AuthRoleName]


class AuthUserList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AuthUserSummary]
    total: int = Field(ge=0)
    limit: int = Field(gt=0)
    offset: int = Field(ge=0)


class AuthSessionSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    user_id: UUID
    expires_at: AwareDatetime
    created_at: AwareDatetime
    last_seen_at: AwareDatetime | None = None
    revoked_at: AwareDatetime | None = None


class OperationalAuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    actor_user_id: UUID | None
    actor_email_hash: Sha256 | None
    event_type: OperationalAuditEventType
    entity_type: ShortText | None
    entity_id: UUID | None
    action: ShortText
    status: ShortText
    ip_hash: Sha256 | None
    user_agent_hash: Sha256 | None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: AwareDatetime


class OperationalAuditEventList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[OperationalAuditEvent]
    total: int = Field(ge=0)
    limit: int = Field(gt=0)
    offset: int = Field(ge=0)


class SystemConfigSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    auth_enabled: bool
    pilot_mode: bool
    environment: ShortText
    storage_mode: ShortText
    ai_enabled: bool
    allowed_origins_count: int = Field(ge=0)
    upload_max_file_size_mb: int = Field(ge=1)
    security_headers_enabled: bool
    worker_capabilities: list[ShortText]
    version: ShortText
    commit: ShortText | None = None
    redacted: dict[str, str] = Field(default_factory=dict)


class HealthReadyDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ShortText
    service: ShortText
    version: ShortText
    checks: dict[str, str]


class PermissionDeniedError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: AuthErrorCode = AuthErrorCode.AUTH_PERMISSION_DENIED
    required_permission: AuthPermission | None = None
    request_id: str | None = None


class AuthContracts(BaseModel):
    """Contenedor para generacion conjunta de esquemas de auth."""

    model_config = ConfigDict(extra="forbid")

    current_user: AuthCurrentUser
    login_request: AuthLoginRequest
    login_response: AuthLoginResponse
    change_password_request: AuthChangePasswordRequest
    user_create_request: AuthUserCreateRequest
    user_role_update_request: AuthUserRoleUpdateRequest
    user_list: AuthUserList
    session_summary: AuthSessionSummary
    audit_event_list: OperationalAuditEventList
    system_config: SystemConfigSummary
    health_ready: HealthReadyDetail
    permission_denied: PermissionDeniedError
