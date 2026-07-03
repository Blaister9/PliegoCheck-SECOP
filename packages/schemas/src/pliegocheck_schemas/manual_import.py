"""Contratos de importacion manual de procesos y documentos (Microfase 2).

Definicion canonica de los contratos entre web y API para crear procesos,
consultarlos y cargar documentos. Ver ``docs/manual-import.md``.

Decisiones documentadas:

- ``estimated_value`` es ``Decimal`` (nunca float); en JSON viaja como number
  o string y la API lo serializa como string para no perder precision.
- Las fechas usan zona horaria obligatoria (``AwareDatetime``).
- ``closing_at`` no puede ser anterior a ``published_at``.
- Los contratos de respuesta nunca exponen ``storage_key`` ni rutas fisicas.
- La carga multiple es de resultado parcial explicito: cada archivo tiene su
  propio resultado (``STORED`` o ``REJECTED`` con codigo de error).
"""

from decimal import Decimal
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    StringConstraints,
    model_validator,
)

from pliegocheck_schemas.company_profile import CompanyErrorCode
from pliegocheck_schemas.document_extraction import DocumentProcessingStatus, ExtractionErrorCode
from pliegocheck_schemas.financial_evaluation import FinancialErrorCode
from pliegocheck_schemas.normalized_requirement import NormalizationErrorCode

MANUAL_IMPORT_SCHEMA_VERSION = "1.0.0"

NonBlankStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
CurrencyCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]


class ProcessSource(StrEnum):
    """Origen de un proceso. La ingesta automatica llegara en la Microfase 9."""

    MANUAL = "MANUAL"


class ProcessStatus(StrEnum):
    """Estado operativo del proceso durante la importacion.

    ``READY_FOR_INVENTORY`` significa unicamente que hay al menos un documento
    almacenado y el proceso puede pasar a inventario documental (Microfase 3).
    No significa "listo para presentar oferta" ni es un resultado GO.
    """

    DRAFT = "DRAFT"
    DOCUMENTS_PENDING = "DOCUMENTS_PENDING"
    READY_FOR_INVENTORY = "READY_FOR_INVENTORY"


class DocumentType(StrEnum):
    """Tipo documental declarado. La clasificacion automatica llega en Microfase 3."""

    UNKNOWN = "UNKNOWN"
    TERMS = "TERMS"
    TECHNICAL_ANNEX = "TECHNICAL_ANNEX"
    FINANCIAL_ANNEX = "FINANCIAL_ANNEX"
    EXPERIENCE_ANNEX = "EXPERIENCE_ANNEX"
    RISK_MATRIX = "RISK_MATRIX"
    SCHEDULE = "SCHEDULE"
    FORM = "FORM"
    ADDENDUM = "ADDENDUM"
    SUPPORTING_DOCUMENT = "SUPPORTING_DOCUMENT"


class DocumentUploadStatus(StrEnum):
    """Resultado del intento de carga de un documento."""

    STORED = "STORED"
    REJECTED = "REJECTED"


class UploadErrorCode(StrEnum):
    """Codigos de error de dominio de la importacion manual."""

    PROCESS_NOT_FOUND = "PROCESS_NOT_FOUND"
    DOCUMENT_NOT_FOUND = "DOCUMENT_NOT_FOUND"
    INVALID_PROCESS_DATA = "INVALID_PROCESS_DATA"
    FILE_EMPTY = "FILE_EMPTY"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    FILE_TYPE_NOT_ALLOWED = "FILE_TYPE_NOT_ALLOWED"
    FILE_CONTENT_MISMATCH = "FILE_CONTENT_MISMATCH"
    DUPLICATE_DOCUMENT = "DUPLICATE_DOCUMENT"
    STORAGE_ERROR = "STORAGE_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"


ApiErrorCode = (
    UploadErrorCode
    | ExtractionErrorCode
    | NormalizationErrorCode
    | CompanyErrorCode
    | FinancialErrorCode
)


class ApiError(BaseModel):
    """Error estructurado devuelto por la API. Nunca expone detalles internos."""

    model_config = ConfigDict(extra="forbid")

    code: ApiErrorCode
    message: str
    details: dict[str, str] = Field(default_factory=dict)


class ProcessCreate(BaseModel):
    """Datos para registrar manualmente un proceso de contratacion."""

    model_config = ConfigDict(extra="forbid")

    title: NonBlankStr
    contracting_entity: NonBlankStr
    secop_reference: NonBlankStr | None = None
    description: str | None = Field(default=None, max_length=5000)
    source_url: HttpUrl | None = None
    selection_method: NonBlankStr | None = None
    estimated_value: Decimal | None = Field(default=None, ge=0)
    currency: CurrencyCode = "COP"
    published_at: AwareDatetime | None = None
    closing_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def closing_not_before_published(self) -> "ProcessCreate":
        if (
            self.published_at is not None
            and self.closing_at is not None
            and self.closing_at < self.published_at
        ):
            msg = "closing_at no puede ser anterior a published_at"
            raise ValueError(msg)
        return self


class ProcessDocumentMetadata(BaseModel):
    """Metadata de un documento cargado. No incluye storage_key ni rutas fisicas."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    original_filename: str
    document_type: DocumentType
    extension: str
    size_bytes: int = Field(gt=0)
    sha256: Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
    declared_content_type: str | None
    detected_content_type: str | None
    upload_status: DocumentUploadStatus
    processing_status: DocumentProcessingStatus
    created_at: AwareDatetime


class ProcessDocumentList(BaseModel):
    """Inventario basico de documentos de un proceso."""

    model_config = ConfigDict(extra="forbid")

    process_id: UUID
    total: int = Field(ge=0)
    documents: list[ProcessDocumentMetadata]


class ProcessSummary(BaseModel):
    """Resumen de un proceso para listados."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    internal_reference: str
    secop_reference: str | None
    title: str
    contracting_entity: str
    status: ProcessStatus
    closing_at: AwareDatetime | None
    document_count: int = Field(ge=0)
    created_at: AwareDatetime


class ProcessDetail(BaseModel):
    """Detalle completo de un proceso, incluido su inventario documental."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    internal_reference: str
    secop_reference: str | None
    title: str
    contracting_entity: str
    description: str | None
    source_url: str | None
    selection_method: str | None
    estimated_value: str | None = Field(
        description="Valor estimado serializado como string decimal para no perder precision.",
    )
    currency: str
    published_at: AwareDatetime | None
    closing_at: AwareDatetime | None
    status: ProcessStatus
    source: ProcessSource
    document_count: int = Field(ge=0)
    documents: list[ProcessDocumentMetadata]
    created_at: AwareDatetime
    updated_at: AwareDatetime


class ProcessList(BaseModel):
    """Pagina de procesos: los items de la pagina y el total real."""

    model_config = ConfigDict(extra="forbid")

    items: list[ProcessSummary]
    total: int = Field(ge=0)
    limit: int = Field(gt=0)
    offset: int = Field(ge=0)


class DocumentUploadResult(BaseModel):
    """Resultado individual de la carga de un archivo (comportamiento parcial explicito)."""

    model_config = ConfigDict(extra="forbid")

    original_filename: str
    upload_status: DocumentUploadStatus
    document: ProcessDocumentMetadata | None = None
    error: ApiError | None = None


class DocumentUploadResponse(BaseModel):
    """Respuesta de la carga multiple: un resultado explicito por archivo."""

    model_config = ConfigDict(extra="forbid")

    process_id: UUID
    results: list[DocumentUploadResult]
    stored_count: int = Field(ge=0)
    rejected_count: int = Field(ge=0)


class ManualImportContracts(BaseModel):
    """Contenedor exclusivamente para la generacion conjunta de esquemas.

    No es un contrato de intercambio: agrupa los contratos de importacion
    manual para producir un unico JSON Schema con ``$defs`` compartidos.
    """

    model_config = ConfigDict(extra="forbid")

    process_create: ProcessCreate
    process_summary: ProcessSummary
    process_detail: ProcessDetail
    process_list: ProcessList
    process_document_metadata: ProcessDocumentMetadata
    process_document_list: ProcessDocumentList
    document_upload_result: DocumentUploadResult
    document_upload_response: DocumentUploadResponse
    api_error: ApiError
