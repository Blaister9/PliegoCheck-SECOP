"""Catalogo cerrado de datasets oficiales verificados."""

from dataclasses import dataclass

from pliegocheck_schemas import ExternalProcurementSourceSystem


@dataclass(frozen=True)
class SourceDefinition:
    source_system: ExternalProcurementSourceSystem
    name: str
    dataset_id: str
    human_path: str
    api_path: str
    field_map: dict[str, str]
    safe_fields: tuple[str, ...]
    unsupported_filters: frozenset[str]
    default_currency: str | None
    metadata: dict[str, object]


SECOP_II_FIELDS = {
    "source_process_id": "id_del_proceso",
    "reference": "referencia_del_proceso",
    "title": "nombre_del_procedimiento",
    "description": "descripci_n_del_procedimiento",
    "entity_name": "entidad",
    "entity_nit": "nit_entidad",
    "modality": "modalidad_de_contratacion",
    "status": "estado_del_procedimiento",
    "estimated_value": "precio_base",
    "publication_date": "fecha_de_publicacion_del",
    "closing_date": "fecha_de_recepcion_de",
    "department": "departamento_entidad",
    "municipality": "ciudad_entidad",
    "source_url": "urlproceso",
}
SECOP_I_FIELDS = {
    # ``uid`` identifies a process-award relation and can repeat one process.
    # ``numero_de_proceso`` is the stable process identity used for import deduplication.
    "source_process_id": "numero_de_proceso",
    "reference": "numero_de_proceso",
    "title": "detalle_del_objeto_a_contratar",
    "description": "objeto_a_contratar",
    "entity_name": "nombre_entidad",
    "entity_nit": "nit_de_la_entidad",
    "modality": "modalidad_de_contratacion",
    "status": "estado_del_proceso",
    "estimated_value": "cuantia_proceso",
    "publication_date": "fecha_de_cargue_en_el_secop",
    "department": "departamento_entidad",
    "municipality": "municipio_entidad",
    "source_url": "ruta_proceso_en_secop_i",
    "currency": "moneda",
}


def _safe_fields(field_map: dict[str, str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(field_map.values()))


SOURCE_DEFINITIONS = {
    ExternalProcurementSourceSystem.SECOP_II: SourceDefinition(
        source_system=ExternalProcurementSourceSystem.SECOP_II,
        name="SECOP II - Procesos de Contratacion",
        dataset_id="p6dx-8zbt",
        human_path="/Estad-sticas-Nacionales/SECOP-II-Procesos-de-Contrataci-n/p6dx-8zbt",
        api_path="/resource/p6dx-8zbt.json",
        field_map=SECOP_II_FIELDS,
        safe_fields=_safe_fields(SECOP_II_FIELDS),
        unsupported_filters=frozenset(),
        # El dataset no publica una columna de moneda. No inferimos COP a partir
        # del contexto del sistema ni del valor numérico.
        default_currency=None,
        metadata={
            "owner": "Datos Abiertos CCE",
            "frequency": "daily",
            "verified_on": "2026-07-13",
            "column_count": 59,
        },
    ),
    ExternalProcurementSourceSystem.SECOP_I: SourceDefinition(
        source_system=ExternalProcurementSourceSystem.SECOP_I,
        name="SECOP I - Procesos de Compra Publica",
        dataset_id="f789-7hwg",
        human_path="/Estad-sticas-Nacionales/SECOP-I-Procesos-de-Compra-P-blica/f789-7hwg",
        api_path="/resource/f789-7hwg.json",
        field_map=SECOP_I_FIELDS,
        safe_fields=_safe_fields(SECOP_I_FIELDS),
        unsupported_filters=frozenset({"closing_from", "closing_to"}),
        default_currency=None,
        metadata={
            "owner": "Datos Abiertos CCE",
            "frequency": "daily",
            "verified_on": "2026-07-13",
            "column_count": 79,
        },
    ),
}


def get_source_definition(source_system: ExternalProcurementSourceSystem) -> SourceDefinition:
    return SOURCE_DEFINITIONS[source_system]
