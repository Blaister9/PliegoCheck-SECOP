"""Cliente HTTP respetuoso para la API Socrata de Datos Abiertos Colombia."""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta
from threading import Lock
from time import monotonic
from typing import Any, ClassVar

import httpx

from pliegocheck_api.config import Settings
from pliegocheck_api.external_procurement.errors import ExternalProviderError
from pliegocheck_api.external_procurement.providers import SourceDefinition
from pliegocheck_schemas import ExternalProcurementErrorCode, ExternalProcurementSearchRequest


class DatosAbiertosClient:
    _requests: ClassVar[dict[str, deque[float]]] = defaultdict(deque)
    _rate_lock: ClassVar[Lock] = Lock()
    _cache: ClassVar[dict[str, tuple[datetime, list[dict[str, Any]]]]] = {}
    _cache_lock: ClassVar[Lock] = Lock()

    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.settings = settings
        headers = {
            "User-Agent": "PliegoCheck-SECOP/0.16 (public procurement search; respectful client)",
            "Accept": "application/json",
        }
        if settings.secop_app_token:
            headers["X-App-Token"] = settings.secop_app_token
        self.client = httpx.Client(
            base_url=settings.secop_base_url,
            headers=headers,
            timeout=settings.secop_timeout_seconds,
            transport=transport,
        )

    def close(self) -> None:
        self.client.close()

    def search(
        self,
        definition: SourceDefinition,
        request: ExternalProcurementSearchRequest,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        params, unsupported = build_query_params(definition, request)
        cache_key = f"{definition.dataset_id}:{sorted(params.items())}"
        cached = self._cached(cache_key)
        if cached is not None:
            return cached, unsupported
        self._check_rate_limit()
        for attempt in range(3):
            try:
                response = self.client.get(definition.api_path, params=params)
                if response.status_code == 429:
                    raise ExternalProviderError(
                        ExternalProcurementErrorCode.RATE_LIMITED,
                        "La fuente publica limito temporalmente las consultas.",
                    )
                if response.status_code >= 500 and attempt < 2:
                    continue
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, list) or not all(
                    isinstance(row, dict) for row in payload
                ):
                    raise ExternalProviderError(
                        ExternalProcurementErrorCode.SOURCE_INVALID_RESPONSE,
                        "La fuente publica devolvio un formato inesperado.",
                    )
                rows = [dict(row) for row in payload]
                self._store_cache(cache_key, rows)
                return rows, unsupported
            except httpx.TimeoutException as exc:
                if attempt < 2:
                    continue
                raise ExternalProviderError(
                    ExternalProcurementErrorCode.SOURCE_TIMEOUT,
                    "La fuente publica no respondio dentro del tiempo configurado.",
                ) from exc
            except ExternalProviderError:
                raise
            except (httpx.HTTPError, ValueError) as exc:
                if attempt < 2:
                    continue
                raise ExternalProviderError(
                    ExternalProcurementErrorCode.SOURCE_UNAVAILABLE,
                    "No fue posible consultar la fuente publica en este momento.",
                ) from exc
        raise AssertionError("unreachable")

    def _check_rate_limit(self) -> None:
        now = monotonic()
        key = self.settings.secop_base_url
        with self._rate_lock:
            requests = self._requests[key]
            while requests and now - requests[0] >= 60:
                requests.popleft()
            if len(requests) >= self.settings.secop_rate_limit_per_minute:
                raise ExternalProviderError(
                    ExternalProcurementErrorCode.RATE_LIMITED,
                    "Se alcanzo el limite local de consultas por minuto.",
                )
            requests.append(now)

    def _cached(self, key: str) -> list[dict[str, Any]] | None:
        if self.settings.secop_cache_ttl_minutes <= 0:
            return None
        with self._cache_lock:
            item = self._cache.get(key)
            if item is None:
                return None
            created_at, rows = item
            if datetime.now(UTC) - created_at > timedelta(
                minutes=self.settings.secop_cache_ttl_minutes
            ):
                self._cache.pop(key, None)
                return None
            return [dict(row) for row in rows]

    def _store_cache(self, key: str, rows: list[dict[str, Any]]) -> None:
        if self.settings.secop_cache_ttl_minutes <= 0:
            return
        with self._cache_lock:
            self._cache[key] = (datetime.now(UTC), [dict(row) for row in rows])


def build_query_params(
    definition: SourceDefinition,
    request: ExternalProcurementSearchRequest,
) -> tuple[dict[str, str], list[str]]:
    fields = definition.field_map
    params = {
        "$limit": str(request.limit),
        "$offset": str(request.offset),
        "$select": ",".join(definition.safe_fields),
        "$order": f"{fields['publication_date']} DESC",
    }
    if request.query:
        params["$q"] = request.query.strip()
    clauses: list[str] = []
    text_filters = {
        "entity_name": request.entity_name,
        "modality": request.modality,
        "status": request.status,
        "department": request.department,
        "municipality": request.municipality,
        "reference": request.process_code,
    }
    for canonical, value in text_filters.items():
        if value and canonical in fields:
            clauses.append(_contains(fields[canonical], value))
    if request.min_value is not None:
        clauses.append(f"{fields['estimated_value']} >= {request.min_value}")
    if request.max_value is not None:
        clauses.append(f"{fields['estimated_value']} <= {request.max_value}")
    _date_clause(clauses, fields["publication_date"], ">=", request.published_from)
    _date_clause(clauses, fields["publication_date"], "<=", request.published_to)
    unsupported = [
        name
        for name in sorted(definition.unsupported_filters)
        if getattr(request, name) is not None
    ]
    if "closing_date" in fields:
        _date_clause(clauses, fields["closing_date"], ">=", request.closing_from)
        _date_clause(clauses, fields["closing_date"], "<=", request.closing_to)
    if clauses:
        params["$where"] = " AND ".join(clauses)
    return params, unsupported


def _contains(field: str, value: str) -> str:
    escaped = value.strip().lower().replace("'", "''").replace("%", "\\%")
    return f"lower({field}) like '%{escaped}%'"


def _date_clause(clauses: list[str], field: str, operator: str, value: datetime | None) -> None:
    if value is not None:
        clauses.append(f"{field} {operator} '{value.isoformat()}'")
