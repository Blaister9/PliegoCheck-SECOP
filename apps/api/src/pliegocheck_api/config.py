"""Configuracion validada de la API."""

from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings de runtime de la API.

    Los valores sensibles no tienen defaults. La aplicacion lee ``.env`` en
    desarrollo local y variables de entorno en CI/produccion.
    """

    model_config = SettingsConfigDict(
        env_file=(".env.example", ".env"),
        env_file_encoding="utf-8",
        enable_decoding=False,
        extra="ignore",
    )

    service_name: str = "api"
    version: str = "0.1.0"
    title: str = "PliegoCheck-SECOP API"
    description: str = (
        "API de PliegoCheck-SECOP. Microfase 4: importacion manual, inventario, "
        "extraccion documental deterministica y normalizacion de requisitos con evidencia, "
        "sin evaluacion GO / NO GO."
    )
    database_url: str = Field(validation_alias="DATABASE_URL")
    storage_path: Path = Field(validation_alias="PLIEGOCHECK_STORAGE_PATH")
    max_file_size_mb: int = Field(
        default=20,
        validation_alias="PLIEGOCHECK_MAX_FILE_SIZE_MB",
        ge=1,
        le=200,
    )
    allowed_web_origins: list[str] = Field(
        validation_alias="PLIEGOCHECK_ALLOWED_WEB_ORIGINS",
    )
    cors_allowed_origins: list[str] | None = Field(
        default=None,
        validation_alias="PLIEGOCHECK_CORS_ALLOWED_ORIGINS",
    )
    environment: str = Field(default="development", validation_alias="PLIEGOCHECK_ENVIRONMENT")
    pilot_mode: bool = Field(default=False, validation_alias="PLIEGOCHECK_PILOT_MODE")
    auth_enabled: bool = Field(default=True, validation_alias="PLIEGOCHECK_AUTH_ENABLED")
    auth_cookie_name: str = Field(
        default="pliegocheck_session",
        validation_alias="PLIEGOCHECK_AUTH_COOKIE_NAME",
    )
    auth_cookie_secure: bool = Field(
        default=False,
        validation_alias="PLIEGOCHECK_AUTH_COOKIE_SECURE",
    )
    auth_cookie_samesite: str = Field(
        default="lax",
        validation_alias="PLIEGOCHECK_AUTH_COOKIE_SAMESITE",
    )
    auth_session_ttl_minutes: int = Field(
        default=480,
        validation_alias="PLIEGOCHECK_AUTH_SESSION_TTL_MINUTES",
        ge=5,
        le=7 * 24 * 60,
    )
    auth_secret_key: str | None = Field(
        default=None,
        validation_alias="PLIEGOCHECK_AUTH_SECRET_KEY",
    )
    auth_password_min_length: int = Field(
        default=12,
        validation_alias="PLIEGOCHECK_AUTH_PASSWORD_MIN_LENGTH",
        ge=8,
        le=128,
    )
    auth_max_failed_attempts: int = Field(
        default=10,
        validation_alias="PLIEGOCHECK_AUTH_MAX_FAILED_ATTEMPTS",
        ge=1,
        le=100,
    )
    auth_lockout_minutes: int = Field(
        default=15,
        validation_alias="PLIEGOCHECK_AUTH_LOCKOUT_MINUTES",
        ge=1,
        le=24 * 60,
    )
    security_headers_enabled: bool = Field(
        default=True,
        validation_alias="PLIEGOCHECK_SECURITY_HEADERS_ENABLED",
    )
    extraction_max_seconds: int = Field(
        default=30,
        validation_alias="PLIEGOCHECK_EXTRACTION_MAX_SECONDS",
        ge=1,
        le=600,
    )
    extraction_max_characters: int = Field(
        default=500_000,
        validation_alias="PLIEGOCHECK_EXTRACTION_MAX_CHARACTERS",
        ge=1_000,
        le=10_000_000,
    )
    extraction_max_pages: int = Field(
        default=300,
        validation_alias="PLIEGOCHECK_EXTRACTION_MAX_PAGES",
        ge=1,
        le=5_000,
    )
    extraction_max_sheets: int = Field(
        default=50,
        validation_alias="PLIEGOCHECK_EXTRACTION_MAX_SHEETS",
        ge=1,
        le=500,
    )
    extraction_max_rows_per_sheet: int = Field(
        default=10_000,
        validation_alias="PLIEGOCHECK_EXTRACTION_MAX_ROWS_PER_SHEET",
        ge=1,
        le=1_000_000,
    )
    extraction_max_zip_entries: int = Field(
        default=2_000,
        validation_alias="PLIEGOCHECK_EXTRACTION_MAX_ZIP_ENTRIES",
        ge=1,
        le=100_000,
    )
    extraction_max_uncompressed_mb: int = Field(
        default=200,
        validation_alias="PLIEGOCHECK_EXTRACTION_MAX_UNCOMPRESSED_MB",
        ge=1,
        le=5_000,
    )
    extraction_max_compression_ratio: int = Field(
        default=100,
        validation_alias="PLIEGOCHECK_EXTRACTION_MAX_COMPRESSION_RATIO",
        ge=1,
        le=10_000,
    )
    worker_max_attempts: int = Field(
        default=3,
        validation_alias="PLIEGOCHECK_WORKER_MAX_ATTEMPTS",
        ge=1,
        le=20,
    )
    ai_enabled: bool = Field(default=False, validation_alias="PLIEGOCHECK_AI_ENABLED")
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_normalization_model: str = Field(
        default="gpt-5.5-pro",
        validation_alias="OPENAI_NORMALIZATION_MODEL",
    )
    openai_normalization_reasoning_effort: str = Field(
        default="high",
        validation_alias="OPENAI_NORMALIZATION_REASONING_EFFORT",
    )
    openai_normalization_background: bool = Field(
        default=True,
        validation_alias="OPENAI_NORMALIZATION_BACKGROUND",
    )
    openai_normalization_max_output_tokens: int = Field(
        default=16_000,
        validation_alias="OPENAI_NORMALIZATION_MAX_OUTPUT_TOKENS",
        ge=1_000,
        le=200_000,
    )
    openai_normalization_timeout_seconds: int = Field(
        default=600,
        validation_alias="OPENAI_NORMALIZATION_TIMEOUT_SECONDS",
        ge=10,
        le=7_200,
    )
    openai_normalization_poll_interval_seconds: int = Field(
        default=5,
        validation_alias="OPENAI_NORMALIZATION_POLL_INTERVAL_SECONDS",
        ge=1,
        le=120,
    )
    openai_normalization_max_calls_per_run: int = Field(
        default=50,
        validation_alias="OPENAI_NORMALIZATION_MAX_CALLS_PER_RUN",
        ge=1,
        le=1_000,
    )
    openai_normalization_max_segments_per_batch: int = Field(
        default=25,
        validation_alias="OPENAI_NORMALIZATION_MAX_SEGMENTS_PER_BATCH",
        ge=1,
        le=200,
    )
    openai_normalization_max_characters_per_batch: int = Field(
        default=40_000,
        validation_alias="OPENAI_NORMALIZATION_MAX_CHARACTERS_PER_BATCH",
        ge=1_000,
        le=500_000,
    )
    openai_normalization_max_total_characters: int = Field(
        default=500_000,
        validation_alias="OPENAI_NORMALIZATION_MAX_TOTAL_CHARACTERS",
        ge=1_000,
        le=10_000_000,
    )
    openai_normalization_max_retries: int = Field(
        default=3,
        validation_alias="OPENAI_NORMALIZATION_MAX_RETRIES",
        ge=0,
        le=10,
    )
    allow_fake_normalization_provider: bool = Field(
        default=False,
        validation_alias="PLIEGOCHECK_ALLOW_FAKE_NORMALIZATION_PROVIDER",
    )
    secop_enabled: bool = Field(default=False, validation_alias="PLIEGOCHECK_SECOP_ENABLED")
    secop_provider: str = Field(
        default="datos_abiertos",
        validation_alias="PLIEGOCHECK_SECOP_PROVIDER",
    )
    secop_base_url: str = Field(
        default="https://www.datos.gov.co",
        validation_alias="PLIEGOCHECK_SECOP_BASE_URL",
    )
    secop_app_token: str | None = Field(
        default=None,
        validation_alias="PLIEGOCHECK_SECOP_APP_TOKEN",
    )
    secop_timeout_seconds: int = Field(
        default=30,
        validation_alias="PLIEGOCHECK_SECOP_TIMEOUT_SECONDS",
        ge=1,
        le=120,
    )
    secop_max_page_size: int = Field(
        default=100,
        validation_alias="PLIEGOCHECK_SECOP_MAX_PAGE_SIZE",
        ge=1,
        le=1000,
    )
    secop_rate_limit_per_minute: int = Field(
        default=60,
        validation_alias="PLIEGOCHECK_SECOP_RATE_LIMIT_PER_MINUTE",
        ge=1,
        le=1000,
    )
    secop_cache_ttl_minutes: int = Field(
        default=60,
        validation_alias="PLIEGOCHECK_SECOP_CACHE_TTL_MINUTES",
        ge=0,
        le=1440,
    )
    secop_allow_live_tests: bool = Field(
        default=False,
        validation_alias="PLIEGOCHECK_SECOP_ALLOW_LIVE_TESTS",
    )
    secop_document_sync_enabled: bool = Field(
        default=False, validation_alias="PLIEGOCHECK_SECOP_DOCUMENT_SYNC_ENABLED"
    )
    secop_document_download_enabled: bool = Field(
        default=False, validation_alias="PLIEGOCHECK_SECOP_DOCUMENT_DOWNLOAD_ENABLED"
    )
    secop_document_max_file_size_bytes: int = Field(
        default=26_214_400,
        validation_alias="PLIEGOCHECK_SECOP_DOCUMENT_MAX_FILE_SIZE_BYTES",
        ge=1,
        le=209_715_200,
    )
    secop_document_max_files_per_sync: int = Field(
        default=25, validation_alias="PLIEGOCHECK_SECOP_DOCUMENT_MAX_FILES_PER_SYNC", ge=1, le=500
    )
    secop_document_timeout_seconds: int = Field(
        default=30, validation_alias="PLIEGOCHECK_SECOP_DOCUMENT_TIMEOUT_SECONDS", ge=1, le=120
    )
    secop_document_max_redirects: int = Field(
        default=3, validation_alias="PLIEGOCHECK_SECOP_DOCUMENT_MAX_REDIRECTS", ge=0, le=10
    )
    secop_document_allowed_hosts: list[str] = Field(
        default_factory=list, validation_alias="PLIEGOCHECK_SECOP_DOCUMENT_ALLOWED_HOSTS"
    )
    secop_document_allowed_content_types: list[str] = Field(
        default_factory=lambda: [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/csv",
            "text/plain",
        ],
        validation_alias="PLIEGOCHECK_SECOP_DOCUMENT_ALLOWED_CONTENT_TYPES",
    )
    secop_document_allow_live_tests: bool = Field(
        default=False, validation_alias="PLIEGOCHECK_SECOP_DOCUMENT_ALLOW_LIVE_TESTS"
    )
    secop_incremental_sync_enabled: bool = Field(
        default=True, validation_alias="PLIEGOCHECK_SECOP_INCREMENTAL_SYNC_ENABLED"
    )
    opportunities_enabled: bool = Field(
        default=True, validation_alias="PLIEGOCHECK_OPPORTUNITIES_ENABLED"
    )
    opportunities_max_candidates: int = Field(
        default=100,
        validation_alias="PLIEGOCHECK_OPPORTUNITIES_MAX_CANDIDATES",
        ge=1,
        le=500,
    )
    monitoring_enabled: bool = Field(
        default=False, validation_alias="PLIEGOCHECK_MONITORING_ENABLED"
    )
    monitor_scheduler_interval_seconds: int = Field(
        default=60,
        validation_alias="PLIEGOCHECK_MONITOR_SCHEDULER_INTERVAL_SECONDS",
        ge=10,
        le=3600,
    )
    monitor_max_active_runs: int = Field(
        default=5, validation_alias="PLIEGOCHECK_MONITOR_MAX_ACTIVE_RUNS", ge=1, le=100
    )
    monitor_max_results_per_run: int = Field(
        default=500, validation_alias="PLIEGOCHECK_MONITOR_MAX_RESULTS_PER_RUN", ge=1, le=5000
    )
    monitor_max_pages_per_run: int = Field(
        default=10, validation_alias="PLIEGOCHECK_MONITOR_MAX_PAGES_PER_RUN", ge=1, le=100
    )
    monitor_failure_alert_threshold: int = Field(
        default=3, validation_alias="PLIEGOCHECK_MONITOR_FAILURE_ALERT_THRESHOLD", ge=1, le=20
    )
    monitor_default_timezone: str = Field(
        default="America/Bogota", validation_alias="PLIEGOCHECK_MONITOR_DEFAULT_TIMEZONE"
    )
    alert_retention_days: int = Field(
        default=365, validation_alias="PLIEGOCHECK_ALERT_RETENTION_DAYS", ge=30, le=3650
    )
    external_delivery_enabled: bool = Field(
        default=False, validation_alias="PLIEGOCHECK_EXTERNAL_DELIVERY_ENABLED"
    )
    notification_dry_run: bool = Field(
        default=True, validation_alias="PLIEGOCHECK_NOTIFICATION_DRY_RUN"
    )
    notification_max_attempts: int = Field(
        default=5, validation_alias="PLIEGOCHECK_NOTIFICATION_MAX_ATTEMPTS", ge=1, le=20
    )
    notification_retry_base_seconds: int = Field(
        default=60, validation_alias="PLIEGOCHECK_NOTIFICATION_RETRY_BASE_SECONDS", ge=1, le=86400
    )
    notification_retry_max_seconds: int = Field(
        default=3600, validation_alias="PLIEGOCHECK_NOTIFICATION_RETRY_MAX_SECONDS", ge=1, le=604800
    )
    notification_retry_jitter_seconds: int = Field(
        default=30, validation_alias="PLIEGOCHECK_NOTIFICATION_RETRY_JITTER_SECONDS", ge=0, le=3600
    )
    notification_max_per_destination_per_hour: int = Field(
        default=20,
        validation_alias="PLIEGOCHECK_NOTIFICATION_MAX_PER_DESTINATION_PER_HOUR",
        ge=1,
        le=10000,
    )
    notification_max_per_destination_per_day: int = Field(
        default=100,
        validation_alias="PLIEGOCHECK_NOTIFICATION_MAX_PER_DESTINATION_PER_DAY",
        ge=1,
        le=100000,
    )
    notification_max_global_per_hour: int = Field(
        default=200,
        validation_alias="PLIEGOCHECK_NOTIFICATION_MAX_GLOBAL_PER_HOUR",
        ge=1,
        le=100000,
    )
    notification_max_digest_alerts: int = Field(
        default=50, validation_alias="PLIEGOCHECK_NOTIFICATION_MAX_DIGEST_ALERTS", ge=1, le=500
    )
    email_enabled: bool = Field(default=False, validation_alias="PLIEGOCHECK_EMAIL_ENABLED")
    smtp_host: str | None = Field(default=None, validation_alias="PLIEGOCHECK_SMTP_HOST")
    smtp_port: int = Field(default=587, validation_alias="PLIEGOCHECK_SMTP_PORT", ge=1, le=65535)
    smtp_username: str | None = Field(default=None, validation_alias="PLIEGOCHECK_SMTP_USERNAME")
    smtp_password: str | None = Field(default=None, validation_alias="PLIEGOCHECK_SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, validation_alias="PLIEGOCHECK_SMTP_USE_TLS")
    smtp_use_starttls: bool = Field(default=True, validation_alias="PLIEGOCHECK_SMTP_USE_STARTTLS")
    smtp_from_address: str | None = Field(
        default=None, validation_alias="PLIEGOCHECK_SMTP_FROM_ADDRESS"
    )
    smtp_from_name: str = Field(
        default="PliegoCheck", validation_alias="PLIEGOCHECK_SMTP_FROM_NAME"
    )
    smtp_timeout_seconds: int = Field(
        default=30, validation_alias="PLIEGOCHECK_SMTP_TIMEOUT_SECONDS", ge=1, le=120
    )
    smtp_allowed_recipient_domains: list[str] = Field(
        default_factory=list, validation_alias="PLIEGOCHECK_SMTP_ALLOWED_RECIPIENT_DOMAINS"
    )
    smtp_allow_local_insecure: bool = Field(
        default=False, validation_alias="PLIEGOCHECK_SMTP_ALLOW_LOCAL_INSECURE"
    )
    webhook_enabled: bool = Field(default=False, validation_alias="PLIEGOCHECK_WEBHOOK_ENABLED")
    webhook_allowed_hosts: list[str] = Field(
        default_factory=list, validation_alias="PLIEGOCHECK_WEBHOOK_ALLOWED_HOSTS"
    )
    webhook_timeout_seconds: int = Field(
        default=15, validation_alias="PLIEGOCHECK_WEBHOOK_TIMEOUT_SECONDS", ge=1, le=120
    )
    webhook_max_redirects: int = Field(
        default=0, validation_alias="PLIEGOCHECK_WEBHOOK_MAX_REDIRECTS", ge=0, le=3
    )
    webhook_max_payload_bytes: int = Field(
        default=65536, validation_alias="PLIEGOCHECK_WEBHOOK_MAX_PAYLOAD_BYTES", ge=1024, le=1048576
    )
    webhook_allow_local_insecure: bool = Field(
        default=False, validation_alias="PLIEGOCHECK_WEBHOOK_ALLOW_LOCAL_INSECURE"
    )
    pilot_allowed_recipients: list[str] = Field(
        default_factory=list, validation_alias="PLIEGOCHECK_PILOT_ALLOWED_RECIPIENTS"
    )
    pilot_allowed_recipient_domains: list[str] = Field(
        default_factory=list, validation_alias="PLIEGOCHECK_PILOT_ALLOWED_RECIPIENT_DOMAINS"
    )
    pilot_max_deliveries_per_day: int = Field(
        default=50, validation_alias="PLIEGOCHECK_PILOT_MAX_DELIVERIES_PER_DAY", ge=1, le=10000
    )
    notification_attempt_retention_days: int = Field(
        default=90,
        validation_alias="PLIEGOCHECK_NOTIFICATION_ATTEMPT_RETENTION_DAYS",
        ge=1,
        le=3650,
    )
    notification_payload_retention_days: int = Field(
        default=30,
        validation_alias="PLIEGOCHECK_NOTIFICATION_PAYLOAD_RETENTION_DAYS",
        ge=1,
        le=3650,
    )

    @field_validator(
        "secop_document_allowed_hosts",
        "secop_document_allowed_content_types",
        "smtp_allowed_recipient_domains",
        "webhook_allowed_hosts",
        "pilot_allowed_recipients",
        "pilot_allowed_recipient_domains",
        mode="before",
    )
    @classmethod
    def parse_csv_list(cls, value: Any) -> list[str]:
        if value in (None, ""):
            return []
        if isinstance(value, str):
            return [item.strip().lower() for item in value.split(",") if item.strip()]
        return [str(item).strip().lower() for item in value if str(item).strip()]

    @field_validator("allowed_web_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: Any) -> list[str]:
        return cls._parse_origins(value, "PLIEGOCHECK_ALLOWED_WEB_ORIGINS")

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str] | None:
        if value in (None, ""):
            return None
        return cls._parse_origins(value, "PLIEGOCHECK_CORS_ALLOWED_ORIGINS")

    @field_validator("auth_cookie_samesite")
    @classmethod
    def validate_samesite(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in {"lax", "strict", "none"}:
            msg = "PLIEGOCHECK_AUTH_COOKIE_SAMESITE debe ser lax, strict o none"
            raise ValueError(msg)
        return normalized

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in {"development", "test", "pilot"}:
            msg = "PLIEGOCHECK_ENVIRONMENT debe ser development, test o pilot"
            raise ValueError(msg)
        return normalized

    @field_validator("secop_provider")
    @classmethod
    def validate_secop_provider(cls, value: str) -> str:
        normalized = value.lower().strip()
        if normalized != "datos_abiertos":
            msg = "PLIEGOCHECK_SECOP_PROVIDER solo admite datos_abiertos"
            raise ValueError(msg)
        return normalized

    @field_validator("secop_base_url")
    @classmethod
    def validate_secop_base_url(cls, value: str) -> str:
        normalized = value.rstrip("/")
        parsed = urlsplit(normalized)
        if (
            parsed.scheme != "https"
            or parsed.hostname not in {"datos.gov.co", "www.datos.gov.co"}
            or parsed.port not in {None, 443}
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            msg = "PLIEGOCHECK_SECOP_BASE_URL debe ser el origen HTTPS oficial de datos.gov.co"
            raise ValueError(msg)
        return normalized

    @classmethod
    def _parse_origins(cls, value: Any, name: str) -> list[str]:
        if isinstance(value, str):
            origins = [origin.strip() for origin in value.split(",") if origin.strip()]
            if "*" in origins:
                msg = f"{name} no puede usar '*'"
                raise ValueError(msg)
            if not origins:
                msg = f"{name} debe incluir al menos un origen"
                raise ValueError(msg)
            return origins
        if isinstance(value, list):
            if "*" in value:
                msg = f"{name} no puede usar '*'"
                raise ValueError(msg)
            origins = [str(origin) for origin in value if str(origin).strip()]
            if not origins:
                msg = f"{name} debe incluir al menos un origen"
                raise ValueError(msg)
            return origins
        msg = f"{name} debe ser una lista o CSV de origenes"
        raise ValueError(msg)

    def model_post_init(self, __context: Any) -> None:
        _ = __context
        if self.auth_enabled and self.environment == "pilot" and not self.auth_secret_key:
            msg = "PLIEGOCHECK_AUTH_SECRET_KEY es obligatorio con auth en piloto"
            raise ValueError(msg)
        if self.pilot_mode and self.auth_enabled and not self.auth_secret_key:
            msg = "PLIEGOCHECK_AUTH_SECRET_KEY es obligatorio en PLIEGOCHECK_PILOT_MODE"
            raise ValueError(msg)
        if self.pilot_mode and not self.auth_cookie_secure:
            msg = "PLIEGOCHECK_AUTH_COOKIE_SECURE debe ser true en piloto con HTTPS"
            raise ValueError(msg)
        if self.pilot_mode and not self.auth_enabled:
            msg = "PLIEGOCHECK_AUTH_ENABLED=false no esta permitido en piloto"
            raise ValueError(msg)

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @property
    def extraction_max_uncompressed_bytes(self) -> int:
        return self.extraction_max_uncompressed_mb * 1024 * 1024

    @property
    def effective_cors_origins(self) -> list[str]:
        return self.cors_allowed_origins or self.allowed_web_origins


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
