"""API de busqueda, resultados, importaciones y enlaces externos."""

from http import HTTPStatus
from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from pliegocheck_api.auth import CurrentUser
from pliegocheck_api.config import Settings, get_settings
from pliegocheck_api.db import get_session
from pliegocheck_api.external_procurement.service import (
    ensure_source_catalog,
    get_search_or_404,
    import_result,
    import_to_contract,
    process_link_to_contract,
    result_to_contract,
    run_search,
    search_to_contract,
    source_to_contract,
)
from pliegocheck_api.models import (
    ExternalProcurementImport,
    ExternalProcurementProcessLink,
    ExternalProcurementSearch,
    ExternalProcurementSearchResult,
    ExternalProcurementSource,
)
from pliegocheck_schemas import (
    ExternalProcurementImportList,
    ExternalProcurementImportRequest,
    ExternalProcurementImportResponse,
    ExternalProcurementProcessLinkList,
    ExternalProcurementResultList,
    ExternalProcurementSearchList,
    ExternalProcurementSearchRequest,
    ExternalProcurementSearchResponse,
    ExternalProcurementSearchSummary,
    ExternalProcurementSourceSummary,
)

router = APIRouter(prefix="/external-procurement", tags=["external-procurement"])
process_router = APIRouter(prefix="/processes", tags=["external-procurement"])
SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
LimitParam = Annotated[int, Query(ge=1, le=100)]
OffsetParam = Annotated[int, Query(ge=0)]


def _actor(request: Request) -> CurrentUser | None:
    value = getattr(request.state, "current_user", None)
    return cast(CurrentUser, value) if value is not None else None


@router.get("/sources", response_model=list[ExternalProcurementSourceSummary])
def list_sources(
    session: SessionDep, settings: SettingsDep
) -> list[ExternalProcurementSourceSummary]:
    return [source_to_contract(item, settings) for item in ensure_source_catalog(session, settings)]


@router.post(
    "/searches",
    response_model=ExternalProcurementSearchResponse,
    status_code=HTTPStatus.CREATED,
)
def create_search(
    payload: ExternalProcurementSearchRequest,
    request: Request,
    session: SessionDep,
    settings: SettingsDep,
) -> ExternalProcurementSearchResponse:
    return run_search(session, settings, payload, actor=_actor(request), request=request)


@router.get("/searches", response_model=ExternalProcurementSearchList)
def list_searches(
    session: SessionDep, limit: LimitParam = 20, offset: OffsetParam = 0
) -> ExternalProcurementSearchList:
    total = session.scalar(select(func.count()).select_from(ExternalProcurementSearch)) or 0
    items = session.scalars(
        select(ExternalProcurementSearch)
        .order_by(ExternalProcurementSearch.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    sources = {item.id: item for item in session.scalars(select(ExternalProcurementSource)).all()}
    return ExternalProcurementSearchList(
        items=[search_to_contract(item, sources[item.source_id]) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/searches/{search_id}", response_model=ExternalProcurementSearchSummary)
def get_search(search_id: UUID, session: SessionDep) -> ExternalProcurementSearchSummary:
    search = get_search_or_404(session, search_id)
    source = session.get(ExternalProcurementSource, search.source_id)
    assert source is not None
    return search_to_contract(search, source)


@router.get("/searches/{search_id}/results", response_model=ExternalProcurementResultList)
def list_results(
    search_id: UUID,
    session: SessionDep,
    limit: LimitParam = 20,
    offset: OffsetParam = 0,
) -> ExternalProcurementResultList:
    get_search_or_404(session, search_id)
    total = (
        session.scalar(
            select(func.count())
            .select_from(ExternalProcurementSearchResult)
            .where(ExternalProcurementSearchResult.search_id == search_id)
        )
        or 0
    )
    items = session.scalars(
        select(ExternalProcurementSearchResult)
        .where(ExternalProcurementSearchResult.search_id == search_id)
        .order_by(ExternalProcurementSearchResult.created_at, ExternalProcurementSearchResult.id)
        .limit(limit)
        .offset(offset)
    ).all()
    return ExternalProcurementResultList(
        search_id=search_id,
        items=[result_to_contract(session, item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/results/{result_id}/import",
    response_model=ExternalProcurementImportResponse,
    status_code=HTTPStatus.CREATED,
)
def create_import(
    result_id: UUID,
    payload: ExternalProcurementImportRequest,
    request: Request,
    session: SessionDep,
) -> ExternalProcurementImportResponse:
    return import_result(
        session,
        result_id,
        expected_source_process_id=payload.expected_source_process_id,
        actor=_actor(request),
        request=request,
    )


@router.get("/imports", response_model=ExternalProcurementImportList)
def list_imports(
    session: SessionDep, limit: LimitParam = 20, offset: OffsetParam = 0
) -> ExternalProcurementImportList:
    total = session.scalar(select(func.count()).select_from(ExternalProcurementImport)) or 0
    items = session.scalars(
        select(ExternalProcurementImport)
        .order_by(ExternalProcurementImport.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return ExternalProcurementImportList(
        items=[import_to_contract(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@process_router.get(
    "/{process_id}/external-links",
    response_model=ExternalProcurementProcessLinkList,
)
def list_process_external_links(
    process_id: UUID, session: SessionDep
) -> ExternalProcurementProcessLinkList:
    items = session.scalars(
        select(ExternalProcurementProcessLink)
        .where(ExternalProcurementProcessLink.process_id == process_id)
        .order_by(ExternalProcurementProcessLink.created_at)
    ).all()
    return ExternalProcurementProcessLinkList(
        process_id=process_id,
        items=[process_link_to_contract(item) for item in items],
        total=len(items),
    )
