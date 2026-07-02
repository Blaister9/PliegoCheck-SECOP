"""Catalogo de contratos compartidos disponibles en la plataforma.

Consume el paquete compartido ``pliegocheck-schemas``: la version publicada
proviene del modelo canonico, no de una constante duplicada.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from pliegocheck_schemas import (
    MANUAL_IMPORT_SCHEMA_VERSION,
    NORMALIZED_REQUIREMENT_SCHEMA_VERSION,
    ManualImportContracts,
    NormalizedRequirement,
)

router = APIRouter(prefix="/contracts", tags=["contracts"])


class ContractInfo(BaseModel):
    """Metadatos de un contrato compartido."""

    name: str
    schema_version: str
    title: str


class ContractsResponse(BaseModel):
    """Catalogo de contratos compartidos."""

    contracts: list[ContractInfo]


@router.get("", summary="Lista los contratos compartidos y sus versiones")
def list_contracts() -> ContractsResponse:
    return ContractsResponse(
        contracts=[
            ContractInfo(
                name="normalized_requirement",
                schema_version=NORMALIZED_REQUIREMENT_SCHEMA_VERSION,
                title=NormalizedRequirement.__name__,
            ),
            ContractInfo(
                name="manual_import",
                schema_version=MANUAL_IMPORT_SCHEMA_VERSION,
                title=ManualImportContracts.__name__,
            ),
        ]
    )
