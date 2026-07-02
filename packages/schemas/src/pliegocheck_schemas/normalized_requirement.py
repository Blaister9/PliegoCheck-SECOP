"""Contrato ``NormalizedRequirement`` v1.

Representa un requisito normalizado de un proceso SECOP II, segun la semantica
definida en ``docs/decision-engine.md``, ``docs/domain-model.md`` y
``docs/agent-contracts.md``.

Decisiones documentadas:

- Todos los campos de primer nivel son obligatorios: un productor debe declarar
  explicitamente ``status``, ``confidence`` y ``requires_human_review``; la
  omision silenciosa no es valida en el contrato de intercambio.
- ``expected_value`` y ``company_value`` admiten escalares JSON
  (string, number, boolean) o ``null``. Las estructuras compuestas se
  incorporaran con una nueva version del contrato cuando un caso real las exija.
- Lo desconocido se representa explicitamente (``UNKNOWN`` / ``null``);
  nunca se rellena con valores plausibles.
"""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

NORMALIZED_REQUIREMENT_SCHEMA_VERSION = "1.0.0"

NonBlankStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

ComparableValue = str | int | float | bool | None
"""Valor comparable de un requisito: escalar JSON o null (decision v1)."""


class RequirementCategory(StrEnum):
    """Categorias iniciales de requisitos (ver docs/domain-model.md)."""

    LEGAL = "LEGAL"
    FINANCIAL = "FINANCIAL"
    ORGANIZATIONAL = "ORGANIZATIONAL"
    EXPERIENCE = "EXPERIENCE"
    TECHNICAL = "TECHNICAL"
    WORKFORCE = "WORKFORCE"
    GUARANTEE = "GUARANTEE"
    SCHEDULE = "SCHEDULE"
    ECONOMIC = "ECONOMIC"
    OPERATIONAL = "OPERATIONAL"
    DOCUMENTARY = "DOCUMENTARY"
    RISK_AND_INELIGIBILITY = "RISK_AND_INELIGIBILITY"


class RequirementStatus(StrEnum):
    """Estado de cumplimiento de un requisito (ver docs/decision-engine.md)."""

    COMPLIES = "COMPLIES"
    DOES_NOT_COMPLY = "DOES_NOT_COMPLY"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"


class RequirementCriticality(StrEnum):
    """Criticidad de un requisito (ver docs/decision-engine.md)."""

    BLOCKING = "BLOCKING"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFORMATIONAL = "INFORMATIONAL"


class RequirementSubsanability(StrEnum):
    """Subsanabilidad de un requisito (ver docs/decision-engine.md)."""

    SUBSANABLE = "SUBSANABLE"
    NON_SUBSANABLE = "NON_SUBSANABLE"
    CONDITIONAL = "CONDITIONAL"
    UNKNOWN = "UNKNOWN"


class SourceLocation(BaseModel):
    """Ubicacion del requisito dentro del documento de origen."""

    model_config = ConfigDict(extra="forbid")

    page: int | None = Field(
        default=None,
        gt=0,
        description="Pagina del documento de origen; cuando existe, debe ser mayor que cero.",
    )
    section: str | None = Field(
        default=None,
        description="Seccion o numeral del documento de origen (por ejemplo '3.2').",
    )


class NormalizedRequirement(BaseModel):
    """Requisito normalizado de un proceso, entrada del motor deterministico."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0.0"] = Field(
        description="Version del contrato NormalizedRequirement.",
    )
    requirement_id: NonBlankStr = Field(
        description="Identificador unico del requisito dentro del proceso (por ejemplo 'REQ-001').",
    )
    category: RequirementCategory = Field(
        description="Categoria del requisito.",
    )
    description: NonBlankStr = Field(
        description="Texto normalizado del requisito, fiel al documento de origen.",
    )
    source_document_id: NonBlankStr = Field(
        description="Identificador del documento del que proviene el requisito.",
    )
    source_location: SourceLocation = Field(
        description="Ubicacion exacta del requisito en el documento de origen.",
    )
    criticality: RequirementCriticality = Field(
        description="Criticidad del requisito para la decision.",
    )
    subsanability: RequirementSubsanability = Field(
        description="Subsanabilidad segun el pliego; UNKNOWN cuando no es determinable.",
    )
    expected_value: ComparableValue = Field(
        description=(
            "Valor exigido por el pliego cuando el requisito es cuantificable; "
            "null cuando no aplica o no esta escrito explicitamente."
        ),
    )
    company_value: ComparableValue = Field(
        description=(
            "Valor acreditado por la empresa con evidencia; null cuando no se conoce. "
            "Nunca se rellena con valores plausibles."
        ),
    )
    status: RequirementStatus = Field(
        description="Estado de cumplimiento; UNKNOWN cuando no hay evidencia suficiente.",
    )
    evidence_ids: list[str] = Field(
        description="Identificadores de las evidencias que respaldan el status.",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confianza del agente (0 a 1). Informativa: nunca sustituye la evidencia.",
    )
    requires_human_review: bool = Field(
        description="Marca el requisito para revision humana obligatoria.",
    )
