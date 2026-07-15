"""Contratos de entrega externa controlada de alertas."""

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

NOTIFICATION_DELIVERY_SCHEMA_VERSION = "1.0.0"
NOTIFICATION_DISCLAIMER = (
    "Esta alerta señala una novedad o cambio relevante según la configuración de PliegoCheck. "
    "No constituye una recomendación automática de presentar oferta ni representa probabilidad "
    "de adjudicación."
)


class NotificationChannel(StrEnum):
    INTERNAL_ONLY = "INTERNAL_ONLY"
    EMAIL_SMTP = "EMAIL_SMTP"
    SIGNED_WEBHOOK = "SIGNED_WEBHOOK"


class NotificationDestinationStatus(StrEnum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DISABLED = "DISABLED"
    ERROR = "ERROR"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"


class NotificationDeliveryMode(StrEnum):
    IMMEDIATE = "IMMEDIATE"
    DAILY_DIGEST = "DAILY_DIGEST"
    WEEKLY_DIGEST = "WEEKLY_DIGEST"
    INTERNAL_ONLY = "INTERNAL_ONLY"


class NotificationOutboxStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    DELIVERED = "DELIVERED"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    FAILED_PERMANENT = "FAILED_PERMANENT"
    CANCELLED = "CANCELLED"
    SUPPRESSED = "SUPPRESSED"
    DRY_RUN = "DRY_RUN"


class NotificationAttemptStatus(StrEnum):
    DELIVERED = "DELIVERED"
    RETRYABLE = "RETRYABLE"
    PERMANENT = "PERMANENT"
    DRY_RUN = "DRY_RUN"


class NotificationDigestPeriod(StrEnum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"


class NotificationOperationAction(StrEnum):
    RETRY = "RETRY"
    CANCEL = "CANCEL"
    SUPPRESS = "SUPPRESS"


class NotificationDestinationCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    channel: NotificationChannel
    name: str = Field(min_length=1, max_length=200)
    email_address: str | None = Field(default=None, max_length=320)
    webhook_url: str | None = Field(default=None, max_length=2083)
    secret_reference: str | None = Field(default=None, pattern=r"^[A-Z][A-Z0-9_]{2,127}$")
    configuration: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_channel_fields(self) -> "NotificationDestinationCreateRequest":
        if self.channel == NotificationChannel.EMAIL_SMTP and not self.email_address:
            raise ValueError("El destino de correo requiere email_address.")
        if self.channel == NotificationChannel.SIGNED_WEBHOOK and (
            not self.webhook_url or not self.secret_reference
        ):
            raise ValueError("El webhook requiere URL y referencia de secreto.")
        return self


class NotificationDestinationUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=200)
    email_address: str | None = Field(default=None, max_length=320)
    webhook_url: str | None = Field(default=None, max_length=2083)
    secret_reference: str | None = Field(default=None, pattern=r"^[A-Z][A-Z0-9_]{2,127}$")
    configuration: dict[str, Any] | None = None


class NotificationDestinationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    owner_actor_id: UUID | None
    channel: NotificationChannel
    name: str
    status: NotificationDestinationStatus
    masked_destination: str
    verified_at: AwareDatetime | None = None
    last_tested_at: AwareDatetime | None = None
    last_test_status: str | None = None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class NotificationDestinationDetail(NotificationDestinationSummary):
    configuration: dict[str, Any] = Field(default_factory=dict)
    secret_configured: bool = False


class NotificationDestinationList(BaseModel):
    items: list[NotificationDestinationSummary]
    total: int


class NotificationQuietHours(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    end: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    critical_bypass: bool = True


class NotificationSubscriptionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    destination_id: UUID
    monitor_id: UUID | None = None
    delivery_mode: NotificationDeliveryMode = NotificationDeliveryMode.IMMEDIATE
    minimum_severity: str = Field(default="INFO", pattern="^(INFO|LOW|MEDIUM|HIGH|CRITICAL)$")
    alert_types: list[str] = Field(default_factory=list, max_length=100)
    quiet_hours: NotificationQuietHours | None = None
    timezone: str = Field(default="America/Bogota", min_length=1, max_length=64)
    daily_digest_time: str = Field(default="08:00", pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    weekly_digest_day: int = Field(default=0, ge=0, le=6)
    include_summary: bool = True
    include_opportunity_link: bool = True


class NotificationSubscriptionUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    delivery_mode: NotificationDeliveryMode | None = None
    minimum_severity: str | None = Field(default=None, pattern="^(INFO|LOW|MEDIUM|HIGH|CRITICAL)$")
    alert_types: list[str] | None = Field(default=None, max_length=100)
    quiet_hours: NotificationQuietHours | None = None
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    daily_digest_time: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    weekly_digest_day: int | None = Field(default=None, ge=0, le=6)
    include_summary: bool | None = None
    include_opportunity_link: bool | None = None


class NotificationSubscriptionSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    owner_actor_id: UUID | None
    destination_id: UUID
    monitor_id: UUID | None
    enabled: bool
    delivery_mode: NotificationDeliveryMode
    minimum_severity: str
    alert_types: list[str]
    timezone: str
    created_at: AwareDatetime
    updated_at: AwareDatetime


class NotificationSubscriptionDetail(NotificationSubscriptionSummary):
    quiet_hours: NotificationQuietHours | None = None
    daily_digest_time: str
    weekly_digest_day: int
    include_summary: bool
    include_opportunity_link: bool


class NotificationSubscriptionList(BaseModel):
    items: list[NotificationSubscriptionSummary]
    total: int


class NotificationTestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(default="Prueba controlada de PliegoCheck", max_length=500)


class NotificationTestResponse(BaseModel):
    delivery_id: UUID
    status: NotificationOutboxStatus


class NotificationAttemptSummary(BaseModel):
    id: UUID
    attempt_number: int
    status: NotificationAttemptStatus
    started_at: AwareDatetime
    finished_at: AwareDatetime | None = None
    http_status: int | None = None
    smtp_response_code: int | None = None
    latency_ms: int | None = None
    error_code: str | None = None
    error_message_sanitized: str | None = None


class NotificationDeliverySummary(BaseModel):
    id: UUID
    alert_id: UUID | None
    destination_id: UUID
    channel: NotificationChannel
    delivery_mode: NotificationDeliveryMode
    status: NotificationOutboxStatus
    masked_destination: str
    attempt_count: int
    available_at: AwareDatetime
    delivered_at: AwareDatetime | None = None
    last_error_code: str | None = None
    created_at: AwareDatetime


class NotificationDeliveryDetail(NotificationDeliverySummary):
    subject: str
    template_version: str
    payload_metadata: dict[str, Any]
    attempts: list[NotificationAttemptSummary] = Field(default_factory=list)
    disclaimer: str = NOTIFICATION_DISCLAIMER


class NotificationDeliveryList(BaseModel):
    items: list[NotificationDeliverySummary]
    total: int
    limit: int
    offset: int


class NotificationOperationRequest(BaseModel):
    action: NotificationOperationAction


class NotificationOperationResponse(BaseModel):
    delivery_id: UUID
    status: NotificationOutboxStatus


class NotificationDigestSummary(BaseModel):
    id: UUID
    destination_id: UUID
    period: NotificationDigestPeriod
    period_start: AwareDatetime
    period_end: AwareDatetime
    status: str
    alert_count: int
    outbox_message_id: UUID | None = None


class NotificationReadiness(BaseModel):
    external_delivery_enabled: bool
    dry_run: bool
    email_enabled: bool
    webhook_enabled: bool
    pending_count: int = 0
    processing_count: int = 0
    retryable_count: int = 0
    permanent_failure_count: int = 0
    delivered_last_24h: int = 0
    suppressed_last_24h: int = 0
    oldest_pending_age_seconds: int | None = None
    worker_last_seen: AwareDatetime | None = None
    digest_last_run: AwareDatetime | None = None
    retention_last_run: AwareDatetime | None = None
    reasons: list[str] = Field(default_factory=list)


class NotificationStatistics(BaseModel):
    by_status: dict[str, int]
    by_channel: dict[str, int]
    generated_at: AwareDatetime


class NotificationRetentionRequest(BaseModel):
    dry_run: bool = True
    batch_size: int = Field(default=500, ge=1, le=5000)


class NotificationRetentionResponse(BaseModel):
    dry_run: bool
    payloads_cleared: int
    attempts_deleted: int


class NotificationContracts(BaseModel):
    destination_create: NotificationDestinationCreateRequest
    destination_detail: NotificationDestinationDetail
    destination_list: NotificationDestinationList
    subscription_create: NotificationSubscriptionCreateRequest
    subscription_detail: NotificationSubscriptionDetail
    subscription_list: NotificationSubscriptionList
    test_response: NotificationTestResponse
    delivery_detail: NotificationDeliveryDetail
    delivery_list: NotificationDeliveryList
    operation: NotificationOperationResponse
    digest: NotificationDigestSummary
    readiness: NotificationReadiness
    statistics: NotificationStatistics
    retention: NotificationRetentionResponse
