"""Genera los artefactos derivados de los contratos canonicos Pydantic.

Produce, de forma deterministica (sin fechas, rutas locales ni contenido variable):

- ``generated/<contrato>.schema.json``: JSON Schema de cada contrato.
- ``generated/<contrato>.enums.ts``: constantes TypeScript de los vocabularios
  cerrados, para consumo en runtime desde el frontend.

Los tipos TypeScript de las interfaces se generan aparte desde los JSON Schema
(``scripts/generate-ts.mjs``). Este script falla con codigo distinto de cero
si la generacion no puede completarse.
"""

import json
import sys
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel

from pliegocheck_schemas.document_extraction import (
    DOCUMENT_EXTRACTION_SCHEMA_VERSION,
    DocumentExtractionContracts,
    DocumentExtractionStatus,
    DocumentProcessingJobStatus,
    DocumentProcessingJobType,
    DocumentProcessingStatus,
    ExtractedSegmentType,
    ExtractionErrorCode,
)
from pliegocheck_schemas.manual_import import (
    MANUAL_IMPORT_SCHEMA_VERSION,
    DocumentType,
    DocumentUploadStatus,
    ManualImportContracts,
    ProcessSource,
    ProcessStatus,
    UploadErrorCode,
)
from pliegocheck_schemas.normalized_requirement import (
    NORMALIZED_REQUIREMENT_SCHEMA_VERSION,
    NormalizedRequirement,
    RequirementCategory,
    RequirementCriticality,
    RequirementStatus,
    RequirementSubsanability,
)

GENERATED_DIR = Path(__file__).resolve().parent.parent / "generated"

TS_HEADER = (
    "// Archivo generado automaticamente por packages/schemas/scripts/generate.py.\n"
    "// No editar a mano: la definicion canonica son los modelos Pydantic de\n"
    "// packages/schemas/src/pliegocheck_schemas/.\n"
)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)


def strip_property_titles(node: object) -> None:
    """Elimina ``title`` recursivamente.

    Los nombres de los tipos TypeScript provienen de las claves de ``$defs``;
    los ``title`` por propiedad solo generan aliases ruidosos y colisiones.
    """
    if isinstance(node, dict):
        node.pop("title", None)
        for key, value in node.items():
            if key == "properties" and isinstance(value, dict):
                for property_schema in value.values():
                    strip_property_titles(property_schema)
                continue
            strip_property_titles(value)
    elif isinstance(node, list):
        for item in node:
            strip_property_titles(item)


def generate_json_schema(model: type[BaseModel], filename: str) -> None:
    schema = model.model_json_schema()
    strip_property_titles(schema)
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    content = json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    write_text(GENERATED_DIR / filename, content)


def ts_const_block(const_name: str, type_name: str, enum_cls: type[StrEnum]) -> str:
    values = ", ".join(f'"{member.value}"' for member in enum_cls)
    return (
        f"export const {const_name} = [{values}] as const;\n"
        f"export type {type_name} = (typeof {const_name})[number];\n"
    )


def generate_requirement_enums_ts() -> None:
    blocks = [
        TS_HEADER,
        "export const NORMALIZED_REQUIREMENT_SCHEMA_VERSION = "
        f'"{NORMALIZED_REQUIREMENT_SCHEMA_VERSION}";\n',
        ts_const_block(
            "REQUIREMENT_CATEGORY_VALUES", "RequirementCategoryValue", RequirementCategory
        ),
        ts_const_block("REQUIREMENT_STATUS_VALUES", "RequirementStatusValue", RequirementStatus),
        ts_const_block(
            "REQUIREMENT_CRITICALITY_VALUES", "RequirementCriticalityValue", RequirementCriticality
        ),
        ts_const_block(
            "REQUIREMENT_SUBSANABILITY_VALUES",
            "RequirementSubsanabilityValue",
            RequirementSubsanability,
        ),
    ]
    write_text(GENERATED_DIR / "normalized-requirement.enums.ts", "\n".join(blocks))


def generate_manual_import_enums_ts() -> None:
    blocks = [
        TS_HEADER,
        f'export const MANUAL_IMPORT_SCHEMA_VERSION = "{MANUAL_IMPORT_SCHEMA_VERSION}";\n',
        ts_const_block("PROCESS_SOURCE_VALUES", "ProcessSourceValue", ProcessSource),
        ts_const_block("PROCESS_STATUS_VALUES", "ProcessStatusValue", ProcessStatus),
        ts_const_block("DOCUMENT_TYPE_VALUES", "DocumentTypeValue", DocumentType),
        ts_const_block(
            "DOCUMENT_UPLOAD_STATUS_VALUES", "DocumentUploadStatusValue", DocumentUploadStatus
        ),
        ts_const_block("UPLOAD_ERROR_CODE_VALUES", "UploadErrorCodeValue", UploadErrorCode),
    ]
    write_text(GENERATED_DIR / "manual-import.enums.ts", "\n".join(blocks))


def generate_document_extraction_enums_ts() -> None:
    blocks = [
        TS_HEADER,
        "export const DOCUMENT_EXTRACTION_SCHEMA_VERSION = "
        f'"{DOCUMENT_EXTRACTION_SCHEMA_VERSION}";\n',
        ts_const_block(
            "DOCUMENT_PROCESSING_STATUS_VALUES",
            "DocumentProcessingStatusValue",
            DocumentProcessingStatus,
        ),
        ts_const_block(
            "DOCUMENT_PROCESSING_JOB_STATUS_VALUES",
            "DocumentProcessingJobStatusValue",
            DocumentProcessingJobStatus,
        ),
        ts_const_block(
            "DOCUMENT_PROCESSING_JOB_TYPE_VALUES",
            "DocumentProcessingJobTypeValue",
            DocumentProcessingJobType,
        ),
        ts_const_block(
            "DOCUMENT_EXTRACTION_STATUS_VALUES",
            "DocumentExtractionStatusValue",
            DocumentExtractionStatus,
        ),
        ts_const_block(
            "EXTRACTED_SEGMENT_TYPE_VALUES",
            "ExtractedSegmentTypeValue",
            ExtractedSegmentType,
        ),
        ts_const_block(
            "EXTRACTION_ERROR_CODE_VALUES",
            "ExtractionErrorCodeValue",
            ExtractionErrorCode,
        ),
    ]
    write_text(GENERATED_DIR / "document-extraction.enums.ts", "\n".join(blocks))


def main() -> int:
    try:
        generate_json_schema(NormalizedRequirement, "normalized-requirement.schema.json")
        generate_json_schema(ManualImportContracts, "manual-import.schema.json")
        generate_json_schema(DocumentExtractionContracts, "document-extraction.schema.json")
        generate_requirement_enums_ts()
        generate_manual_import_enums_ts()
        generate_document_extraction_enums_ts()
    except Exception as exc:  # el fallo debe ser visible y con codigo distinto de cero
        print(f"ERROR generando contratos: {exc}", file=sys.stderr)
        return 1
    print("Contratos generados en packages/schemas/generated/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
