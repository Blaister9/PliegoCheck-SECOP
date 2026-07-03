"""Construccion reproducible de snapshots y lotes de normalizacion."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from pliegocheck_api.config import Settings
from pliegocheck_api.models import DocumentExtraction, ExtractedSegment, ProcessDocument
from pliegocheck_schemas import DocumentExtractionStatus


@dataclass(frozen=True)
class SnapshotBuildResult:
    manifest: dict[str, object]
    input_digest: str
    source_extraction_ids: list[UUID]
    segment_count: int
    warnings: list[str]
    omitted_documents: list[dict[str, object]]


@dataclass(frozen=True)
class BatchBuildResult:
    index: int
    segment_ids: list[UUID]
    input_digest: str


TERMINAL_USABLE_EXTRACTION_STATUSES = {
    DocumentExtractionStatus.COMPLETED.value,
    DocumentExtractionStatus.COMPLETED_WITH_WARNINGS.value,
}


def stable_digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def build_input_snapshot(
    session: Session,
    *,
    process_id: UUID,
    document_ids: list[UUID] | None,
    settings: Settings,
) -> SnapshotBuildResult:
    documents_query = (
        select(ProcessDocument)
        .where(ProcessDocument.process_id == process_id)
        .order_by(ProcessDocument.created_at.asc(), ProcessDocument.id.asc())
    )
    if document_ids is not None:
        documents_query = documents_query.where(ProcessDocument.id.in_(document_ids))
    documents = list(session.scalars(documents_query).all())

    requested = set(document_ids or [])
    found = {document.id for document in documents}
    omitted_documents: list[dict[str, object]] = [
        {"document_id": str(document_id), "reason": "DOCUMENT_NOT_IN_PROCESS"}
        for document_id in sorted(requested - found, key=str)
    ]
    warnings: list[str] = []
    manifest_documents: list[dict[str, object]] = []
    manifest_extractions: list[dict[str, object]] = []
    manifest_segments: list[dict[str, object]] = []
    total_characters = 0
    source_extraction_ids: list[UUID] = []

    for document in documents:
        extraction = _latest_usable_extraction(session, document.id)
        if extraction is None:
            omitted_documents.append(
                {
                    "document_id": str(document.id),
                    "filename": document.original_filename,
                    "reason": "NO_COMPLETED_EXTRACTION",
                    "processing_status": document.processing_status,
                }
            )
            continue
        segments = list(
            session.scalars(
                select(ExtractedSegment)
                .where(ExtractedSegment.extraction_id == extraction.id)
                .order_by(ExtractedSegment.sequence.asc())
            ).all()
        )
        if not segments:
            omitted_documents.append(
                {
                    "document_id": str(document.id),
                    "filename": document.original_filename,
                    "reason": "EXTRACTION_WITHOUT_SEGMENTS",
                }
            )
            continue
        manifest_documents.append(
            {
                "document_id": str(document.id),
                "original_filename": document.original_filename,
                "document_type": document.document_type,
                "sha256": document.sha256,
                "extension": document.extension,
            }
        )
        manifest_extractions.append(
            {
                "extraction_id": str(extraction.id),
                "document_id": str(document.id),
                "source_sha256": extraction.source_sha256,
                "extractor_name": extraction.extractor_name,
                "extractor_version": extraction.extractor_version,
                "status": extraction.status,
                "segment_count": extraction.segment_count,
                "character_count": extraction.character_count,
            }
        )
        source_extraction_ids.append(extraction.id)
        for segment in segments:
            if total_characters >= settings.openai_normalization_max_total_characters:
                warnings.append("NORMALIZATION_TOTAL_CHARACTER_LIMIT_REACHED")
                break
            text = segment.text
            remaining = settings.openai_normalization_max_total_characters - total_characters
            if len(text) > remaining:
                text = text[:remaining]
                warnings.append("SEGMENT_TRUNCATED_BY_TOTAL_CHARACTER_LIMIT")
            total_characters += len(text)
            manifest_segments.append(
                {
                    "segment_id": str(segment.id),
                    "extraction_id": str(extraction.id),
                    "document_id": str(document.id),
                    "document_name": document.original_filename,
                    "sequence": segment.sequence,
                    "segment_type": segment.segment_type,
                    "text": text,
                    "source_location": segment.source_location,
                    "page_number": segment.page_number,
                    "paragraph_index": segment.paragraph_index,
                    "table_index": segment.table_index,
                    "sheet_name": segment.sheet_name,
                    "row_start": segment.row_start,
                    "row_end": segment.row_end,
                    "line_start": segment.line_start,
                    "line_end": segment.line_end,
                    "text_sha256": sha256(text.encode("utf-8")).hexdigest(),
                }
            )
        if total_characters >= settings.openai_normalization_max_total_characters:
            break

    manifest: dict[str, object] = {
        "schema_version": "1.0.0",
        "process_id": str(process_id),
        "documents": manifest_documents,
        "extractions": manifest_extractions,
        "segments": manifest_segments,
        "limits": {
            "max_segments_per_batch": settings.openai_normalization_max_segments_per_batch,
            "max_characters_per_batch": settings.openai_normalization_max_characters_per_batch,
            "max_total_characters": settings.openai_normalization_max_total_characters,
        },
        "warnings": warnings,
        "omitted_documents": omitted_documents,
    }
    return SnapshotBuildResult(
        manifest=manifest,
        input_digest=stable_digest(manifest),
        source_extraction_ids=source_extraction_ids,
        segment_count=len(manifest_segments),
        warnings=warnings,
        omitted_documents=omitted_documents,
    )


def build_batches(
    manifest: dict[str, object],
    *,
    max_segments_per_batch: int,
    max_characters_per_batch: int,
) -> list[BatchBuildResult]:
    segments = _manifest_segments(manifest)
    batches: list[BatchBuildResult] = []
    current_segments: list[dict[str, object]] = []
    current_chars = 0
    for segment in segments:
        text = str(segment["text"])
        would_exceed_segments = len(current_segments) >= max_segments_per_batch
        would_exceed_chars = (
            current_segments and current_chars + len(text) > max_characters_per_batch
        )
        if would_exceed_segments or would_exceed_chars:
            batches.append(_batch_from_segments(len(batches), current_segments))
            current_segments = []
            current_chars = 0
        current_segments.append(segment)
        current_chars += len(text)
    if current_segments:
        batches.append(_batch_from_segments(len(batches), current_segments))
    return batches


def batch_payload(manifest: dict[str, object], segment_ids: list[UUID]) -> dict[str, object]:
    selected = {str(segment_id) for segment_id in segment_ids}
    return {
        "schema_version": manifest["schema_version"],
        "process_id": manifest["process_id"],
        "segments": [
            segment
            for segment in _manifest_segments(manifest)
            if str(segment["segment_id"]) in selected
        ],
    }


def segment_index(manifest: dict[str, object]) -> dict[UUID, dict[str, object]]:
    return {UUID(str(segment["segment_id"])): segment for segment in _manifest_segments(manifest)}


def _manifest_segments(manifest: dict[str, object]) -> list[dict[str, object]]:
    segments = manifest.get("segments", [])
    if not isinstance(segments, list):
        return []
    return [segment for segment in segments if isinstance(segment, dict)]


def _batch_from_segments(index: int, segments: list[dict[str, object]]) -> BatchBuildResult:
    segment_ids = [UUID(str(segment["segment_id"])) for segment in segments]
    payload = {"batch_index": index, "segments": segments}
    return BatchBuildResult(
        index=index, segment_ids=segment_ids, input_digest=stable_digest(payload)
    )


def _latest_usable_extraction(session: Session, document_id: UUID) -> DocumentExtraction | None:
    return session.scalar(
        select(DocumentExtraction)
        .where(
            DocumentExtraction.document_id == document_id,
            DocumentExtraction.status.in_(TERMINAL_USABLE_EXTRACTION_STATUSES),
        )
        .order_by(DocumentExtraction.created_at.desc())
        .limit(1)
    )
