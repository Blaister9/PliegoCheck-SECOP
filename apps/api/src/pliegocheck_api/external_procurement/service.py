"""Persistencia, trazabilidad e importacion idempotente de procesos externos."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from http import HTTPStatus
from typing import Any
from uuid import UUID, uuid4

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from pliegocheck_api.auth import CurrentUser, audit_event
from pliegocheck_api.config import Settings
from pliegocheck_api.errors import DomainError
from pliegocheck_api.external_procurement.datos_abiertos import DatosAbiertosClient
from pliegocheck_api.external_procurement.errors import ExternalProviderError
from pliegocheck_api.external_procurement.providers import (
    SOURCE_DEFINITIONS,
    get_source_definition,
)
from pliegocheck_api.external_procurement.secop_mapper import map_secop_process
from pliegocheck_api.models import (
    ExternalProcurementImport,
    ExternalProcurementProcessLink,
    ExternalProcurementSearch,
    ExternalProcurementSource,
    ImportEvent,
    Process,
)
from pliegocheck_api.models import (
    ExternalProcurementSearchResult as SearchResultModel,
)
from pliegocheck_schemas import (
    ExternalProcurementDocumentStatus,
    ExternalProcurementErrorCode,
    ExternalProcurementFieldStatus,
    ExternalProcurementImportResponse,
    ExternalProcurementImportStatus,
    ExternalProcurementProvider,
    ExternalProcurementSearchRequest,
    ExternalProcurementSearchResponse,
    ExternalProcurementSearchResult,
    ExternalProcurementSearchStatus,
    ExternalProcurementSearchSummary,
    ExternalProcurementSourceStatus,
    ExternalProcurementSourceSummary,
    ExternalProcurementSourceSystem,
    ExternalProcurementWarning,
    OperationalAuditEventType,
    ProcessSource,
    ProcessStatus,
)
from pliegocheck_schemas import (
    ExternalProcurementProcessLink as ProcessLinkContract,
)


def ensure_source_catalog(session: Session, settings: Settings) -> list[ExternalProcurementSource]:
    sources: list[ExternalProcurementSource] = []
    for definition in SOURCE_DEFINITIONS.values():
        source = session.scalar(
            select(ExternalProcurementSource).where(
                ExternalProcurementSource.source_system == definition.source_system.value,
                ExternalProcurementSource.dataset_id == definition.dataset_id,
            )
        )
        desired_status = (
            ExternalProcurementSourceStatus.AVAILABLE.value
            if settings.secop_enabled
            else ExternalProcurementSourceStatus.UNSUPPORTED.value
        )
        if source is None:
            source = ExternalProcurementSource(
                id=uuid4(),
                source_system=definition.source_system.value,
                provider=settings.secop_provider,
                name=definition.name,
                base_url=settings.secop_base_url,
                dataset_id=definition.dataset_id,
                human_url=f"{settings.secop_base_url}{definition.human_path}",
                api_url=f"{settings.secop_base_url}{definition.api_path}",
                status=desired_status,
                source_metadata=definition.metadata,
            )
            session.add(source)
        else:
            source.base_url = settings.secop_base_url
            source.human_url = f"{settings.secop_base_url}{definition.human_path}"
            source.api_url = f"{settings.secop_base_url}{definition.api_path}"
            source.status = desired_status
            source.source_metadata = definition.metadata
        sources.append(source)
    session.commit()
    for source in sources:
        session.refresh(source)
    return sources


def source_to_contract(
    source: ExternalProcurementSource, settings: Settings
) -> ExternalProcurementSourceSummary:
    return ExternalProcurementSourceSummary(
        id=source.id,
        source_system=ExternalProcurementSourceSystem(source.source_system),
        provider=ExternalProcurementProvider(source.provider),
        name=source.name,
        base_url=source.base_url,
        dataset_id=source.dataset_id,
        human_url=source.human_url,
        api_url=source.api_url,
        status=ExternalProcurementSourceStatus(source.status),
        enabled=settings.secop_enabled,
        last_checked_at=source.last_checked_at,
        metadata=source.source_metadata,
        created_at=source.created_at,
        updated_at=source.updated_at,
    )


def run_search(
    session: Session,
    settings: Settings,
    payload: ExternalProcurementSearchRequest,
    *,
    actor: CurrentUser | None = None,
    request: Request | None = None,
    client: DatosAbiertosClient | None = None,
) -> ExternalProcurementSearchResponse:
    if not settings.secop_enabled:
        raise DomainError(
            ExternalProcurementErrorCode.SOURCE_DISABLED,
            "El conector SECOP esta deshabilitado por configuracion.",
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
        )
    sources = ensure_source_catalog(session, settings)
    source = next(item for item in sources if item.source_system == payload.source_system.value)
    definition = get_source_definition(payload.source_system)
    effective_payload = payload
    search_warnings: list[dict[str, str | None]] = []
    if payload.limit > settings.secop_max_page_size:
        effective_payload = payload.model_copy(update={"limit": settings.secop_max_page_size})
        search_warnings.append(
            {
                "code": "MAX_PAGE_SIZE_APPLIED",
                "message": "El limite solicitado se redujo al maximo configurado.",
                "field": "limit",
            }
        )
    filters = effective_payload.model_dump(
        mode="json",
        exclude={"source_system", "query", "limit", "offset"},
        exclude_none=True,
    )
    search = ExternalProcurementSearch(
        id=uuid4(),
        source_id=source.id,
        query=effective_payload.query,
        filters=filters,
        status=ExternalProcurementSearchStatus.RUNNING.value,
        result_count=0,
        source_row_count=0,
        page_count=0,
        limit=effective_payload.limit,
        offset=effective_payload.offset,
        unsupported_filters=[],
        warnings=search_warnings,
        started_at=datetime.now(UTC),
        created_by=actor.id if actor else None,
    )
    session.add(search)
    session.commit()
    session.refresh(search)
    owns_client = client is None
    external_client = client or DatosAbiertosClient(settings)
    try:
        rows, unsupported = external_client.search(definition, effective_payload)
        search.unsupported_filters = unsupported
        for name in unsupported:
            search_warnings.append(
                {
                    "code": ExternalProcurementErrorCode.UNSUPPORTED_FILTER.value,
                    "message": f"La fuente no publica el campo requerido por {name}.",
                    "field": name,
                }
            )
        results: list[SearchResultModel] = []
        seen_processes: set[tuple[str, str, str]] = set()
        for row in rows:
            try:
                normalized, safe_payload = map_secop_process(row, definition)
            except ExternalProviderError:
                search_warnings.append(
                    {
                        "code": "ROW_SKIPPED_INVALID",
                        "message": "Una fila sin campos criticos fue omitida.",
                        "field": None,
                    }
                )
                continue
            source_key = (
                normalized.source_system.value,
                normalized.source_dataset,
                normalized.source_process_id,
            )
            if source_key in seen_processes:
                search_warnings.append(
                    {
                        "code": "DUPLICATE_SOURCE_PROCESS_SKIPPED",
                        "message": "Una fila repetida del mismo proceso fue omitida.",
                        "field": "source_process_id",
                    }
                )
                continue
            seen_processes.add(source_key)
            result = _new_result(search, source, normalized.model_dump(mode="json"), safe_payload)
            session.add(result)
            results.append(result)
        search.result_count = len(results)
        search.source_row_count = len(rows)
        search.page_count = 1 if rows else 0
        search.warnings = search_warnings
        search.status = (
            ExternalProcurementSearchStatus.COMPLETED_WITH_WARNINGS.value
            if search_warnings
            else ExternalProcurementSearchStatus.COMPLETED.value
        )
        search.finished_at = datetime.now(UTC)
        source.status = ExternalProcurementSourceStatus.AVAILABLE.value
        source.last_checked_at = search.finished_at
        audit_event(
            session,
            event_type=OperationalAuditEventType.EXTERNAL_SEARCH_COMPLETED,
            action="external.search",
            status="SUCCESS",
            actor=actor,
            request=request,
            entity_type="external_procurement_search",
            entity_id=search.id,
            metadata={"source": source.source_system, "result_count": len(results)},
        )
        session.commit()
        session.refresh(search)
        for result in results:
            session.refresh(result)
        return ExternalProcurementSearchResponse(
            search=search_to_contract(search, source),
            items=[result_to_contract(session, result) for result in results],
        )
    except ExternalProviderError as exc:
        search.status = ExternalProcurementSearchStatus.FAILED.value
        search.error_code = exc.code.value
        search.error_message = exc.message
        search.finished_at = datetime.now(UTC)
        source.status = ExternalProcurementSourceStatus.ERROR.value
        source.last_checked_at = search.finished_at
        audit_event(
            session,
            event_type=OperationalAuditEventType.EXTERNAL_SEARCH_FAILED,
            action="external.search",
            status="FAILED",
            actor=actor,
            request=request,
            entity_type="external_procurement_search",
            entity_id=search.id,
            metadata={"source": source.source_system, "error_code": exc.code.value},
        )
        session.commit()
        raise DomainError(
            exc.code,
            exc.message,
            status_code=HTTPStatus.BAD_GATEWAY,
            details={"search_id": str(search.id)},
        ) from exc
    finally:
        if owns_client:
            external_client.close()


def search_to_contract(
    search: ExternalProcurementSearch, source: ExternalProcurementSource
) -> ExternalProcurementSearchSummary:
    return ExternalProcurementSearchSummary(
        id=search.id,
        source_id=search.source_id,
        source_system=ExternalProcurementSourceSystem(source.source_system),
        query=search.query,
        filters=search.filters,
        status=ExternalProcurementSearchStatus(search.status),
        result_count=search.result_count,
        source_row_count=search.source_row_count,
        page_count=search.page_count,
        limit=search.limit,
        offset=search.offset,
        unsupported_filters=search.unsupported_filters,
        warnings=[ExternalProcurementWarning.model_validate(item) for item in search.warnings],
        started_at=search.started_at,
        finished_at=search.finished_at,
        error_code=(ExternalProcurementErrorCode(search.error_code) if search.error_code else None),
        error_message=search.error_message,
        created_at=search.created_at,
    )


def result_to_contract(
    session: Session, result: SearchResultModel
) -> ExternalProcurementSearchResult:
    link = session.scalar(
        select(ExternalProcurementProcessLink).where(
            ExternalProcurementProcessLink.source_system == result.source_system,
            ExternalProcurementProcessLink.source_dataset == result.source_dataset,
            ExternalProcurementProcessLink.source_process_id == result.source_process_id,
        )
    )
    return ExternalProcurementSearchResult(
        id=result.id,
        search_id=result.search_id,
        source_id=result.source_id,
        source_system=ExternalProcurementSourceSystem(result.source_system),
        source_dataset=result.source_dataset,
        source_process_id=result.source_process_id,
        source_process_reference=result.source_process_reference,
        title=result.title,
        entity_name=result.entity_name,
        modality=result.modality,
        status=result.status,
        estimated_value=str(result.estimated_value) if result.estimated_value is not None else None,
        currency=result.currency,
        publication_date=result.publication_date,
        closing_date=result.closing_date,
        department=result.department,
        municipality=result.municipality,
        source_url=result.source_url,
        documents_status=ExternalProcurementDocumentStatus(result.documents_status),
        raw_payload_hash=result.raw_payload_hash,
        field_statuses={
            key: ExternalProcurementFieldStatus(value)
            for key, value in result.field_statuses.items()
        },
        warnings=[ExternalProcurementWarning.model_validate(item) for item in result.warnings],
        import_status=(
            ExternalProcurementImportStatus.IMPORTED
            if link is not None
            else ExternalProcurementImportStatus(result.import_status)
        ),
        process_id=link.process_id if link else None,
        created_at=result.created_at,
    )


def import_result(
    session: Session,
    result_id: UUID,
    *,
    expected_source_process_id: str | None = None,
    actor: CurrentUser | None = None,
    request: Request | None = None,
) -> ExternalProcurementImportResponse:
    result = session.get(SearchResultModel, result_id)
    if result is None:
        raise DomainError(
            ExternalProcurementErrorCode.RESULT_NOT_FOUND,
            "El resultado externo no existe.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    if expected_source_process_id and expected_source_process_id != result.source_process_id:
        raise DomainError(
            ExternalProcurementErrorCode.INVALID_EXTERNAL_PROCESS,
            "El identificador externo no coincide con el resultado seleccionado.",
            status_code=HTTPStatus.CONFLICT,
        )
    deduplication_key = _deduplication_key(result)
    existing_link = session.scalar(
        select(ExternalProcurementProcessLink).where(
            ExternalProcurementProcessLink.source_system == result.source_system,
            ExternalProcurementProcessLink.source_dataset == result.source_dataset,
            ExternalProcurementProcessLink.source_process_id == result.source_process_id,
        )
    )
    now = datetime.now(UTC)
    if existing_link is not None:
        attempt = ExternalProcurementImport(
            id=uuid4(),
            source_result_id=result.id,
            process_id=existing_link.process_id,
            status=ExternalProcurementImportStatus.SKIPPED_DUPLICATE.value,
            deduplication_key=deduplication_key,
            import_manifest={"existing_link_id": str(existing_link.id)},
            imported_at=existing_link.imported_at,
            created_by=actor.id if actor else None,
        )
        session.add(attempt)
        audit_event(
            session,
            event_type=OperationalAuditEventType.EXTERNAL_IMPORT_SKIPPED_DUPLICATE,
            action="external.import",
            status="SKIPPED_DUPLICATE",
            actor=actor,
            request=request,
            entity_type="process",
            entity_id=existing_link.process_id,
            metadata={"deduplication_key": deduplication_key},
        )
        session.commit()
        session.refresh(attempt)
        return _import_to_contract(attempt, "El proceso ya estaba importado; no se duplico.")

    process_id = uuid4()
    process = Process(
        id=process_id,
        internal_reference=f"SECOP-{now:%Y%m%d}-{process_id.hex[:8].upper()}",
        secop_reference=result.source_process_reference,
        title=result.title,
        contracting_entity=result.entity_name,
        description=result.normalized_payload.get("description"),
        source_url=result.source_url,
        selection_method=result.modality,
        estimated_value=result.estimated_value,
        currency=result.currency,
        published_at=result.publication_date,
        closing_at=result.closing_date,
        status=ProcessStatus.DOCUMENTS_PENDING.value,
        source=ProcessSource.SECOP_IMPORT.value,
    )
    # The link and import rows only carry scalar foreign-key values, so make the
    # parent process durable in the unit of work before adding its dependants.
    session.add(process)
    session.flush()
    link = ExternalProcurementProcessLink(
        id=uuid4(),
        process_id=process_id,
        source_result_id=result.id,
        source_system=result.source_system,
        source_dataset=result.source_dataset,
        source_process_id=result.source_process_id,
        source_process_reference=result.source_process_reference,
        source_url=result.source_url,
        documents_url=result.documents_url,
        documents_status=result.documents_status,
        external_metadata={
            "raw_payload_hash": result.raw_payload_hash,
            "field_statuses": result.field_statuses,
            "warnings": result.warnings,
        },
        imported_at=now,
    )
    attempt = ExternalProcurementImport(
        id=uuid4(),
        source_result_id=result.id,
        process_id=process_id,
        status=ExternalProcurementImportStatus.IMPORTED.value,
        deduplication_key=deduplication_key,
        import_manifest={
            "source_system": result.source_system,
            "source_dataset": result.source_dataset,
            "source_process_id": result.source_process_id,
            "currency_status": "PRESENT" if result.currency else "UNKNOWN",
            "analysis_started": False,
        },
        imported_at=now,
        created_by=actor.id if actor else None,
    )
    result.import_status = ExternalProcurementImportStatus.IMPORTED.value
    session.add_all([link, attempt])
    session.add(
        ImportEvent(
            id=uuid4(),
            process_id=process_id,
            event_type="EXTERNAL_PROCESS_IMPORTED",
            details={
                "source_system": result.source_system,
                "source_dataset": result.source_dataset,
                "source_process_id": result.source_process_id,
                "analysis_started": "false",
            },
        )
    )
    audit_event(
        session,
        event_type=OperationalAuditEventType.EXTERNAL_PROCESS_IMPORTED,
        action="external.import",
        status="SUCCESS",
        actor=actor,
        request=request,
        entity_type="process",
        entity_id=process_id,
        metadata={"deduplication_key": deduplication_key},
    )
    session.commit()
    session.refresh(attempt)
    return _import_to_contract(
        attempt,
        "Proceso importado sin ejecutar evaluacion ni descarga automatica de documentos.",
    )


def import_to_contract(item: ExternalProcurementImport) -> ExternalProcurementImportResponse:
    message = (
        "El proceso ya estaba importado; no se duplico."
        if item.status == ExternalProcurementImportStatus.SKIPPED_DUPLICATE.value
        else "Proceso importado sin ejecutar evaluacion automatica."
    )
    return _import_to_contract(item, message)


def process_link_to_contract(link: ExternalProcurementProcessLink) -> ProcessLinkContract:
    return ProcessLinkContract(
        id=link.id,
        process_id=link.process_id,
        source_system=ExternalProcurementSourceSystem(link.source_system),
        source_dataset=link.source_dataset,
        source_process_id=link.source_process_id,
        source_process_reference=link.source_process_reference,
        source_url=link.source_url,
        documents_url=link.documents_url,
        documents_status=ExternalProcurementDocumentStatus(link.documents_status),
        external_metadata=link.external_metadata,
        imported_at=link.imported_at,
        created_at=link.created_at,
    )


def get_search_or_404(session: Session, search_id: UUID) -> ExternalProcurementSearch:
    search = session.get(ExternalProcurementSearch, search_id)
    if search is None:
        raise DomainError(
            ExternalProcurementErrorCode.SEARCH_NOT_FOUND,
            "La busqueda externa no existe.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return search


def _new_result(
    search: ExternalProcurementSearch,
    source: ExternalProcurementSource,
    normalized: dict[str, Any],
    safe_payload: dict[str, Any],
) -> SearchResultModel:
    return SearchResultModel(
        id=uuid4(),
        search_id=search.id,
        source_id=source.id,
        source_system=normalized["source_system"],
        source_dataset=normalized["source_dataset"],
        source_process_id=normalized["source_process_id"],
        source_process_reference=normalized["reference"],
        title=normalized["title"],
        entity_name=normalized["entity_name"],
        modality=normalized["modality"],
        status=normalized["status"],
        estimated_value=normalized["estimated_value"],
        currency=normalized["currency"],
        publication_date=normalized["publication_date"],
        closing_date=normalized["closing_date"],
        department=normalized["department"],
        municipality=normalized["municipality"],
        raw_payload=safe_payload,
        normalized_payload=normalized,
        raw_payload_hash=normalized["raw_payload_hash"],
        field_statuses=normalized["field_statuses"],
        warnings=normalized["warnings"],
        source_url=normalized["source_url"],
        documents_url=normalized["documents_url"],
        documents_status=normalized["documents_status"],
        import_status=ExternalProcurementImportStatus.PENDING.value,
    )


def _deduplication_key(result: SearchResultModel) -> str:
    value = f"{result.source_system}:{result.source_dataset}:{result.source_process_id}"
    return sha256(value.encode("utf-8")).hexdigest()


def _import_to_contract(
    item: ExternalProcurementImport, message: str
) -> ExternalProcurementImportResponse:
    return ExternalProcurementImportResponse(
        id=item.id,
        source_result_id=item.source_result_id,
        process_id=item.process_id,
        status=ExternalProcurementImportStatus(item.status),
        deduplication_key=item.deduplication_key,
        imported_at=item.imported_at,
        created_at=item.created_at,
        message=message,
    )
