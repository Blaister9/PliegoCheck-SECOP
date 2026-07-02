"""Contratos compartidos de PliegoCheck-SECOP.

La definicion canonica de cada contrato vive aqui como modelo Pydantic.
El JSON Schema y los tipos TypeScript se generan desde estos modelos
(ver ``scripts/generate.py``); nunca se editan a mano.
"""

from pliegocheck_schemas.manual_import import (
    MANUAL_IMPORT_SCHEMA_VERSION,
    ApiError,
    DocumentType,
    DocumentUploadResponse,
    DocumentUploadResult,
    DocumentUploadStatus,
    ManualImportContracts,
    ProcessCreate,
    ProcessDetail,
    ProcessDocumentList,
    ProcessDocumentMetadata,
    ProcessList,
    ProcessSource,
    ProcessStatus,
    ProcessSummary,
    UploadErrorCode,
)
from pliegocheck_schemas.normalized_requirement import (
    NORMALIZED_REQUIREMENT_SCHEMA_VERSION,
    NormalizedRequirement,
    RequirementCategory,
    RequirementCriticality,
    RequirementStatus,
    RequirementSubsanability,
    SourceLocation,
)

__all__ = [
    "MANUAL_IMPORT_SCHEMA_VERSION",
    "NORMALIZED_REQUIREMENT_SCHEMA_VERSION",
    "ApiError",
    "DocumentType",
    "DocumentUploadResponse",
    "DocumentUploadResult",
    "DocumentUploadStatus",
    "ManualImportContracts",
    "NormalizedRequirement",
    "ProcessCreate",
    "ProcessDetail",
    "ProcessDocumentList",
    "ProcessDocumentMetadata",
    "ProcessList",
    "ProcessSource",
    "ProcessStatus",
    "ProcessSummary",
    "RequirementCategory",
    "RequirementCriticality",
    "RequirementStatus",
    "RequirementSubsanability",
    "SourceLocation",
    "UploadErrorCode",
]
