"""Configuracion validada de la API."""

from functools import lru_cache
from pathlib import Path
from typing import Any

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
