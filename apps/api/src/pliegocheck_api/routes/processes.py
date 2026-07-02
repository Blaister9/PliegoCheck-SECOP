"""Endpoints de importacion manual de procesos y documentos."""

import logging
from collections.abc import Iterator
from datetime import UTC, datetime
from hashlib import sha256
from http import HTTPStatus
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Annotated, Any, cast
from urllib.parse import quote
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from pliegocheck_api.config import Settings, get_settings
from pliegocheck_api.db import get_session
from pliegocheck_api.errors import DomainError
from pliegocheck_api.file_validation import (
    FileValidationError,
    detect_content_type,
    validate_declared_content_type,
    validate_original_filename,
)
from pliegocheck_api.models import (
    DocumentExtraction,
    DocumentProcessingJob,
    ExtractedSegment,
    ImportEvent,
    Process,
    ProcessDocument,
)
from pliegocheck_api.storage import DocumentStorage, LocalDocumentStorage, StorageError
from pliegocheck_schemas import (
    ApiError,
    DocumentExtractionDetail,
    DocumentExtractionStatus,
    DocumentExtractionSummary,
    DocumentInventoryItem,
    DocumentProcessingJobStatus,
    DocumentProcessingJobType,
    DocumentProcessingStatus,
    DocumentType,
    DocumentUploadResponse,
    DocumentUploadResult,
    DocumentUploadStatus,
    ExtractedSegmentList,
    ExtractedSegmentType,
    ExtractionErrorCode,
    ExtractionRequest,
    ExtractionRetryResponse,
    ExtractionWarning,
    ProcessCreate,
    ProcessDetail,
    ProcessDocumentList,
    ProcessDocumentMetadata,
    ProcessInventory,
    ProcessList,
    ProcessSource,
    ProcessStatus,
    ProcessSummary,
    UploadErrorCode,
)
from pliegocheck_schemas import (
    ExtractedSegment as ExtractedSegmentContract,
)

router = APIRouter(prefix="/processes", tags=["processes"])
logger = logging.getLogger(__name__)
CHUNK_SIZE = 1024 * 1024
MAX_LIST_LIMIT = 100

SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
LimitParam = Annotated[int, Query(ge=1, le=MAX_LIST_LIMIT)]
OffsetParam = Annotated[int, Query(ge=0)]
StatusParam = Annotated[ProcessStatus | None, Query()]
SearchParam = Annotated[str | None, Query(min_length=1, max_length=200)]
FilesParam = Annotated[list[UploadFile], File()]
SegmentTypeParam = Annotated[ExtractedSegmentType | None, Query()]
PageNumberParam = Annotated[int | None, Query(ge=1)]
SheetNameParam = Annotated[str | None, Query(min_length=1, max_length=255)]


def get_storage(settings: SettingsDep) -> DocumentStorage:
    return LocalDocumentStorage(settings.storage_path)


StorageDep = Annotated[DocumentStorage, Depends(get_storage)]


def process_to_summary(process: Process, document_count: int) -> ProcessSummary:
    return ProcessSummary(
        id=process.id,
        internal_reference=process.internal_reference,
        secop_reference=process.secop_reference,
        title=process.title,
        contracting_entity=process.contracting_entity,
        status=ProcessStatus(process.status),
        closing_at=process.closing_at,
        document_count=document_count,
        created_at=process.created_at,
    )


def document_to_metadata(document: ProcessDocument) -> ProcessDocumentMetadata:
    return ProcessDocumentMetadata(
        id=document.id,
        original_filename=document.original_filename,
        document_type=DocumentType(document.document_type),
        extension=document.extension,
        size_bytes=document.size_bytes,
        sha256=document.sha256,
        declared_content_type=document.declared_content_type,
        detected_content_type=document.detected_content_type,
        upload_status=DocumentUploadStatus(document.upload_status),
        processing_status=DocumentProcessingStatus(document.processing_status),
        created_at=document.created_at,
    )


def warning_to_contract(warning: dict[str, object]) -> ExtractionWarning:
    location = warning.get("location", {})
    return ExtractionWarning(
        code=str(warning.get("code", "UNKNOWN_WARNING")),
        message=str(warning.get("message", "Advertencia de extraccion.")),
        location=cast(dict[str, Any], location) if isinstance(location, dict) else {},
    )


def extraction_to_summary(extraction: DocumentExtraction) -> DocumentExtractionSummary:
    return DocumentExtractionSummary(
        id=extraction.id,
        document_id=extraction.document_id,
        job_id=extraction.job_id,
        source_sha256=extraction.source_sha256,
        extractor_name=extraction.extractor_name,
        extractor_version=extraction.extractor_version,
        status=DocumentExtractionStatus(extraction.status),
        detected_format=extraction.detected_format,
        page_count=extraction.page_count,
        sheet_count=extraction.sheet_count,
        segment_count=extraction.segment_count,
        character_count=extraction.character_count,
        language_hint=extraction.language_hint,
        warnings=[warning_to_contract(warning) for warning in extraction.warnings],
        error_code=(
            ExtractionErrorCode(extraction.error_code)
            if extraction.error_code is not None
            else None
        ),
        error_message=extraction.error_message,
        started_at=extraction.started_at,
        finished_at=extraction.finished_at,
        created_at=extraction.created_at,
        updated_at=extraction.updated_at,
    )


def segment_to_contract(segment: ExtractedSegment) -> ExtractedSegmentContract:
    return ExtractedSegmentContract(
        id=segment.id,
        extraction_id=segment.extraction_id,
        sequence=segment.sequence,
        segment_type=ExtractedSegmentType(segment.segment_type),
        text=segment.text,
        page_number=segment.page_number,
        paragraph_index=segment.paragraph_index,
        table_index=segment.table_index,
        sheet_name=segment.sheet_name,
        row_start=segment.row_start,
        row_end=segment.row_end,
        line_start=segment.line_start,
        line_end=segment.line_end,
        source_location=segment.source_location,
        metadata=segment.segment_metadata,
        created_at=segment.created_at,
    )


def latest_extraction(session: Session, document_id: UUID) -> DocumentExtraction | None:
    return session.scalar(
        select(DocumentExtraction)
        .where(DocumentExtraction.document_id == document_id)
        .order_by(DocumentExtraction.created_at.desc())
        .limit(1)
    )


def document_to_inventory_item(
    session: Session,
    document: ProcessDocument,
) -> DocumentInventoryItem:
    extraction = latest_extraction(session, document.id)
    summary = extraction_to_summary(extraction) if extraction is not None else None
    return DocumentInventoryItem(
        document_id=document.id,
        original_filename=document.original_filename,
        document_type=document.document_type,
        extension=document.extension,
        size_bytes=document.size_bytes,
        sha256=document.sha256,
        declared_content_type=document.declared_content_type,
        detected_content_type=document.detected_content_type,
        upload_status=document.upload_status,
        processing_status=DocumentProcessingStatus(document.processing_status),
        detected_format=extraction.detected_format if extraction is not None else None,
        page_count=extraction.page_count if extraction is not None else None,
        sheet_count=extraction.sheet_count if extraction is not None else None,
        has_text=bool(extraction and extraction.character_count > 0),
        is_encrypted=bool(
            extraction and extraction.status == DocumentExtractionStatus.ENCRYPTED.value
        ),
        needs_ocr=bool(
            extraction and extraction.status == DocumentExtractionStatus.NEEDS_OCR.value
        ),
        contains_macros=any(
            warning.get("code") == "OFFICE_MACROS_DETECTED"
            for warning in (extraction.warnings if extraction is not None else [])
        ),
        segment_count=extraction.segment_count if extraction is not None else 0,
        character_count=extraction.character_count if extraction is not None else 0,
        warnings=(
            [warning_to_contract(warning) for warning in extraction.warnings]
            if extraction is not None
            else []
        ),
        latest_extraction=summary,
        created_at=document.created_at,
    )


def process_to_detail(process: Process) -> ProcessDetail:
    documents = [document_to_metadata(document) for document in process.documents]
    return ProcessDetail(
        id=process.id,
        internal_reference=process.internal_reference,
        secop_reference=process.secop_reference,
        title=process.title,
        contracting_entity=process.contracting_entity,
        description=process.description,
        source_url=process.source_url,
        selection_method=process.selection_method,
        estimated_value=(
            str(process.estimated_value) if process.estimated_value is not None else None
        ),
        currency=process.currency,
        published_at=process.published_at,
        closing_at=process.closing_at,
        status=ProcessStatus(process.status),
        source=ProcessSource(process.source),
        document_count=len(documents),
        documents=documents,
        created_at=process.created_at,
        updated_at=process.updated_at,
    )


def get_process_or_404(session: Session, process_id: UUID) -> Process:
    process = session.scalar(
        select(Process).where(Process.id == process_id).options(selectinload(Process.documents))
    )
    if process is None:
        raise DomainError(
            UploadErrorCode.PROCESS_NOT_FOUND,
            "El proceso no existe.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return process


def add_event(
    session: Session,
    *,
    process_id: UUID,
    event_type: str,
    document_id: UUID | None = None,
    details: dict[str, str] | None = None,
) -> None:
    session.add(
        ImportEvent(
            id=uuid4(),
            process_id=process_id,
            document_id=document_id,
            event_type=event_type,
            details=details or {},
        )
    )


@router.post("", response_model=ProcessDetail, status_code=HTTPStatus.CREATED)
def create_process(
    payload: ProcessCreate,
    session: SessionDep,
) -> ProcessDetail:
    process_id = uuid4()
    now = datetime.now(UTC)
    process = Process(
        id=process_id,
        internal_reference=f"MAN-{now:%Y%m%d}-{process_id.hex[:8].upper()}",
        secop_reference=payload.secop_reference,
        title=payload.title,
        contracting_entity=payload.contracting_entity,
        description=payload.description,
        source_url=str(payload.source_url) if payload.source_url is not None else None,
        selection_method=payload.selection_method,
        estimated_value=payload.estimated_value,
        currency=payload.currency,
        published_at=payload.published_at,
        closing_at=payload.closing_at,
        status=ProcessStatus.DRAFT.value,
        source=ProcessSource.MANUAL.value,
    )
    session.add(process)
    add_event(session, process_id=process.id, event_type="PROCESS_CREATED")
    try:
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        logger.exception("database_error_creating_process")
        raise DomainError(
            UploadErrorCode.DATABASE_ERROR,
            "No fue posible crear el proceso.",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        ) from exc
    session.refresh(process)
    logger.info("process_created", extra={"process_id": str(process.id)})
    return process_to_detail(process)


@router.get("", response_model=ProcessList)
def list_processes(
    session: SessionDep,
    limit: LimitParam = 20,
    offset: OffsetParam = 0,
    status: StatusParam = None,
    search: SearchParam = None,
) -> ProcessList:
    filters = []
    if status is not None:
        filters.append(Process.status == status.value)
    if search is not None:
        pattern = f"%{search.strip()}%"
        filters.append(
            or_(
                Process.title.ilike(pattern),
                Process.contracting_entity.ilike(pattern),
                Process.internal_reference.ilike(pattern),
                Process.secop_reference.ilike(pattern),
            )
        )

    count_query = select(func.count()).select_from(Process)
    items_query = (
        select(Process, func.count(ProcessDocument.id).label("document_count"))
        .outerjoin(ProcessDocument)
        .group_by(Process.id)
        .order_by(Process.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if filters:
        count_query = count_query.where(*filters)
        items_query = items_query.where(*filters)

    total = session.scalar(count_query) or 0
    rows = session.execute(items_query).all()
    return ProcessList(
        items=[process_to_summary(process, document_count) for process, document_count in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{process_id}", response_model=ProcessDetail)
def get_process(process_id: UUID, session: SessionDep) -> ProcessDetail:
    return process_to_detail(get_process_or_404(session, process_id))


@router.post("/{process_id}/documents", response_model=DocumentUploadResponse)
def upload_documents(
    process_id: UUID,
    response: Response,
    session: SessionDep,
    storage: StorageDep,
    settings: SettingsDep,
    files: FilesParam,
) -> DocumentUploadResponse:
    process = get_process_or_404(session, process_id)
    if not files:
        raise DomainError(
            UploadErrorCode.FILE_EMPTY,
            "Debe adjuntar al menos un archivo.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    results = [
        _store_one_file(
            process=process,
            upload=upload,
            session=session,
            storage=storage,
            max_file_size=settings.max_file_size_bytes,
        )
        for upload in files
    ]
    stored_count = sum(
        1 for result in results if result.upload_status is DocumentUploadStatus.STORED
    )
    rejected_count = len(results) - stored_count
    if stored_count > 0 and rejected_count == 0:
        response.status_code = HTTPStatus.CREATED
    elif stored_count > 0 and rejected_count > 0:
        response.status_code = HTTPStatus.MULTI_STATUS
    else:
        response.status_code = HTTPStatus.BAD_REQUEST
    return DocumentUploadResponse(
        process_id=process_id,
        results=results,
        stored_count=stored_count,
        rejected_count=rejected_count,
    )


@router.get("/{process_id}/documents", response_model=ProcessDocumentList)
def list_documents(
    process_id: UUID,
    session: SessionDep,
) -> ProcessDocumentList:
    process = get_process_or_404(session, process_id)
    documents = [document_to_metadata(document) for document in process.documents]
    return ProcessDocumentList(process_id=process_id, total=len(documents), documents=documents)


@router.get("/{process_id}/inventory", response_model=ProcessInventory)
def get_process_inventory(process_id: UUID, session: SessionDep) -> ProcessInventory:
    process = get_process_or_404(session, process_id)
    documents = [document_to_inventory_item(session, document) for document in process.documents]
    return ProcessInventory(process_id=process_id, total=len(documents), documents=documents)


@router.post("/{process_id}/extractions", response_model=list[ExtractionRetryResponse])
def enqueue_process_extractions(
    process_id: UUID,
    session: SessionDep,
    settings: SettingsDep,
) -> list[ExtractionRetryResponse]:
    process = get_process_or_404(session, process_id)
    return [
        enqueue_document_extraction(
            session=session,
            process=process,
            document=document,
            force=False,
            max_attempts=settings.worker_max_attempts,
        )
        for document in process.documents
    ]


@router.post(
    "/{process_id}/documents/{document_id}/extractions",
    response_model=ExtractionRetryResponse,
)
def enqueue_one_extraction(
    process_id: UUID,
    document_id: UUID,
    payload: ExtractionRequest,
    session: SessionDep,
    settings: SettingsDep,
) -> ExtractionRetryResponse:
    process = get_process_or_404(session, process_id)
    document = get_document_or_404(session, process_id, document_id)
    return enqueue_document_extraction(
        session=session,
        process=process,
        document=document,
        force=payload.force,
        max_attempts=settings.worker_max_attempts,
    )


@router.get(
    "/{process_id}/documents/{document_id}/extraction",
    response_model=DocumentExtractionDetail,
)
def get_document_extraction(
    process_id: UUID,
    document_id: UUID,
    session: SessionDep,
) -> DocumentExtractionDetail:
    get_process_or_404(session, process_id)
    get_document_or_404(session, process_id, document_id)
    extraction = latest_extraction(session, document_id)
    if extraction is None:
        raise DomainError(
            ExtractionErrorCode.EXTRACTION_NOT_FOUND,
            "No existe extraccion para este documento.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    segments = session.scalars(
        select(ExtractedSegment)
        .where(ExtractedSegment.extraction_id == extraction.id)
        .order_by(ExtractedSegment.sequence)
        .limit(5)
    ).all()
    return DocumentExtractionDetail(
        **extraction_to_summary(extraction).model_dump(),
        segments_preview=[segment_to_contract(segment) for segment in segments],
    )


@router.get(
    "/{process_id}/documents/{document_id}/extraction/segments",
    response_model=ExtractedSegmentList,
)
def get_extraction_segments(
    process_id: UUID,
    document_id: UUID,
    session: SessionDep,
    limit: LimitParam = 20,
    offset: OffsetParam = 0,
    page_number: PageNumberParam = None,
    sheet_name: SheetNameParam = None,
    segment_type: SegmentTypeParam = None,
) -> ExtractedSegmentList:
    get_process_or_404(session, process_id)
    get_document_or_404(session, process_id, document_id)
    extraction = latest_extraction(session, document_id)
    if extraction is None:
        raise DomainError(
            ExtractionErrorCode.EXTRACTION_NOT_FOUND,
            "No existe extraccion para este documento.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    filters = [ExtractedSegment.extraction_id == extraction.id]
    if page_number is not None:
        filters.append(ExtractedSegment.page_number == page_number)
    if sheet_name is not None:
        filters.append(ExtractedSegment.sheet_name == sheet_name)
    if segment_type is not None:
        filters.append(ExtractedSegment.segment_type == segment_type.value)
    total = session.scalar(select(func.count()).select_from(ExtractedSegment).where(*filters)) or 0
    segments = session.scalars(
        select(ExtractedSegment)
        .where(*filters)
        .order_by(ExtractedSegment.sequence)
        .limit(limit)
        .offset(offset)
    ).all()
    return ExtractedSegmentList(
        extraction_id=extraction.id,
        total=total,
        limit=limit,
        offset=offset,
        segments=[segment_to_contract(segment) for segment in segments],
    )


@router.get("/{process_id}/documents/{document_id}/download")
def download_document(
    process_id: UUID,
    document_id: UUID,
    session: SessionDep,
    storage: StorageDep,
) -> StreamingResponse:
    get_process_or_404(session, process_id)
    document = session.scalar(
        select(ProcessDocument).where(
            ProcessDocument.id == document_id,
            ProcessDocument.process_id == process_id,
        )
    )
    if document is None:
        raise DomainError(
            UploadErrorCode.DOCUMENT_NOT_FOUND,
            "El documento no existe para este proceso.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    if not storage.exists(document.storage_key):
        raise DomainError(
            UploadErrorCode.DOCUMENT_NOT_FOUND,
            "El archivo original no existe en almacenamiento.",
            status_code=HTTPStatus.NOT_FOUND,
        )

    add_event(
        session,
        process_id=process_id,
        document_id=document_id,
        event_type="DOCUMENT_DOWNLOADED",
        details={"document_id": str(document_id)},
    )
    session.commit()
    logger.info(
        "document_downloaded",
        extra={"process_id": str(process_id), "document_id": str(document_id)},
    )
    content_disposition = _content_disposition(document.original_filename)
    return StreamingResponse(
        _stream_storage(storage, document.storage_key),
        media_type=document.detected_content_type or "application/octet-stream",
        headers={"Content-Disposition": content_disposition},
    )


def get_document_or_404(session: Session, process_id: UUID, document_id: UUID) -> ProcessDocument:
    document = session.scalar(
        select(ProcessDocument).where(
            ProcessDocument.id == document_id,
            ProcessDocument.process_id == process_id,
        )
    )
    if document is None:
        raise DomainError(
            UploadErrorCode.DOCUMENT_NOT_FOUND,
            "El documento no existe para este proceso.",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return document


def enqueue_document_extraction(
    *,
    session: Session,
    process: Process,
    document: ProcessDocument,
    force: bool,
    max_attempts: int,
) -> ExtractionRetryResponse:
    active_job = session.scalar(
        select(DocumentProcessingJob).where(
            DocumentProcessingJob.document_id == document.id,
            DocumentProcessingJob.job_type == DocumentProcessingJobType.EXTRACT_DOCUMENT.value,
            DocumentProcessingJob.status.in_(
                [
                    DocumentProcessingJobStatus.PENDING.value,
                    DocumentProcessingJobStatus.PROCESSING.value,
                ]
            ),
        )
    )
    if active_job is not None:
        return ExtractionRetryResponse(
            document_id=document.id,
            job_id=active_job.id,
            processing_status=DocumentProcessingStatus(document.processing_status),
            message="El documento ya tiene un trabajo activo.",
        )

    extraction = latest_extraction(session, document.id)
    if (
        not force
        and extraction is not None
        and extraction.status
        in {
            DocumentExtractionStatus.COMPLETED.value,
            DocumentExtractionStatus.COMPLETED_WITH_WARNINGS.value,
            DocumentExtractionStatus.NEEDS_OCR.value,
            DocumentExtractionStatus.UNSUPPORTED.value,
            DocumentExtractionStatus.ENCRYPTED.value,
        }
    ):
        return ExtractionRetryResponse(
            document_id=document.id,
            job_id=None,
            processing_status=DocumentProcessingStatus(document.processing_status),
            message="El documento ya tiene una extraccion vigente.",
        )

    job = DocumentProcessingJob(
        id=uuid4(),
        document_id=document.id,
        job_type=DocumentProcessingJobType.EXTRACT_DOCUMENT.value,
        max_attempts=max_attempts,
        available_at=datetime.now(UTC),
    )
    document.processing_status = DocumentProcessingStatus.QUEUED.value
    session.add(job)
    add_event(
        session,
        process_id=process.id,
        document_id=document.id,
        event_type="EXTRACTION_RETRIED" if force else "EXTRACTION_QUEUED",
        details={"job_id": str(job.id), "force": str(force).lower()},
    )
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        active_job = session.scalar(
            select(DocumentProcessingJob).where(
                DocumentProcessingJob.document_id == document.id,
                DocumentProcessingJob.job_type == DocumentProcessingJobType.EXTRACT_DOCUMENT.value,
                DocumentProcessingJob.status.in_(
                    [
                        DocumentProcessingJobStatus.PENDING.value,
                        DocumentProcessingJobStatus.PROCESSING.value,
                    ]
                ),
            )
        )
        if active_job is None:
            raise
        return ExtractionRetryResponse(
            document_id=document.id,
            job_id=active_job.id,
            processing_status=DocumentProcessingStatus.QUEUED,
            message="El documento ya tiene un trabajo activo.",
        )
    return ExtractionRetryResponse(
        document_id=document.id,
        job_id=job.id,
        processing_status=DocumentProcessingStatus.QUEUED,
        message="Trabajo de extraccion encolado.",
    )


def _store_one_file(
    *,
    process: Process,
    upload: UploadFile,
    session: Session,
    storage: DocumentStorage,
    max_file_size: int,
) -> DocumentUploadResult:
    original_filename = upload.filename or "archivo-sin-nombre"
    temp_path: Path | None = None
    storage_key: str | None = None
    try:
        original_filename, extension = validate_original_filename(upload.filename)
        validate_declared_content_type(extension, upload.content_type)
        temp_path, digest, size_bytes = _write_temp_and_hash(upload, max_file_size)
        if size_bytes == 0:
            raise FileValidationError(UploadErrorCode.FILE_EMPTY, "El archivo esta vacio.")
        detected_content_type = detect_content_type(temp_path, extension)

        duplicate = session.scalar(
            select(ProcessDocument.id).where(
                ProcessDocument.process_id == process.id,
                ProcessDocument.sha256 == digest,
            )
        )
        if duplicate is not None:
            _record_rejection(
                session,
                process.id,
                original_filename,
                "DUPLICATE_DOCUMENT_REJECTED",
                UploadErrorCode.DUPLICATE_DOCUMENT,
                "El documento ya fue cargado en este proceso.",
            )
            return _rejected(
                original_filename,
                UploadErrorCode.DUPLICATE_DOCUMENT,
                "El documento ya fue cargado en este proceso.",
            )

        document_id = uuid4()
        stored_filename = f"{document_id.hex}{extension}"
        storage_key = f"{process.id}/{document_id}/{stored_filename}"
        storage.save(temp_path, storage_key)
        temp_path = None
        document = ProcessDocument(
            id=document_id,
            process_id=process.id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            storage_key=storage_key,
            declared_content_type=upload.content_type,
            detected_content_type=detected_content_type,
            extension=extension,
            size_bytes=size_bytes,
            sha256=digest,
            document_type=DocumentType.UNKNOWN.value,
            upload_status=DocumentUploadStatus.STORED.value,
            processing_status=DocumentProcessingStatus.QUEUED.value,
        )
        session.add(document)
        job = DocumentProcessingJob(
            id=uuid4(),
            document_id=document_id,
            job_type=DocumentProcessingJobType.EXTRACT_DOCUMENT.value,
            max_attempts=get_settings().worker_max_attempts,
            available_at=datetime.now(UTC),
        )
        session.add(job)
        process.status = ProcessStatus.READY_FOR_INVENTORY.value
        add_event(
            session,
            process_id=process.id,
            document_id=document_id,
            event_type="DOCUMENT_UPLOADED",
            details={"document_id": str(document_id), "original_filename": original_filename},
        )
        add_event(
            session,
            process_id=process.id,
            document_id=document_id,
            event_type="EXTRACTION_QUEUED",
            details={"job_id": str(job.id), "job_type": job.job_type},
        )
        session.commit()
        session.refresh(document)
        logger.info(
            "document_uploaded",
            extra={"process_id": str(process.id), "document_id": str(document.id)},
        )
        return DocumentUploadResult(
            original_filename=original_filename,
            upload_status=DocumentUploadStatus.STORED,
            document=document_to_metadata(document),
        )
    except FileValidationError as exc:
        session.rollback()
        _record_rejection(
            session,
            process.id,
            original_filename,
            "DOCUMENT_REJECTED",
            exc.code,
            exc.message,
        )
        logger.info("document_rejected", extra={"process_id": str(process.id), "code": exc.code})
        return _rejected(original_filename, exc.code, exc.message, exc.details)
    except StorageError:
        session.rollback()
        logger.exception("storage_error_uploading_document")
        _record_rejection(
            session,
            process.id,
            original_filename,
            "DOCUMENT_REJECTED",
            UploadErrorCode.STORAGE_ERROR,
            "No fue posible almacenar el documento.",
        )
        return _rejected(
            original_filename,
            UploadErrorCode.STORAGE_ERROR,
            "No fue posible almacenar el documento.",
        )
    except IntegrityError:
        session.rollback()
        if storage_key is not None and not _delete_compensating(storage, storage_key):
            logger.error("database_error_left_orphaned_file", extra={"storage_key": storage_key})
        _record_rejection(
            session,
            process.id,
            original_filename,
            "DUPLICATE_DOCUMENT_REJECTED",
            UploadErrorCode.DUPLICATE_DOCUMENT,
            "El documento ya fue cargado en este proceso.",
        )
        return _rejected(
            original_filename,
            UploadErrorCode.DUPLICATE_DOCUMENT,
            "El documento ya fue cargado en este proceso.",
        )
    except SQLAlchemyError:
        session.rollback()
        if storage_key is not None and not _delete_compensating(storage, storage_key):
            logger.error("database_error_left_orphaned_file", extra={"storage_key": storage_key})
        logger.exception("database_error_uploading_document")
        return _rejected(
            original_filename,
            UploadErrorCode.DATABASE_ERROR,
            "No fue posible registrar el documento.",
        )
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def _write_temp_and_hash(upload: UploadFile, max_file_size: int) -> tuple[Path, str, int]:
    hasher = sha256()
    size = 0
    temp_path: Path | None = None
    try:
        with NamedTemporaryFile(delete=False, prefix="pliegocheck-upload-", suffix=".tmp") as temp:
            temp_path = Path(temp.name)
            while chunk := upload.file.read(CHUNK_SIZE):
                size += len(chunk)
                if size > max_file_size:
                    raise FileValidationError(
                        UploadErrorCode.FILE_TOO_LARGE,
                        "El archivo supera el tamano maximo permitido.",
                        details={"max_file_size_bytes": str(max_file_size)},
                    )
                hasher.update(chunk)
                temp.write(chunk)
    except Exception:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()
        raise
    assert temp_path is not None
    return temp_path, hasher.hexdigest(), size


def _record_rejection(
    session: Session,
    process_id: UUID,
    original_filename: str,
    event_type: str,
    code: UploadErrorCode,
    message: str,
) -> None:
    add_event(
        session,
        process_id=process_id,
        event_type=event_type,
        details={"original_filename": original_filename, "code": code.value, "message": message},
    )
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        logger.exception("database_error_recording_rejection")


def _rejected(
    original_filename: str,
    code: UploadErrorCode,
    message: str,
    details: dict[str, str] | None = None,
) -> DocumentUploadResult:
    return DocumentUploadResult(
        original_filename=original_filename,
        upload_status=DocumentUploadStatus.REJECTED,
        error=ApiError(code=code, message=message, details=details or {}),
    )


def _delete_compensating(storage: DocumentStorage, storage_key: str) -> bool:
    try:
        storage.delete(storage_key)
        return True
    except StorageError:
        logger.exception("storage_compensation_failed", extra={"storage_key": storage_key})
        return False


def _stream_storage(storage: DocumentStorage, storage_key: str) -> Iterator[bytes]:
    with storage.open(storage_key) as fh:
        while chunk := fh.read(CHUNK_SIZE):
            yield chunk


def _content_disposition(filename: str) -> str:
    fallback = "".join(char if char.isalnum() or char in "._-" else "_" for char in filename)
    quoted = quote(filename)
    return f"attachment; filename=\"{fallback}\"; filename*=UTF-8''{quoted}"
