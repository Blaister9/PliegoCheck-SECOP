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
        if isinstance(value, str):
            origins = [origin.strip() for origin in value.split(",") if origin.strip()]
            if "*" in origins:
                msg = "PLIEGOCHECK_ALLOWED_WEB_ORIGINS no puede usar '*'"
                raise ValueError(msg)
            if not origins:
                msg = "PLIEGOCHECK_ALLOWED_WEB_ORIGINS debe incluir al menos un origen"
                raise ValueError(msg)
            return origins
        if isinstance(value, list):
            if "*" in value:
                msg = "PLIEGOCHECK_ALLOWED_WEB_ORIGINS no puede usar '*'"
                raise ValueError(msg)
            origins = [str(origin) for origin in value if str(origin).strip()]
            if not origins:
                msg = "PLIEGOCHECK_ALLOWED_WEB_ORIGINS debe incluir al menos un origen"
                raise ValueError(msg)
            return origins
        msg = "PLIEGOCHECK_ALLOWED_WEB_ORIGINS debe ser una lista o CSV de origenes"
        raise ValueError(msg)

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @property
    def extraction_max_uncompressed_bytes(self) -> int:
        return self.extraction_max_uncompressed_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
