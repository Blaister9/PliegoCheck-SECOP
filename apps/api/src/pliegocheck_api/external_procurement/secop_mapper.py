"""Normalizacion conservadora de filas SECOP I/II."""

import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from typing import Any
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from pliegocheck_api.external_procurement.errors import ExternalProviderError
from pliegocheck_api.external_procurement.providers import SourceDefinition
from pliegocheck_schemas import (
    ExternalProcurementDocumentStatus,
    ExternalProcurementErrorCode,
    ExternalProcurementFieldStatus,
    ExternalProcurementWarning,
    SecopProcessNormalized,
)

BOGOTA = ZoneInfo("America/Bogota")
OFFICIAL_PROCESS_HOSTS = {
    "community.secop.gov.co",
    "contratos.gov.co",
    "www.contratos.gov.co",
}


def sanitize_payload(payload: dict[str, Any], definition: SourceDefinition) -> dict[str, Any]:
    """Retiene solo campos de proceso necesarios; excluye datos personales del adjudicatario."""
    return {
        key: _url_value(payload[key])
        for key in definition.safe_fields
        if key in payload and payload[key] is not None
    }


def map_secop_process(
    payload: dict[str, Any], definition: SourceDefinition
) -> tuple[SecopProcessNormalized, dict[str, Any]]:
    safe_payload = sanitize_payload(payload, definition)
    fields = definition.field_map
    process_id = _text(safe_payload.get(fields["source_process_id"]), 500)
    title = _text(safe_payload.get(fields["title"]), 500)
    entity = _text(safe_payload.get(fields["entity_name"]), 500)
    if not process_id or not title or not entity:
        raise ExternalProviderError(
            ExternalProcurementErrorCode.SOURCE_INVALID_RESPONSE,
            "La fuente devolvio una fila sin identificador, titulo o entidad.",
        )

    statuses: dict[str, ExternalProcurementFieldStatus] = {}
    warnings: list[ExternalProcurementWarning] = []

    def read(name: str, limit: int = 500) -> str | None:
        field = fields.get(name)
        value = _text(safe_payload.get(field), limit) if field else None
        statuses[name] = (
            ExternalProcurementFieldStatus.PRESENT
            if value is not None
            else ExternalProcurementFieldStatus.MISSING
        )
        if value is None:
            warnings.append(
                ExternalProcurementWarning(
                    code="MISSING_FIELD",
                    message=f"La fuente no informo {name}.",
                    field=name,
                )
            )
        return value

    reference = read("reference")
    description = read("description", 5000)
    entity_nit = read("entity_nit", 100)
    modality = read("modality")
    status = read("status")
    department = read("department", 300)
    municipality = read("municipality", 300)
    source_url = _official_process_url(safe_payload.get(fields.get("source_url", "")))
    statuses["source_url"] = (
        ExternalProcurementFieldStatus.NORMALIZED
        if source_url
        else ExternalProcurementFieldStatus.MISSING
    )
    estimated_value = _decimal(safe_payload.get(fields.get("estimated_value", "")))
    statuses["estimated_value"] = (
        ExternalProcurementFieldStatus.NORMALIZED
        if estimated_value is not None
        else ExternalProcurementFieldStatus.MISSING
    )
    publication_date = _datetime(safe_payload.get(fields.get("publication_date", "")))
    closing_date = _datetime(safe_payload.get(fields.get("closing_date", "")))
    statuses["publication_date"] = _date_status(publication_date)
    statuses["closing_date"] = _date_status(closing_date)
    if closing_date is None:
        warnings.append(
            ExternalProcurementWarning(
                code="MISSING_FIELD",
                message="La fuente no informo closing_date.",
                field="closing_date",
            )
        )
    currency = _currency(
        safe_payload.get(fields.get("currency", "")),
        default=definition.default_currency,
    )
    statuses["currency"] = (
        ExternalProcurementFieldStatus.NORMALIZED
        if currency is not None
        else ExternalProcurementFieldStatus.MISSING
    )
    if currency is None:
        warnings.append(
            ExternalProcurementWarning(
                code="UNKNOWN_CURRENCY",
                message="La fuente no informo una moneda ISO reconocida.",
                field="currency",
            )
        )
    raw_source_url = _text(_url_value(safe_payload.get(fields.get("source_url", ""))), 2083)
    if raw_source_url and source_url is None:
        warnings.append(
            ExternalProcurementWarning(
                code="UNTRUSTED_SOURCE_URL",
                message="El enlace externo no pertenece a un host oficial permitido.",
                field="source_url",
            )
        )
    canonical = json.dumps(safe_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    raw_hash = sha256(canonical.encode("utf-8")).hexdigest()
    documents_status = (
        ExternalProcurementDocumentStatus.DOCUMENT_DOWNLOAD_UNSUPPORTED
        if source_url
        else ExternalProcurementDocumentStatus.DOCUMENTS_NOT_AVAILABLE
    )
    normalized = SecopProcessNormalized(
        source_system=definition.source_system,
        source_dataset=definition.dataset_id,
        source_process_id=process_id,
        reference=reference,
        title=title,
        description=description,
        entity_name=entity,
        entity_nit=entity_nit,
        modality=modality,
        status=status,
        estimated_value=estimated_value,
        currency=currency,
        publication_date=publication_date,
        closing_date=closing_date,
        department=department,
        municipality=municipality,
        source_url=source_url,
        documents_url=source_url,
        documents_status=documents_status,
        raw_payload_hash=raw_hash,
        field_statuses=statuses,
        warnings=warnings,
    )
    return normalized, safe_payload


def _url_value(value: Any) -> Any:
    if isinstance(value, dict):
        return value.get("url")
    return value


def _text(value: Any, limit: int) -> str | None:
    if value is None:
        return None
    normalized = " ".join(str(value).split()).strip()
    return normalized[:limit] if normalized else None


def _decimal(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.replace(tzinfo=BOGOTA) if parsed.tzinfo is None else parsed


def _date_status(value: datetime | None) -> ExternalProcurementFieldStatus:
    return (
        ExternalProcurementFieldStatus.NORMALIZED
        if value is not None
        else ExternalProcurementFieldStatus.MISSING
    )


def _currency(value: Any, *, default: str | None) -> str | None:
    normalized = _text(value, 100)
    if normalized is None:
        return default
    if normalized.lower() in {"peso colombiano", "pesos colombianos", "cop"}:
        return "COP"
    candidate = normalized.upper()
    return (
        candidate if len(candidate) == 3 and candidate.isascii() and candidate.isalpha() else None
    )


def _official_process_url(value: Any) -> str | None:
    normalized = _text(_url_value(value), 2083)
    if normalized is None:
        return None
    parsed = urlsplit(normalized)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in OFFICIAL_PROCESS_HOSTS
        or parsed.port not in {None, 443}
        or parsed.username is not None
        or parsed.password is not None
    ):
        return None
    return normalized
