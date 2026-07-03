"""Orquestador deterministico de normalizacion de requisitos."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from pliegocheck_api.config import get_settings
from pliegocheck_api.db import get_sessionmaker
from pliegocheck_api.models import (
    ImportEvent,
    RejectedRequirementCandidate,
    Requirement,
    RequirementEvidence,
    RequirementNormalizationBatch,
    RequirementNormalizationJob,
    RequirementNormalizationRun,
    RequirementRelation,
)
from pliegocheck_api.normalization import batch_payload, stable_digest
from pliegocheck_schemas import (
    RejectedCandidateReason,
    RequirementBasis,
    RequirementCandidate,
    RequirementEvidenceStatus,
    RequirementEvidenceValidationStatus,
    RequirementNormalizationStatus,
    RequirementRelationType,
    RequirementReviewStatus,
    RequirementSubsanability,
)
from pliegocheck_worker.normalization.evidence import EvidenceValidator
from pliegocheck_worker.normalization.providers import (
    ConsolidationRequest,
    FakeNormalizationProvider,
    NormalizationBatchRequest,
    OpenAIResponsesNormalizationProvider,
    ProviderError,
    RequirementNormalizationProvider,
)


def normalization_queue_connected() -> bool:
    try:
        sessionmaker = get_sessionmaker()
        with sessionmaker() as session:
            session.execute(select(1))
        return True
    except SQLAlchemyError:
        return False


def normalization_run_once(
    *,
    worker_id: str | None = None,
    provider_name: str | None = None,
) -> dict[str, Any]:
    worker = worker_id or "normalization-worker"
    sessionmaker = get_sessionmaker()
    with sessionmaker() as session:
        job = claim_next_normalization_job(session, worker)
        if job is None:
            return {"status": "idle", "processed": 0, "worker_id": worker}
        result = process_claimed_normalization_job(
            session,
            job.id,
            worker_id=worker,
            provider_name=provider_name,
        )
        result["worker_id"] = worker
        return result


def normalization_drain(
    *,
    max_jobs: int = 100,
    worker_id: str | None = None,
    provider_name: str | None = None,
) -> dict[str, Any]:
    processed = 0
    completed = 0
    failed = 0
    last: dict[str, Any] | None = None
    for _ in range(max_jobs):
        result = normalization_run_once(worker_id=worker_id, provider_name=provider_name)
        last = result
        if result.get("processed") == 0:
            break
        processed += 1
        if result.get("job_status") == RequirementNormalizationStatus.COMPLETED.value:
            completed += 1
        if result.get("job_status") == RequirementNormalizationStatus.FAILED.value:
            failed += 1
    return {
        "status": "ok",
        "processed": processed,
        "completed": completed,
        "failed": failed,
        "last": last,
    }


def claim_next_normalization_job(
    session: Session,
    worker_id: str,
) -> RequirementNormalizationJob | None:
    now = datetime.now(UTC)
    with session.begin():
        job = session.scalar(
            select(RequirementNormalizationJob)
            .where(
                RequirementNormalizationJob.status == RequirementNormalizationStatus.PENDING.value,
                RequirementNormalizationJob.available_at <= now,
            )
            .order_by(
                RequirementNormalizationJob.priority.asc(),
                RequirementNormalizationJob.created_at.asc(),
            )
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if job is None:
            return None
        run = _run_for_job(session, job)
        job.status = RequirementNormalizationStatus.PROCESSING.value
        job.locked_by = worker_id
        job.locked_at = now
        job.started_at = now
        job.finished_at = None
        job.attempt_count += 1
        if run is not None:
            run.status = RequirementNormalizationStatus.PROCESSING.value
            run.started_at = run.started_at or now
            run.error_code = None
            run.error_message = None
        _add_event(
            session,
            process_id=job.process_id,
            event_type="NORMALIZATION_STARTED",
            details={
                "job_id": str(job.id),
                "run_id": str(run.id) if run is not None else "",
                "worker_id": worker_id,
            },
        )
    return job


def process_claimed_normalization_job(
    session: Session,
    job_id: UUID,
    *,
    worker_id: str,
    provider_name: str | None = None,
) -> dict[str, Any]:
    job = session.get(RequirementNormalizationJob, job_id)
    if job is None:
        return {"status": "error", "processed": 0, "error_code": "NORMALIZATION_JOB_NOT_FOUND"}
    run = _run_for_job(session, job)
    if run is None:
        return _fail_job(
            session,
            job,
            None,
            "NORMALIZATION_RUN_NOT_FOUND",
            "El trabajo no tiene una ejecucion asociada.",
            retryable=False,
        )
    try:
        provider = _provider_for_run(run, provider_name)
        _process_run(session, job, run, provider)
        return {
            "status": "ok",
            "processed": 1,
            "job_id": str(job.id),
            "run_id": str(run.id),
            "job_status": job.status,
            "run_status": run.status,
            "accepted_requirement_count": run.accepted_requirement_count,
            "rejected_candidate_count": run.rejected_candidate_count,
        }
    except ProviderError as exc:
        return _fail_job(
            session,
            job,
            run,
            exc.code,
            exc.message,
            retryable=exc.retryable,
        )
    except Exception:
        return _fail_job(
            session,
            job,
            run,
            "NORMALIZATION_FAILED",
            "No fue posible completar la normalizacion.",
            retryable=True,
        )


def _process_run(
    session: Session,
    job: RequirementNormalizationJob,
    run: RequirementNormalizationRun,
    provider: RequirementNormalizationProvider,
) -> None:
    calls = 0
    validator = EvidenceValidator(run.input_manifest)
    prompt_version = run.prompt_version
    consolidation_prompt = run.consolidation_prompt_version
    batches = list(
        session.scalars(
            select(RequirementNormalizationBatch)
            .where(RequirementNormalizationBatch.run_id == run.id)
            .order_by(RequirementNormalizationBatch.batch_index.asc())
        ).all()
    )
    for batch in batches:
        if batch.status == RequirementNormalizationStatus.COMPLETED.value:
            continue
        if calls >= get_settings().openai_normalization_max_calls_per_run:
            raise ProviderError("Se alcanzo el limite de llamadas por ejecucion")
        _process_batch(session, run, batch, provider, validator, prompt_version)
        calls += 1
    _consolidate(session, run, provider, consolidation_prompt)
    _complete_run(session, job, run)


def _process_batch(
    session: Session,
    run: RequirementNormalizationRun,
    batch: RequirementNormalizationBatch,
    provider: RequirementNormalizationProvider,
    validator: EvidenceValidator,
    prompt_version: Any,
) -> None:
    now = datetime.now(UTC)
    payload = batch_payload(
        run.input_manifest,
        [UUID(str(segment_id)) for segment_id in batch.segment_ids],
    )
    segments = payload["segments"]
    assert isinstance(segments, list)
    batch.status = RequirementNormalizationStatus.PROCESSING.value
    batch.started_at = now
    result = provider.normalize_batch(
        NormalizationBatchRequest(
            process_id=run.process_id,
            batch_index=batch.batch_index,
            prompt_version=prompt_version.semantic_version,
            system_prompt=prompt_version.system_content,
            user_template=prompt_version.user_template_content,
            segments=[segment for segment in segments if isinstance(segment, dict)],
        )
    )
    output = result.output
    if not hasattr(output, "candidates"):
        raise ProviderError("El proveedor no devolvio candidatos")
    batch.structured_output = output.model_dump(mode="json")
    batch.provider_response_id = result.response_id
    batch.candidate_count = len(output.candidates)
    batch.input_tokens = result.usage.input_tokens
    batch.output_tokens = result.usage.output_tokens
    batch.reasoning_tokens = result.usage.reasoning_tokens
    accepted = 0
    rejected = 0
    for candidate in output.candidates:
        if _candidate_has_forbidden_decision(candidate):
            _reject_candidate(
                session,
                run=run,
                batch=batch,
                candidate=candidate,
                reason=RejectedCandidateReason.FORBIDDEN_DECISION,
                message="El candidato contiene una decision fuera de alcance.",
            )
            rejected += 1
            continue
        validation_results = [validator.validate(evidence) for evidence in candidate.evidence]
        valid_results = [
            result
            for result in validation_results
            if result.status == RequirementEvidenceValidationStatus.VALID
        ]
        if not valid_results:
            first = validation_results[0] if validation_results else None
            _reject_candidate(
                session,
                run=run,
                batch=batch,
                candidate=candidate,
                reason=_reason_for_validation(first.status if first is not None else None),
                message=first.message if first is not None else "El candidato no tiene evidencia.",
            )
            rejected += 1
            continue
        stable_key = _stable_key(candidate)
        existing = session.scalar(
            select(Requirement.id).where(
                Requirement.normalization_run_id == run.id,
                Requirement.stable_key == stable_key,
            )
        )
        if existing is not None:
            _reject_candidate(
                session,
                run=run,
                batch=batch,
                candidate=candidate,
                reason=RejectedCandidateReason.EXACT_DUPLICATE,
                message="Duplicado exacto consolidado contra un requisito existente.",
            )
            rejected += 1
            continue
        requirement = _persist_requirement(session, run, candidate, stable_key)
        for evidence, validation in zip(candidate.evidence, validation_results, strict=True):
            if validation.status == RequirementEvidenceValidationStatus.VALID:
                assert validation.extraction_id is not None
                session.add(
                    RequirementEvidence(
                        id=uuid4(),
                        requirement_id=requirement.id,
                        extraction_id=validation.extraction_id,
                        segment_id=evidence.segment_id,
                        evidence_role=evidence.evidence_role.value,
                        quoted_text=evidence.quoted_text,
                        quote_start=evidence.quote_start,
                        quote_end=evidence.quote_end,
                        source_location=evidence.source_location.model_dump(mode="json"),
                        validation_status=validation.status.value,
                    )
                )
        accepted += 1
    batch.status = RequirementNormalizationStatus.COMPLETED.value
    batch.finished_at = datetime.now(UTC)
    batch.error_code = None
    batch.error_message = None
    run.candidate_count += batch.candidate_count
    run.accepted_requirement_count += accepted
    run.rejected_candidate_count += rejected
    run.warning_count += len(output.warnings)
    run.input_tokens += batch.input_tokens
    run.output_tokens += batch.output_tokens
    run.reasoning_tokens += batch.reasoning_tokens
    if result.response_id is not None:
        run.provider_response_ids = [*run.provider_response_ids, result.response_id]
    _add_event(
        session,
        process_id=run.process_id,
        event_type="NORMALIZATION_BATCH_COMPLETED",
        details={
            "run_id": str(run.id),
            "batch_id": str(batch.id),
            "candidate_count": str(batch.candidate_count),
            "accepted": str(accepted),
            "rejected": str(rejected),
        },
    )
    session.commit()


def _consolidate(
    session: Session,
    run: RequirementNormalizationRun,
    provider: RequirementNormalizationProvider,
    prompt_version: Any,
) -> None:
    requirements = list(
        session.scalars(
            select(Requirement)
            .where(Requirement.normalization_run_id == run.id)
            .order_by(Requirement.created_at.asc(), Requirement.id.asc())
        ).all()
    )
    if len(requirements) < 2:
        return
    candidates = [
        _candidate_payload_from_requirement(session, requirement) for requirement in requirements
    ]
    result = provider.consolidate_candidates(
        ConsolidationRequest(
            process_id=run.process_id,
            prompt_version=prompt_version.semantic_version,
            system_prompt=prompt_version.system_content,
            user_template=prompt_version.user_template_content,
            candidates=candidates,
        )
    )
    output = result.output
    if not hasattr(output, "relations"):
        raise ProviderError("El proveedor no devolvio relaciones")
    by_stable_key = {requirement.stable_key: requirement for requirement in requirements}
    for proposal in output.relations:
        if proposal.relation_type == RequirementRelationType.INDEPENDENT:
            continue
        source = by_stable_key.get(proposal.source_candidate_id)
        target = by_stable_key.get(proposal.target_candidate_id)
        if source is None or target is None or source.id == target.id:
            continue
        relation = RequirementRelation(
            id=uuid4(),
            process_id=run.process_id,
            normalization_run_id=run.id,
            source_requirement_id=source.id,
            target_requirement_id=target.id,
            relation_type=proposal.relation_type.value,
            explanation=proposal.explanation,
            confidence=Decimal(str(proposal.confidence)),
            requires_human_review=proposal.requires_human_review,
        )
        session.add(relation)
        if proposal.relation_type in {
            RequirementRelationType.POTENTIAL_CONFLICT,
            RequirementRelationType.POTENTIAL_DUPLICATE,
            RequirementRelationType.POTENTIAL_AMENDMENT,
        }:
            source.requires_human_review = True
            target.requires_human_review = True
            _add_event(
                session,
                process_id=run.process_id,
                event_type="REQUIREMENT_CONFLICT_DETECTED",
                details={
                    "run_id": str(run.id),
                    "source_requirement_id": str(source.id),
                    "target_requirement_id": str(target.id),
                    "relation_type": proposal.relation_type.value,
                },
            )
    run.input_tokens += result.usage.input_tokens
    run.output_tokens += result.usage.output_tokens
    run.reasoning_tokens += result.usage.reasoning_tokens
    if result.response_id is not None:
        run.provider_response_ids = [*run.provider_response_ids, result.response_id]
    run.warning_count += len(output.warnings)
    session.commit()


def _complete_run(
    session: Session,
    job: RequirementNormalizationJob,
    run: RequirementNormalizationRun,
) -> None:
    now = datetime.now(UTC)
    rejected = (
        session.scalar(
            select(func.count())
            .select_from(RejectedRequirementCandidate)
            .where(RejectedRequirementCandidate.run_id == run.id)
        )
        or 0
    )
    run.rejected_candidate_count = int(rejected)
    status = (
        RequirementNormalizationStatus.COMPLETED_WITH_WARNINGS.value
        if run.warning_count > 0 or run.rejected_candidate_count > 0
        else RequirementNormalizationStatus.COMPLETED.value
    )
    run.status = status
    run.finished_at = now
    job.status = status
    job.finished_at = now
    job.last_error_code = None
    job.last_error_message = None
    _add_event(
        session,
        process_id=run.process_id,
        event_type="NORMALIZATION_COMPLETED_WITH_WARNINGS"
        if status == RequirementNormalizationStatus.COMPLETED_WITH_WARNINGS.value
        else "NORMALIZATION_COMPLETED",
        details={
            "job_id": str(job.id),
            "run_id": str(run.id),
            "accepted_requirement_count": str(run.accepted_requirement_count),
            "rejected_candidate_count": str(run.rejected_candidate_count),
        },
    )
    session.commit()


def _fail_job(
    session: Session,
    job: RequirementNormalizationJob,
    run: RequirementNormalizationRun | None,
    code: str,
    message: str,
    *,
    retryable: bool,
) -> dict[str, Any]:
    now = datetime.now(UTC)
    if retryable and job.attempt_count < job.max_attempts:
        job.status = RequirementNormalizationStatus.PENDING.value
        job.available_at = now + timedelta(seconds=30 * max(job.attempt_count, 1))
        if run is not None:
            run.status = RequirementNormalizationStatus.PROCESSING.value
    else:
        job.status = RequirementNormalizationStatus.FAILED.value
        job.finished_at = now
        if run is not None:
            run.status = RequirementNormalizationStatus.FAILED.value
            run.finished_at = now
            run.error_code = code
            run.error_message = message
    job.last_error_code = code
    job.last_error_message = message
    _add_event(
        session,
        process_id=job.process_id,
        event_type="NORMALIZATION_FAILED",
        details={
            "job_id": str(job.id),
            "run_id": str(run.id) if run is not None else "",
            "error_code": code,
        },
    )
    session.commit()
    return {
        "status": "error",
        "processed": 1,
        "job_id": str(job.id),
        "run_id": str(run.id) if run is not None else None,
        "job_status": job.status,
        "error_code": code,
        "error_message": message,
    }


def _provider_for_run(
    run: RequirementNormalizationRun,
    provider_name: str | None,
) -> RequirementNormalizationProvider:
    settings = get_settings()
    requested = provider_name or run.provider
    if requested == "fake":
        if not settings.allow_fake_normalization_provider:
            raise ProviderError("El proveedor fake no esta habilitado en este entorno")
        return FakeNormalizationProvider()
    return OpenAIResponsesNormalizationProvider(settings)


def _run_for_job(
    session: Session,
    job: RequirementNormalizationJob,
) -> RequirementNormalizationRun | None:
    if job.run_id is not None:
        run = session.get(RequirementNormalizationRun, job.run_id)
        if run is not None:
            return run
    return session.scalar(
        select(RequirementNormalizationRun)
        .where(RequirementNormalizationRun.job_id == job.id)
        .order_by(RequirementNormalizationRun.created_at.desc())
        .limit(1)
    )


def _candidate_has_forbidden_decision(candidate: RequirementCandidate) -> bool:
    value = " ".join(
        item
        for item in [
            candidate.description,
            candidate.condition_text or "",
            str(candidate.expected_value.raw_text) if candidate.expected_value else "",
        ]
        if item
    ).upper()
    forbidden = ["GO", "NO_GO", "GO_CONDICIONADO", "BUSCAR_ALIADO", "NO_CARGAR"]
    return any(token in value for token in forbidden)


def _stable_key(candidate: RequirementCandidate) -> str:
    payload = {
        "category": candidate.category.value,
        "scope": candidate.scope.value,
        "modality": candidate.modality.value,
        "description": " ".join(candidate.description.split()).casefold(),
        "condition_text": " ".join((candidate.condition_text or "").split()).casefold(),
        "expected_value": candidate.expected_value.model_dump(mode="json")
        if candidate.expected_value is not None
        else None,
        "evidence_quotes": sorted(
            " ".join(e.quoted_text.split()).casefold() for e in candidate.evidence
        ),
    }
    return sha256(stable_digest(payload).encode("utf-8")).hexdigest()


def _persist_requirement(
    session: Session,
    run: RequirementNormalizationRun,
    candidate: RequirementCandidate,
    stable_key: str,
) -> Requirement:
    subsanability = candidate.subsanability
    subsanability_basis = candidate.subsanability_basis
    if subsanability_basis is not RequirementBasis.EXPLICIT:
        subsanability = RequirementSubsanability.UNKNOWN
        subsanability_basis = RequirementBasis.UNKNOWN
    requirement = Requirement(
        id=uuid4(),
        process_id=run.process_id,
        normalization_run_id=run.id,
        stable_key=stable_key,
        category=candidate.category.value,
        scope=candidate.scope.value,
        modality=candidate.modality.value,
        description=candidate.description,
        condition_text=candidate.condition_text,
        expected_value=(
            candidate.expected_value.model_dump(mode="json")
            if candidate.expected_value is not None
            else None
        ),
        criticality=candidate.criticality.value,
        criticality_basis=candidate.criticality_basis.value,
        subsanability=subsanability.value,
        subsanability_basis=subsanability_basis.value,
        confidence=Decimal(str(candidate.confidence)),
        evidence_status=RequirementEvidenceStatus.VALIDATED.value,
        review_status=RequirementReviewStatus.PENDING.value,
        requires_human_review=True,
        is_active=True,
    )
    session.add(requirement)
    session.flush()
    return requirement


def _reject_candidate(
    session: Session,
    *,
    run: RequirementNormalizationRun,
    batch: RequirementNormalizationBatch,
    candidate: RequirementCandidate,
    reason: RejectedCandidateReason,
    message: str,
) -> None:
    session.add(
        RejectedRequirementCandidate(
            id=uuid4(),
            run_id=run.id,
            batch_id=batch.id,
            candidate_id=candidate.candidate_id,
            rejection_reason=reason.value,
            rejection_message=message,
            raw_candidate=candidate.model_dump(mode="json"),
        )
    )
    _add_event(
        session,
        process_id=run.process_id,
        event_type="REQUIREMENT_CANDIDATE_REJECTED",
        details={
            "run_id": str(run.id),
            "batch_id": str(batch.id),
            "candidate_id": candidate.candidate_id,
            "reason": reason.value,
        },
    )


def _reason_for_validation(
    status: RequirementEvidenceValidationStatus | None,
) -> RejectedCandidateReason:
    if status == RequirementEvidenceValidationStatus.INVALID_SEGMENT:
        return RejectedCandidateReason.INVALID_SEGMENT
    if status == RequirementEvidenceValidationStatus.QUOTE_NOT_FOUND:
        return RejectedCandidateReason.QUOTE_NOT_FOUND
    if status == RequirementEvidenceValidationStatus.OUTSIDE_SNAPSHOT:
        return RejectedCandidateReason.OUTSIDE_SNAPSHOT
    if status == RequirementEvidenceValidationStatus.LOCATION_MISMATCH:
        return RejectedCandidateReason.LOCATION_MISMATCH
    return RejectedCandidateReason.REJECTED_UNSUPPORTED


def _candidate_payload_from_requirement(
    session: Session,
    requirement: Requirement,
) -> dict[str, object]:
    evidence_segment_ids = [
        str(segment_id)
        for segment_id in session.scalars(
            select(RequirementEvidence.segment_id).where(
                RequirementEvidence.requirement_id == requirement.id
            )
        ).all()
    ]
    return {
        "candidate_id": requirement.stable_key,
        "requirement_id": str(requirement.id),
        "category": requirement.category,
        "description": requirement.description,
        "condition_text": requirement.condition_text,
        "expected_value": requirement.expected_value,
        "evidence_segment_ids": evidence_segment_ids,
    }


def _add_event(
    session: Session,
    *,
    process_id: UUID,
    event_type: str,
    details: dict[str, str],
) -> None:
    session.add(
        ImportEvent(
            id=uuid4(),
            process_id=process_id,
            document_id=None,
            event_type=event_type,
            details=details,
        )
    )
