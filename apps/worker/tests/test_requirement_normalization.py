"""Pruebas del worker de normalizacion de requisitos."""

import json
from datetime import UTC, datetime
from hashlib import sha256
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import select

from pliegocheck_api.config import get_settings
from pliegocheck_api.db import get_sessionmaker
from pliegocheck_api.models import (
    DocumentExtraction,
    DocumentProcessingJob,
    ExtractedSegment,
    Process,
    ProcessDocument,
    Requirement,
    RequirementNormalizationBatch,
    RequirementNormalizationJob,
    RequirementNormalizationRun,
)
from pliegocheck_api.normalization import build_batches, build_input_snapshot
from pliegocheck_api.prompt_registry import (
    CONSOLIDATION_PROMPT,
    NORMALIZATION_PROMPT,
    ensure_prompt_version,
)
from pliegocheck_schemas import (
    DocumentProcessingJobStatus,
    DocumentProcessingJobType,
    DocumentProcessingStatus,
    DocumentType,
    DocumentUploadStatus,
    NormalizationProvider,
    ProcessSource,
    ProcessStatus,
    RequirementNormalizationStatus,
)
from pliegocheck_worker.normalization.orchestrator import (
    claim_next_normalization_job,
    normalization_run_once,
)
from pliegocheck_worker.normalization.providers import (
    NormalizationBatchRequest,
    OpenAIResponsesNormalizationProvider,
    ProviderResponseInvalidError,
)


def test_snapshot_and_batches_are_deterministic() -> None:
    process_id = _create_extracted_process(
        "El proponente debe acreditar indice de liquidez minimo de 1.2."
    )
    settings = get_settings()
    with get_sessionmaker()() as session:
        first = build_input_snapshot(
            session, process_id=process_id, document_ids=None, settings=settings
        )
        second = build_input_snapshot(
            session, process_id=process_id, document_ids=None, settings=settings
        )
        assert first.input_digest == second.input_digest
        batches = build_batches(
            first.manifest,
            max_segments_per_batch=1,
            max_characters_per_batch=1000,
        )
        assert len(batches) == 1
        assert (
            batches[0].input_digest
            == build_batches(
                second.manifest,
                max_segments_per_batch=1,
                max_characters_per_batch=1000,
            )[0].input_digest
        )


def test_two_workers_do_not_claim_same_normalization_job() -> None:
    run_id = _create_normalization_run(
        "El proponente debe presentar experiencia minima de dos contratos."
    )
    with get_sessionmaker()() as first_session, get_sessionmaker()() as second_session:
        first = claim_next_normalization_job(first_session, "normalizer-a")
        second = claim_next_normalization_job(second_session, "normalizer-b")
    assert first is not None
    assert first.run_id == run_id
    assert second is None


def test_normalization_worker_persists_requirements_and_rejections() -> None:
    _create_normalization_run(
        "El proponente debe acreditar indice de liquidez minimo de 1.2. "
        "REQUISITO_SIN_EVIDENCIA_FAKE"
    )
    result = normalization_run_once(worker_id="normalizer", provider_name="fake")
    assert result["processed"] == 1
    assert result["accepted_requirement_count"] >= 1
    assert result["rejected_candidate_count"] >= 1
    with get_sessionmaker()() as session:
        requirement = session.scalars(select(Requirement)).one()
        assert requirement.evidence_status == "VALIDATED"
        assert requirement.review_status == "PENDING"


def test_openai_provider_uses_strict_schema_without_tools() -> None:
    settings = get_settings().model_copy(
        update={
            "ai_enabled": True,
            "openai_api_key": "test-key",
            "openai_normalization_background": False,
        }
    )
    responses = _FakeResponses(_openai_output())
    provider = OpenAIResponsesNormalizationProvider.__new__(OpenAIResponsesNormalizationProvider)
    provider_any = cast(Any, provider)
    provider_any._settings = settings
    provider_any._client = SimpleNamespace(responses=responses)

    result = provider.normalize_batch(_openai_request())

    assert result.response_id == "resp_1"
    assert responses.create_kwargs["tools"] == []
    assert responses.create_kwargs["store"] is False
    assert responses.create_kwargs["text"]["format"]["strict"] is True
    assert responses.create_kwargs["text"]["format"]["type"] == "json_schema"


def test_openai_provider_polls_background_response() -> None:
    settings = get_settings().model_copy(
        update={
            "ai_enabled": True,
            "openai_api_key": "test-key",
            "openai_normalization_background": True,
            "openai_normalization_poll_interval_seconds": 1,
        }
    )
    responses = _FakeResponses(_openai_output(), queued_first=True)
    provider = OpenAIResponsesNormalizationProvider.__new__(OpenAIResponsesNormalizationProvider)
    provider_any = cast(Any, provider)
    provider_any._settings = settings
    provider_any._client = SimpleNamespace(responses=responses)

    provider.normalize_batch(_openai_request())

    assert responses.create_kwargs["background"] is True
    assert "store" not in responses.create_kwargs
    assert responses.retrieve_count == 1


def test_openai_provider_rejects_invalid_structured_output() -> None:
    settings = get_settings().model_copy(
        update={
            "ai_enabled": True,
            "openai_api_key": "test-key",
            "openai_normalization_background": False,
        }
    )
    responses = _FakeResponses("{}")
    provider = OpenAIResponsesNormalizationProvider.__new__(OpenAIResponsesNormalizationProvider)
    provider_any = cast(Any, provider)
    provider_any._settings = settings
    provider_any._client = SimpleNamespace(responses=responses)

    try:
        provider.normalize_batch(_openai_request())
    except ProviderResponseInvalidError:
        return
    raise AssertionError("La salida estructurada invalida debia rechazarse")


def _create_normalization_run(text: str) -> UUID:
    process_id = _create_extracted_process(text)
    settings = get_settings()
    with get_sessionmaker()() as session:
        normalization_prompt = ensure_prompt_version(session, NORMALIZATION_PROMPT)
        consolidation_prompt = ensure_prompt_version(session, CONSOLIDATION_PROMPT)
        snapshot = build_input_snapshot(
            session, process_id=process_id, document_ids=None, settings=settings
        )
        batches = build_batches(
            snapshot.manifest,
            max_segments_per_batch=settings.openai_normalization_max_segments_per_batch,
            max_characters_per_batch=settings.openai_normalization_max_characters_per_batch,
        )
        job = RequirementNormalizationJob(
            id=uuid4(),
            process_id=process_id,
            status=RequirementNormalizationStatus.PENDING.value,
            max_attempts=3,
            available_at=datetime.now(UTC),
            force=False,
        )
        session.add(job)
        session.flush()
        run = RequirementNormalizationRun(
            id=uuid4(),
            job_id=job.id,
            process_id=process_id,
            status=RequirementNormalizationStatus.PENDING.value,
            provider=NormalizationProvider.FAKE.value,
            model="fake",
            reasoning_effort="none",
            prompt_version_id=normalization_prompt.id,
            consolidation_prompt_version_id=consolidation_prompt.id,
            input_manifest=snapshot.manifest,
            input_digest=snapshot.input_digest,
            source_extraction_ids=[
                str(extraction_id) for extraction_id in snapshot.source_extraction_ids
            ],
            segment_count=snapshot.segment_count,
            batch_count=len(batches),
            candidate_count=0,
            accepted_requirement_count=0,
            rejected_candidate_count=0,
            warning_count=0,
            input_tokens=0,
            output_tokens=0,
            reasoning_tokens=0,
            provider_response_ids=[],
        )
        session.add(run)
        session.flush()
        job.run_id = run.id
        for batch in batches:
            session.add(
                RequirementNormalizationBatch(
                    id=uuid4(),
                    run_id=run.id,
                    batch_index=batch.index,
                    status=RequirementNormalizationStatus.PENDING.value,
                    segment_ids=[str(segment_id) for segment_id in batch.segment_ids],
                    input_digest=batch.input_digest,
                )
            )
        session.commit()
        return run.id


def _create_extracted_process(text: str) -> UUID:
    process_id = uuid4()
    document_id = uuid4()
    extraction_job_id = uuid4()
    extraction_id = uuid4()
    content_hash = sha256(text.encode()).hexdigest()
    with get_sessionmaker()() as session:
        process = Process(
            id=process_id,
            internal_reference=f"MAN-TEST-{process_id.hex[:8]}",
            title="Proceso normalizacion",
            contracting_entity="Entidad",
            status=ProcessStatus.READY_FOR_INVENTORY.value,
            source=ProcessSource.MANUAL.value,
        )
        document = ProcessDocument(
            id=document_id,
            process_id=process_id,
            original_filename="pliego.txt",
            stored_filename=f"{document_id.hex}.txt",
            storage_key=f"{process_id}/{document_id}/{document_id.hex}.txt",
            declared_content_type="text/plain",
            detected_content_type="text/plain",
            extension=".txt",
            size_bytes=len(text.encode()),
            sha256=content_hash,
            document_type=DocumentType.TERMS.value,
            upload_status=DocumentUploadStatus.STORED.value,
            processing_status=DocumentProcessingStatus.COMPLETED.value,
        )
        extraction_job = DocumentProcessingJob(
            id=extraction_job_id,
            document_id=document_id,
            job_type=DocumentProcessingJobType.EXTRACT_DOCUMENT.value,
            status=DocumentProcessingJobStatus.COMPLETED.value,
            max_attempts=3,
            attempt_count=1,
            available_at=datetime.now(UTC),
        )
        extraction = DocumentExtraction(
            id=extraction_id,
            document_id=document_id,
            job_id=extraction_job_id,
            source_sha256=content_hash,
            extractor_name="test",
            extractor_version="1",
            status="COMPLETED",
            detected_format="txt",
            segment_count=1,
            character_count=len(text),
            warnings=[],
        )
        segment = ExtractedSegment(
            id=uuid4(),
            extraction_id=extraction_id,
            sequence=1,
            segment_type="TEXT_LINES",
            text=text,
            line_start=1,
            line_end=1,
            source_location={"line_start": 1, "line_end": 1},
            segment_metadata={},
        )
        session.add_all([process, document, extraction_job, extraction, segment])
        session.commit()
    return process_id


class _FakeResponses:
    def __init__(self, output_text: str, *, queued_first: bool = False) -> None:
        self.output_text = output_text
        self.queued_first = queued_first
        self.create_kwargs: dict[str, Any] = {}
        self.retrieve_count = 0

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.create_kwargs = kwargs
        if self.queued_first:
            return SimpleNamespace(id="resp_1", status="queued")
        return _fake_openai_response(self.output_text)

    def retrieve(self, _response_id: str) -> SimpleNamespace:
        self.retrieve_count += 1
        return _fake_openai_response(self.output_text)


def _fake_openai_response(output_text: str) -> SimpleNamespace:
    return SimpleNamespace(
        id="resp_1",
        status="completed",
        output_text=output_text,
        usage=SimpleNamespace(
            input_tokens=11,
            output_tokens=22,
            output_tokens_details=SimpleNamespace(reasoning_tokens=3),
        ),
    )


def _openai_output() -> str:
    return json.dumps(
        {
            "schema_version": "2.0.0",
            "agent": "RequirementNormalizationAgent",
            "prompt_version": "1.0.0",
            "process_id": "11111111-1111-1111-1111-111111111111",
            "batch_index": 0,
            "candidates": [],
            "warnings": [],
        }
    )


def _openai_request() -> NormalizationBatchRequest:
    return NormalizationBatchRequest(
        process_id=UUID("11111111-1111-1111-1111-111111111111"),
        batch_index=0,
        prompt_version="1.0.0",
        system_prompt="system",
        user_template="{{segments_json}}",
        segments=[],
    )
