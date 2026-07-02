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
        "API de PliegoCheck-SECOP. Microfase 2: importacion manual de procesos "
        "y documentos originales, sin extraccion ni evaluacion GO / NO GO."
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


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
