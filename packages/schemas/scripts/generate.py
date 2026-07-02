"""Genera los artefactos derivados del contrato canonico Pydantic.

Produce, de forma deterministica (sin fechas, rutas locales ni contenido variable):

- ``generated/normalized-requirement.schema.json``: JSON Schema del contrato.
- ``generated/normalized-requirement.enums.ts``: constantes TypeScript de los
  vocabularios cerrados, para consumo en runtime desde el frontend.

El tipo TypeScript de la interfaz se genera aparte desde el JSON Schema
(``scripts/generate-ts.mjs``). Este script falla con codigo distinto de cero
si la generacion no puede completarse.
"""

import json
import sys
from enum import StrEnum
from pathlib import Path

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
    "// No editar a mano: la definicion canonica es el modelo Pydantic\n"
    "// packages/schemas/src/pliegocheck_schemas/normalized_requirement.py.\n"
)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)


def generate_json_schema() -> None:
    schema = NormalizedRequirement.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    content = json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    write_text(GENERATED_DIR / "normalized-requirement.schema.json", content)


def ts_const_block(const_name: str, type_name: str, enum_cls: type[StrEnum]) -> str:
    values = ", ".join(f'"{member.value}"' for member in enum_cls)
    return (
        f"export const {const_name} = [{values}] as const;\n"
        f"export type {type_name} = (typeof {const_name})[number];\n"
    )


def generate_enums_ts() -> None:
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


def main() -> int:
    try:
        generate_json_schema()
        generate_enums_ts()
    except Exception as exc:  # el fallo debe ser visible y con codigo distinto de cero
        print(f"ERROR generando contratos: {exc}", file=sys.stderr)
        return 1
    print("Contratos generados en packages/schemas/generated/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
