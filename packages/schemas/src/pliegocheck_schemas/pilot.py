"""Contratos del piloto controlado end-to-end (Microfase 11).

El piloto usa exclusivamente datos sinteticos. Estos contratos describen el
resumen de una corrida end-to-end, el estado por paso, el resultado esperado
del dataset sintetico y la preparacion (readiness) del entorno de piloto.
"""

from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

PILOT_SCHEMA_VERSION: Literal["1.0.0"] = "1.0.0"

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class PilotStepName(StrEnum):
    """Pasos del flujo end-to-end del piloto."""

    SEED_USERS = "SEED_USERS"
    SEED_PROCESS = "SEED_PROCESS"
    UPLOAD_DOCUMENTS = "UPLOAD_DOCUMENTS"
    EXTRACTION = "EXTRACTION"
    NORMALIZATION = "NORMALIZATION"
    SEED_COMPANY = "SEED_COMPANY"
    PUBLISH_SNAPSHOT = "PUBLISH_SNAPSHOT"
    FINANCIAL_EVALUATION = "FINANCIAL_EVALUATION"
    LEGAL_EVALUATION = "LEGAL_EVALUATION"
    EXPERIENCE_EVALUATION = "EXPERIENCE_EVALUATION"
    TECHNICAL_EVALUATION = "TECHNICAL_EVALUATION"
    DECISION = "DECISION"
    REPORT_PACKAGE = "REPORT_PACKAGE"
    PACKAGE_DOWNLOAD = "PACKAGE_DOWNLOAD"
    AUDIT = "AUDIT"


class PilotStepState(StrEnum):
    """Estado de un paso del piloto."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"


class PilotStepStatus(BaseModel):
    """Resultado de un paso individual del flujo de piloto."""

    model_config = ConfigDict(extra="forbid")

    step: PilotStepName
    state: PilotStepState
    detail: str | None = None
    warnings: list[str] = Field(default_factory=list)


class PilotExpectedOutcome(BaseModel):
    """Resultado esperado del dataset sintetico, sin depender de IA real."""

    model_config = ConfigDict(extra="forbid")

    decision_outcome: str
    financial_complies_min: int = Field(ge=0)
    financial_does_not_comply_min: int = Field(ge=0)
    unknown_min: int = Field(ge=0)
    not_evaluated_expected: bool
    action_min: int = Field(ge=0)
    report_artifact_count: int = Field(ge=0)
    notes: str | None = None


class PilotRunSummary(BaseModel):
    """Resumen estructurado de una corrida end-to-end del piloto."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0.0"] = PILOT_SCHEMA_VERSION
    process_id: UUID | None = None
    company_id: UUID | None = None
    snapshot_id: UUID | None = None
    normalization_run_id: UUID | None = None
    financial_run_id: UUID | None = None
    specialized_run_ids: list[UUID] = Field(default_factory=list)
    decision_run_id: UUID | None = None
    report_package_id: UUID | None = None
    decision_outcome: str | None = None
    duration_seconds: float = Field(ge=0)
    steps: list[PilotStepStatus] = Field(default_factory=list)
    steps_total: int = Field(ge=0)
    steps_succeeded: int = Field(ge=0)
    steps_failed: int = Field(ge=0)
    artifact_count: int = Field(ge=0)
    audit_event_count: int = Field(ge=0)
    warnings: list[str] = Field(default_factory=list)
    synthetic_data_only: Literal[True] = True


class PilotDatasetUser(BaseModel):
    """Usuario sintetico del dataset de piloto (sin contrasena versionada)."""

    model_config = ConfigDict(extra="forbid")

    email: ShortText
    display_name: ShortText
    roles: list[str] = Field(min_length=1)


class PilotReadiness(BaseModel):
    """Estado de preparacion del entorno de piloto. Solo diagnostico."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0.0"] = PILOT_SCHEMA_VERSION
    environment: str
    pilot_mode: bool
    auth_enabled: bool
    is_local_environment: bool
    admin_user_exists: bool
    pilot_users_present: list[str] = Field(default_factory=list)
    pilot_process_present: bool
    pilot_company_present: bool
    dataset_available: bool
    ready: bool
    warnings: list[str] = Field(default_factory=list)


class PilotContracts(BaseModel):
    """Contenedor para generar JSON Schema con defs compartidos."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0.0"] = PILOT_SCHEMA_VERSION
    step_status: PilotStepStatus
    expected_outcome: PilotExpectedOutcome
    run_summary: PilotRunSummary
    dataset_user: PilotDatasetUser
    readiness: PilotReadiness
