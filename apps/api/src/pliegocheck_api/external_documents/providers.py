"""Proveedores SECOP I/II respaldados exclusivamente por datasets publicos oficiales."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, ClassVar, Protocol

import httpx

from pliegocheck_api.config import Settings
from pliegocheck_api.external_procurement.providers import get_source_definition
from pliegocheck_api.external_procurement.secop_mapper import map_secop_process
from pliegocheck_api.models import ExternalProcurementProcessLink
from pliegocheck_schemas import (
    ExternalDocumentAddendumStatus,
    ExternalDocumentDiscoveryStatus,
    ExternalDocumentDownloadStatus,
    ExternalProcurementSourceSystem,
)


@dataclass(frozen=True)
class DiscoveredExternalDocument:
    source_document_id: str
    source_document_reference: str | None
    title: str
    document_type: str | None
    document_category: str | None
    source_url: str | None
    source_public_url: str
    published_at: datetime | None
    updated_at_source: datetime | None
    reported_size_bytes: int | None
    reported_content_type: str | None
    discovery_status: ExternalDocumentDiscoveryStatus
    download_status: ExternalDocumentDownloadStatus
    addendum_status: ExternalDocumentAddendumStatus
    requires_human_review: bool


@dataclass(frozen=True)
class ProcessRefresh:
    metadata: dict[str, Any]
    source_updated_at: datetime | None
    documents: tuple[DiscoveredExternalDocument, ...]
    warnings: tuple[dict[str, str], ...] = ()


class ExternalProcessDocumentProvider(Protocol):
    def refresh(
        self, link: ExternalProcurementProcessLink, max_documents: int
    ) -> ProcessRefresh: ...
    def close(self) -> None: ...


class SocrataDocumentProvider:
    PROCESS_DATASETS: ClassVar[dict[str, str]] = {
        "SECOP_II": "p6dx-8zbt",
        "SECOP_I": "f789-7hwg",
    }
    DOCUMENT_DATASETS: ClassVar[dict[str, tuple[str, ...]]] = {
        "SECOP_II": ("dmgg-8hin", "nbae-kzan", "3skv-9na7", "kgcd-kt7i", "f8va-cf4m"),
        "SECOP_I": ("ps88-5e3v", "8kpz-m6cc"),
    }

    def __init__(self, settings: Settings, *, transport: httpx.BaseTransport | None = None) -> None:
        headers = {"User-Agent": "PliegoCheck-SECOP/0.17", "Accept": "application/json"}
        if settings.secop_app_token:
            headers["X-App-Token"] = settings.secop_app_token
        self.client = httpx.Client(
            base_url=settings.secop_base_url,
            timeout=settings.secop_timeout_seconds,
            headers=headers,
            transport=transport,
        )

    def close(self) -> None:
        self.client.close()

    def refresh(self, link: ExternalProcurementProcessLink, max_documents: int) -> ProcessRefresh:
        source = link.source_system
        if source not in self.PROCESS_DATASETS:
            raise ValueError(f"Fuente no soportada: {source}")
        process_field = "id_del_proceso" if source == "SECOP_II" else "numero_de_proceso"
        rows = self._query(self.PROCESS_DATASETS[source], process_field, link.source_process_id, 1)
        raw_metadata = rows[0] if rows else {}
        join_field = "proceso" if source == "SECOP_II" else "numero_de_constancia"
        join_value = (
            raw_metadata.get("id_del_portafolio")
            if source == "SECOP_II"
            else raw_metadata.get("numero_de_constancia")
        )
        warnings: list[dict[str, str]] = []
        if raw_metadata:
            normalized, _safe = map_secop_process(
                raw_metadata,
                get_source_definition(ExternalProcurementSourceSystem(source)),
            )
            metadata = normalized.model_dump(mode="json")
        else:
            metadata = {}
            warnings.append(
                {
                    "code": "EXTERNAL_PROCESS_NOT_FOUND",
                    "message": "La fuente ya no devolvio el proceso importado.",
                }
            )
        if not join_value:
            warnings.append(
                {
                    "code": "EXTERNAL_DOCUMENT_JOIN_UNKNOWN",
                    "message": "La fuente no publico la clave de correlacion documental.",
                }
            )
            return ProcessRefresh(
                metadata=metadata,
                source_updated_at=_source_updated(raw_metadata),
                documents=(),
                warnings=tuple(warnings),
            )
        documents: list[DiscoveredExternalDocument] = []
        for dataset in self.DOCUMENT_DATASETS[source]:
            if len(documents) >= max_documents:
                break
            try:
                doc_rows = self._query(
                    dataset, join_field, str(join_value), max_documents - len(documents)
                )
            except httpx.HTTPError:
                warnings.append(
                    {
                        "code": "EXTERNAL_DOCUMENT_DATASET_UNAVAILABLE",
                        "message": f"No se pudo consultar el dataset publico {dataset}.",
                    }
                )
                continue
            documents.extend(
                _map_secop_ii(row, dataset) if source == "SECOP_II" else _map_secop_i(row, dataset)
                for row in doc_rows
            )
        return ProcessRefresh(
            metadata=metadata,
            source_updated_at=_source_updated(raw_metadata),
            documents=tuple(documents),
            warnings=tuple(warnings),
        )

    def _query(self, dataset: str, field: str, value: str, limit: int) -> list[dict[str, Any]]:
        escaped = value.replace("'", "''")
        response = self.client.get(
            f"/resource/{dataset}.json",
            params={"$limit": str(limit), "$where": f"{field}='{escaped}'"},
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list) or not all(isinstance(row, dict) for row in payload):
            raise httpx.DecodingError("Socrata response is not a row list")
        return [dict(row) for row in payload]


class SecopIIProcessDocumentProvider(SocrataDocumentProvider):
    def refresh(self, link: ExternalProcurementProcessLink, max_documents: int) -> ProcessRefresh:
        if link.source_system != "SECOP_II":
            raise ValueError("El proveedor SECOP II no acepta otra fuente.")
        return super().refresh(link, max_documents)


class SecopIProcessDocumentProvider(SocrataDocumentProvider):
    def refresh(self, link: ExternalProcurementProcessLink, max_documents: int) -> ProcessRefresh:
        if link.source_system != "SECOP_I":
            raise ValueError("El proveedor SECOP I no acepta otra fuente.")
        return super().refresh(link, max_documents)


def provider_for_link(
    settings: Settings, link: ExternalProcurementProcessLink
) -> SocrataDocumentProvider:
    if link.source_system == "SECOP_II":
        return SecopIIProcessDocumentProvider(settings)
    if link.source_system == "SECOP_I":
        return SecopIProcessDocumentProvider(settings)
    raise ValueError(f"Fuente no soportada: {link.source_system}")


def _map_secop_ii(row: dict[str, Any], dataset: str) -> DiscoveredExternalDocument:
    title = str(row.get("nombre_archivo") or row.get("descripci_n") or "Documento SECOP II")[:500]
    url = _url(row.get("url_descarga_documento"))
    document_type = str(row.get("extensi_n") or "").strip().lower() or None
    supported_download = bool(url and document_type in {"pdf", "docx", "xlsx", "txt", "csv"})
    category = str(row.get("descripci_n") or "")[:255] or None
    addendum = _addendum(title, category, explicit_category=False)
    return DiscoveredExternalDocument(
        source_document_id=str(row.get("id_documento") or f"{dataset}:{title}"),
        source_document_reference=str(row.get("n_mero_de_contrato") or "") or None,
        title=title,
        document_type=document_type,
        document_category=category,
        source_url=url,
        source_public_url=f"https://www.datos.gov.co/resource/{dataset}",
        published_at=_dt(row.get("fecha_carga")),
        updated_at_source=_dt(row.get("fecha_carga")),
        reported_size_bytes=_int(row.get("tamanno_archivo")),
        reported_content_type=None,
        discovery_status=(
            ExternalDocumentDiscoveryStatus.DISCOVERED
            if supported_download
            else (
                ExternalDocumentDiscoveryStatus.LINK_AVAILABLE
                if url
                else ExternalDocumentDiscoveryStatus.METADATA_ONLY
            )
        ),
        download_status=ExternalDocumentDownloadStatus.NOT_REQUESTED
        if supported_download
        else ExternalDocumentDownloadStatus.UNSUPPORTED,
        addendum_status=addendum,
        requires_human_review=addendum
        in {
            ExternalDocumentAddendumStatus.POTENTIAL_ADDENDUM,
            ExternalDocumentAddendumStatus.CONFIRMED_ADDENDUM,
        },
    )


def _map_secop_i(row: dict[str, Any], dataset: str) -> DiscoveredExternalDocument:
    title = str(
        row.get("nombrearchivo")
        or row.get("titulo")
        or row.get("descripcion")
        or "Documento SECOP I"
    )[:500]
    url = _url(row.get("ruta_descarga"))
    category = str(row.get("tipo") or row.get("descripcion") or "")[:255] or None
    addendum = _addendum(title, category, explicit_category=True)
    return DiscoveredExternalDocument(
        source_document_id=str(row.get("identificador") or f"{dataset}:{title}"),
        source_document_reference=str(row.get("numero_de_constancia") or "") or None,
        title=title,
        document_type=str(row.get("extension") or "") or None,
        document_category=category,
        source_url=url,
        source_public_url=f"https://www.datos.gov.co/resource/{dataset}",
        published_at=_dt(row.get("fecha_creacion")),
        updated_at_source=_dt(row.get("fecha_ultima_modificacion")),
        reported_size_bytes=_int(row.get("tama_o")),
        reported_content_type=None,
        discovery_status=ExternalDocumentDiscoveryStatus.LINK_AVAILABLE
        if url
        else ExternalDocumentDiscoveryStatus.METADATA_ONLY,
        download_status=ExternalDocumentDownloadStatus.UNSUPPORTED,
        addendum_status=addendum,
        requires_human_review=addendum
        in {
            ExternalDocumentAddendumStatus.POTENTIAL_ADDENDUM,
            ExternalDocumentAddendumStatus.CONFIRMED_ADDENDUM,
        },
    )


def _addendum(*values: str | None, explicit_category: bool) -> ExternalDocumentAddendumStatus:
    text = " ".join(value or "" for value in values).casefold()
    has_term = any(term in text for term in ("adenda", "adendo", "modificaci", "aclaraci"))
    if explicit_category and has_term:
        return ExternalDocumentAddendumStatus.CONFIRMED_ADDENDUM
    if has_term:
        return ExternalDocumentAddendumStatus.POTENTIAL_ADDENDUM
    return ExternalDocumentAddendumStatus.NOT_ADDENDUM


def _url(value: Any) -> str | None:
    if isinstance(value, dict):
        value = value.get("url")
    return str(value).strip() if value else None


def _dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return result.replace(tzinfo=UTC) if result.tzinfo is None else result
    except ValueError:
        return None


def _source_updated(metadata: dict[str, Any]) -> datetime | None:
    for field in ("fecha_de_ultima_publicaci", "ultima_actualizacion", "fecha_de_publicacion_del"):
        value = _dt(metadata.get(field))
        if value:
            return value
    return None


def _int(value: Any) -> int | None:
    try:
        return int(float(str(value))) if value not in (None, "") else None
    except ValueError:
        return None
