"""Runner de trabajos de extraccion documental."""

import hashlib
import multiprocessing as mp
import os
import shutil
import tempfile
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from queue import Empty
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from pliegocheck_api.config import get_settings
from pliegocheck_api.db import get_sessionmaker
from pliegocheck_api.models import (
    DocumentExtraction,
    DocumentProcessingJob,
    ExtractedSegment,
    ImportEvent,
    ProcessDocument,
)
from pliegocheck_api.storage import LocalDocumentStorage, StorageError
from pliegocheck_schemas import (
    DocumentExtractionStatus,
    DocumentProcessingJobStatus,
    DocumentProcessingJobType,
    DocumentProcessingStatus,
)
from pliegocheck_worker.extraction.limits import ExtractionLimits
from pliegocheck_worker.extraction.models import (
    EXTRACTOR_NAME,
    EXTRACTOR_VERSION,
    ControlledExtractionError,
    ExtractionResultData,
)
from pliegocheck_worker.extraction.registry import extract_by_extension


def queue_connected() -> bool:
    try:
        sessionmaker = get_sessionmaker()
        with sessionmaker() as session:
            session.execute(select(1))
        return True
    except SQLAlchemyError:
        return False


def run_once(worker_id: str | None = None) -> dict[str, Any]:
    worker = worker_id or f"worker-{os.getpid()}"
    sessionmaker = get_sessionmaker()
    with sessionmaker() as session:
        job = claim_next_job(session, worker)
        if job is None:
            return {"status": "idle", "processed": 0, "worker_id": worker}
        result = process_claimed_job(session, job.id, worker)
        result["worker_id"] = worker
        return result


def drain(max_jobs: int = 100, worker_id: str | None = None) -> dict[str, Any]:
    processed = 0
    completed = 0
    failed = 0
    last: dict[str, Any] | None = None
    for _ in range(max_jobs):
        result = run_once(worker_id)
        last = result
        if result.get("processed") == 0:
            break
        processed += 1
        if result.get("job_status") == DocumentProcessingJobStatus.COMPLETED.value:
            completed += 1
        if result.get("job_status") == DocumentProcessingJobStatus.FAILED.value:
            failed += 1
    return {
        "status": "ok",
        "processed": processed,
        "completed": completed,
        "failed": failed,
        "last": last,
    }


def claim_next_job(session: Session, worker_id: str) -> DocumentProcessingJob | None:
    now = datetime.now(UTC)
    with session.begin():
        job = session.scalar(
            select(DocumentProcessingJob)
            .where(
                DocumentProcessingJob.job_type == DocumentProcessingJobType.EXTRACT_DOCUMENT.value,
                DocumentProcessingJob.status == DocumentProcessingJobStatus.PENDING.value,
                DocumentProcessingJob.available_at <= now,
            )
            .order_by(
                DocumentProcessingJob.priority.asc(),
                DocumentProcessingJob.created_at.asc(),
            )
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if job is None:
            return None
        job.status = DocumentProcessingJobStatus.PROCESSING.value
        job.locked_by = worker_id
        job.locked_at = now
        job.started_at = now
        job.finished_at = None
        job.attempt_count += 1
        job.document.processing_status = DocumentProcessingStatus.PROCESSING.value
        _add_event(
            session,
            process_id=job.document.process_id,
            document_id=job.document_id,
            event_type="EXTRACTION_STARTED",
            details={"job_id": str(job.id), "worker_id": worker_id},
        )
    return job


def process_claimed_job(session: Session, job_id: UUID, worker_id: str) -> dict[str, Any]:
    job = session.get(DocumentProcessingJob, job_id)
    if job is None:
        return {"status": "error", "processed": 0, "error_code": "PROCESSING_JOB_NOT_FOUND"}
    document = job.document
    settings = get_settings()
    limits = ExtractionLimits.from_settings(settings)
    storage = LocalDocumentStorage(settings.storage_path)

    try:
        source_path = _copy_source_to_temp(storage, document.storage_key)
        try:
            digest = _sha256(source_path)
            if digest != document.sha256:
                raise ControlledExtractionError(
                    "SOURCE_HASH_MISMATCH",
                    "El hash del archivo almacenado no coincide con la metadata.",
                )
            existing = _find_existing_success(session, document)
            if existing is not None:
                _complete_idempotent(session, job, document, existing)
                return {
                    "status": "ok",
                    "processed": 1,
                    "job_id": str(job.id),
                    "job_status": job.status,
                    "extraction_id": str(existing.id),
                    "idempotent": True,
                }
            result = _run_with_timeout(source_path, document.extension, limits)
            extraction = _persist_result(session, job, document, result)
            return {
                "status": "ok",
                "processed": 1,
                "job_id": str(job.id),
                "job_status": job.status,
                "extraction_id": str(extraction.id),
                "extraction_status": extraction.status,
            }
        finally:
            source_path.unlink(missing_ok=True)
    except StorageError:
        return _fail_job(
            session,
            job,
            document,
            "SOURCE_FILE_NOT_FOUND",
            "El archivo original no existe en almacenamiento.",
        )
    except ControlledExtractionError as exc:
        return _fail_job(session, job, document, exc.code, exc.message, status=exc.status)
    except Exception:
        return _fail_job(
            session,
            job,
            document,
            "EXTRACTION_FAILED",
            "No fue posible completar la extraccion.",
        )


def _copy_source_to_temp(storage: LocalDocumentStorage, storage_key: str) -> Path:
    suffix = Path(storage_key).suffix
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=suffix, prefix="pliegocheck-extract-"
    ) as fh:
        with storage.open(storage_key) as source:
            shutil.copyfileobj(source, fh)
        return Path(fh.name)


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _find_existing_success(
    session: Session, document: ProcessDocument
) -> DocumentExtraction | None:
    return session.scalar(
        select(DocumentExtraction)
        .where(
            DocumentExtraction.document_id == document.id,
            DocumentExtraction.source_sha256 == document.sha256,
            DocumentExtraction.extractor_name == EXTRACTOR_NAME,
            DocumentExtraction.extractor_version == EXTRACTOR_VERSION,
            DocumentExtraction.status.in_(
                [
                    DocumentExtractionStatus.COMPLETED.value,
                    DocumentExtractionStatus.COMPLETED_WITH_WARNINGS.value,
                    DocumentExtractionStatus.NEEDS_OCR.value,
                    DocumentExtractionStatus.UNSUPPORTED.value,
                    DocumentExtractionStatus.ENCRYPTED.value,
                ]
            ),
        )
        .order_by(DocumentExtraction.created_at.desc())
    )


def _run_with_timeout(
    source_path: Path,
    extension: str,
    limits: ExtractionLimits,
) -> ExtractionResultData:
    if os.environ.get("PLIEGOCHECK_EXTRACTION_SYNC") == "1":
        return extract_by_extension(str(source_path), extension, limits)

    queue: mp.Queue[dict[str, Any]] = mp.Queue(maxsize=1)
    process = mp.Process(
        target=_child_extract,
        args=(str(source_path), extension, limits, queue),
    )
    process.start()
    process.join(limits.max_seconds)
    if process.is_alive():
        process.terminate()
        process.join(5)
        raise ControlledExtractionError(
            "EXTRACTION_TIMEOUT",
            "La extraccion excedio el tiempo maximo configurado.",
        )
    try:
        payload = queue.get_nowait()
    except Empty as exc:
        raise ControlledExtractionError(
            "EXTRACTION_FAILED",
            "El proceso extractor termino sin resultado.",
        ) from exc
    if payload["ok"]:
        return _result_from_payload(payload["result"])
    raise ControlledExtractionError(
        payload["code"],
        payload["message"],
        payload.get("status", "FAILED"),
    )


def _child_extract(
    source_path: str,
    extension: str,
    limits: ExtractionLimits,
    queue: Any,
) -> None:
    try:
        result = extract_by_extension(source_path, extension, limits)
        queue.put({"ok": True, "result": asdict(result)})
    except ControlledExtractionError as exc:
        queue.put({"ok": False, "code": exc.code, "message": exc.message, "status": exc.status})
    except Exception:
        queue.put(
            {
                "ok": False,
                "code": "EXTRACTION_FAILED",
                "message": "No fue posible completar la extraccion.",
                "status": "FAILED",
            }
        )


def _result_from_payload(payload: dict[str, Any]) -> ExtractionResultData:
    from pliegocheck_worker.extraction.models import ExtractionWarningData, SegmentData

    return ExtractionResultData(
        status=payload["status"],
        detected_format=payload["detected_format"],
        segments=[SegmentData(**segment) for segment in payload.get("segments", [])],
        warnings=[ExtractionWarningData(**warning) for warning in payload.get("warnings", [])],
        page_count=payload.get("page_count"),
        sheet_count=payload.get("sheet_count"),
        character_count=payload.get("character_count", 0),
        language_hint=payload.get("language_hint"),
        error_code=payload.get("error_code"),
        error_message=payload.get("error_message"),
        contains_macros=payload.get("contains_macros", False),
    )


def _persist_result(
    session: Session,
    job: DocumentProcessingJob,
    document: ProcessDocument,
    result: ExtractionResultData,
) -> DocumentExtraction:
    now = datetime.now(UTC)
    extraction = DocumentExtraction(
        id=uuid4(),
        document_id=document.id,
        job_id=job.id,
        source_sha256=document.sha256,
        extractor_name=EXTRACTOR_NAME,
        extractor_version=EXTRACTOR_VERSION,
        status=result.status,
        started_at=job.started_at,
        finished_at=now,
        detected_format=result.detected_format,
        page_count=result.page_count,
        sheet_count=result.sheet_count,
        segment_count=len(result.segments),
        character_count=result.character_count,
        language_hint=result.language_hint,
        warnings=[asdict(warning) for warning in result.warnings],
        error_code=result.error_code,
        error_message=result.error_message,
    )
    session.add(extraction)
    for segment in result.segments:
        session.add(
            ExtractedSegment(
                id=uuid4(),
                extraction_id=extraction.id,
                sequence=segment.sequence,
                segment_type=segment.segment_type,
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
                segment_metadata=segment.metadata,
            )
        )
    job.status = DocumentProcessingJobStatus.COMPLETED.value
    job.finished_at = now
    job.last_error_code = None
    job.last_error_message = None
    document.processing_status = _processing_status_for_extraction(result.status)
    _add_event(
        session,
        process_id=document.process_id,
        document_id=document.id,
        event_type=f"EXTRACTION_{result.status}",
        details={
            "job_id": str(job.id),
            "extraction_id": str(extraction.id),
            "extractor": EXTRACTOR_NAME,
            "extractor_version": EXTRACTOR_VERSION,
            "segment_count": str(len(result.segments)),
            "character_count": str(result.character_count),
            "error_code": result.error_code or "",
        },
    )
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        existing = _find_existing_success(session, document)
        if existing is None:
            raise
        _complete_idempotent(session, job, document, existing)
        return existing
    return extraction


def _complete_idempotent(
    session: Session,
    job: DocumentProcessingJob,
    document: ProcessDocument,
    existing: DocumentExtraction,
) -> None:
    job.status = DocumentProcessingJobStatus.COMPLETED.value
    job.finished_at = datetime.now(UTC)
    job.last_error_code = None
    job.last_error_message = None
    document.processing_status = _processing_status_for_extraction(existing.status)
    _add_event(
        session,
        process_id=document.process_id,
        document_id=document.id,
        event_type="EXTRACTION_COMPLETED",
        details={"job_id": str(job.id), "extraction_id": str(existing.id), "idempotent": "true"},
    )
    session.commit()


def _fail_job(
    session: Session,
    job: DocumentProcessingJob,
    document: ProcessDocument,
    code: str,
    message: str,
    *,
    status: str = "FAILED",
) -> dict[str, Any]:
    now = datetime.now(UTC)
    terminal_status = status
    if status == "FAILED" and job.attempt_count < job.max_attempts:
        job.status = DocumentProcessingJobStatus.PENDING.value
        job.available_at = now + timedelta(seconds=30 * job.attempt_count)
        document.processing_status = DocumentProcessingStatus.QUEUED.value
    else:
        job.status = DocumentProcessingJobStatus.FAILED.value
        job.finished_at = now
        document.processing_status = _processing_status_for_extraction(terminal_status)
    job.last_error_code = code
    job.last_error_message = message
    if terminal_status in {
        DocumentExtractionStatus.NEEDS_OCR.value,
        DocumentExtractionStatus.UNSUPPORTED.value,
        DocumentExtractionStatus.ENCRYPTED.value,
    }:
        result = ExtractionResultData(
            status=terminal_status,
            detected_format=document.extension.removeprefix("."),
            error_code=code,
            error_message=message,
        )
        _persist_result(session, job, document, result)
    else:
        _add_event(
            session,
            process_id=document.process_id,
            document_id=document.id,
            event_type="EXTRACTION_FAILED",
            details={"job_id": str(job.id), "error_code": code},
        )
        session.commit()
    return {
        "status": "error" if terminal_status == "FAILED" else "ok",
        "processed": 1,
        "job_id": str(job.id),
        "job_status": job.status,
        "error_code": code,
        "error_message": message,
    }


def _processing_status_for_extraction(status: str) -> str:
    mapping = {
        DocumentExtractionStatus.COMPLETED.value: DocumentProcessingStatus.COMPLETED.value,
        DocumentExtractionStatus.COMPLETED_WITH_WARNINGS.value: (
            DocumentProcessingStatus.COMPLETED_WITH_WARNINGS.value
        ),
        DocumentExtractionStatus.NEEDS_OCR.value: DocumentProcessingStatus.NEEDS_OCR.value,
        DocumentExtractionStatus.UNSUPPORTED.value: DocumentProcessingStatus.UNSUPPORTED.value,
        DocumentExtractionStatus.ENCRYPTED.value: DocumentProcessingStatus.ENCRYPTED.value,
    }
    return mapping.get(status, DocumentProcessingStatus.FAILED.value)


def _add_event(
    session: Session,
    *,
    process_id: UUID,
    document_id: UUID | None,
    event_type: str,
    details: dict[str, str],
) -> None:
    session.add(
        ImportEvent(
            id=uuid4(),
            process_id=process_id,
            document_id=document_id,
            event_type=event_type,
            details=details,
        )
    )
