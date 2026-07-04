# mypy: ignore-errors
"""Pruebas del worker de evaluaciones especializadas."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select

from pliegocheck_api.db import get_sessionmaker
from pliegocheck_api.models import (
    CompanyProfile,
    CompanyProfileSnapshot,
    Process,
    Requirement,
    RequirementNormalizationJob,
    RequirementNormalizationRun,
    SpecializedEvaluationJob,
    SpecializedEvaluationResult,
    SpecializedEvaluationRun,
    SpecializedRequirementRule,
)
from pliegocheck_api.prompt_registry import (
    CONSOLIDATION_PROMPT,
    NORMALIZATION_PROMPT,
    ensure_prompt_version,
)
from pliegocheck_api.specialized_evaluation import (
    RULE_MAPPING_VERSION,
    build_input_manifest,
    map_specialized_requirement,
    stable_digest,
)
from pliegocheck_schemas import (
    CompanyProfileStatus,
    CompanySnapshotStatus,
    NormalizationProvider,
    ProcessSource,
    ProcessStatus,
    RequirementBasis,
    RequirementCategory,
    RequirementCriticality,
    RequirementEvidenceStatus,
    RequirementModality,
    RequirementNormalizationStatus,
    RequirementReviewStatus,
    RequirementScope,
    RequirementSubsanability,
    SpecializedEvaluationJobStatus,
    SpecializedEvaluationRunStatus,
)
from pliegocheck_worker.specialized.orchestrator import (
    claim_next_specialized_job,
    specialized_run_once,
)


def test_two_workers_do_not_claim_same_specialized_job() -> None:
    job_id = _create_specialized_job("LEGAL")
    with get_sessionmaker()() as first_session, get_sessionmaker()() as second_session:
        first = claim_next_specialized_job(first_session, "specialized-a")
        second = claim_next_specialized_job(second_session, "specialized-b")
    assert first is not None
    assert first.id == job_id
    assert second is None


def test_specialized_worker_completes_legal_requirement() -> None:
    _create_specialized_job("LEGAL")

    result = specialized_run_once(worker_id="specialized-test")

    assert result["processed"] == 1
    assert result["run_status"] in {"COMPLETED", "COMPLETED_WITH_WARNINGS"}
    with get_sessionmaker()() as session:
        persisted = session.scalars(select(SpecializedEvaluationResult)).one()
        assert persisted.domain == "LEGAL"
        assert persisted.status == "COMPLIES"
        assert persisted.requires_human_review is True


def _create_specialized_job(domain: str):
    now = datetime.now(UTC)
    process_id = uuid4()
    system_process_id = uuid4()
    company_id = uuid4()
    snapshot_id = uuid4()
    with get_sessionmaker()() as session:
        process = Process(
            id=process_id,
            internal_reference=f"SPEC-{process_id.hex[:8]}",
            title="Proceso especializado worker",
            contracting_entity="Entidad",
            closing_at=datetime(2026, 12, 31, tzinfo=UTC),
            status=ProcessStatus.READY_FOR_INVENTORY.value,
            source=ProcessSource.MANUAL.value,
        )
        system_process = Process(
            id=system_process_id,
            internal_reference=f"CPDOC-{company_id.hex[:8]}",
            title="Documentos de empresa",
            contracting_entity="Empresa",
            status=ProcessStatus.DRAFT.value,
            source=ProcessSource.MANUAL.value,
            is_system=True,
        )
        company = CompanyProfile(
            id=company_id,
            system_process_id=system_process_id,
            internal_reference=f"CP-{company_id.hex[:8]}",
            legal_name="Empresa Especializada SAS",
            status=CompanyProfileStatus.READY_FOR_REVIEW.value,
            economic_activity_codes=[],
        )
        session.add_all([process, system_process, company])
        normalization_prompt = ensure_prompt_version(session, NORMALIZATION_PROMPT)
        consolidation_prompt = ensure_prompt_version(session, CONSOLIDATION_PROMPT)
        normalization_job = RequirementNormalizationJob(
            id=uuid4(),
            process_id=process_id,
            status=RequirementNormalizationStatus.COMPLETED.value,
            force=False,
            available_at=now,
            started_at=now,
            finished_at=now,
        )
        session.add(normalization_job)
        session.flush()
        normalization_run = RequirementNormalizationRun(
            id=uuid4(),
            job_id=normalization_job.id,
            process_id=process_id,
            status=RequirementNormalizationStatus.COMPLETED.value,
            provider=NormalizationProvider.FAKE.value,
            model="fake",
            reasoning_effort="none",
            prompt_version_id=normalization_prompt.id,
            consolidation_prompt_version_id=consolidation_prompt.id,
            input_manifest={"documents": []},
            input_digest="c" * 64,
            source_extraction_ids=[],
            segment_count=0,
            batch_count=0,
            candidate_count=1,
            accepted_requirement_count=1,
            rejected_candidate_count=0,
            warning_count=0,
            input_tokens=0,
            output_tokens=0,
            reasoning_tokens=0,
            provider_response_ids=[],
            started_at=now,
            finished_at=now,
        )
        session.add(normalization_run)
        session.flush()
        normalization_job.run_id = normalization_run.id
        requirement = Requirement(
            id=uuid4(),
            process_id=process_id,
            normalization_run_id=normalization_run.id,
            stable_key="d" * 64,
            category=RequirementCategory.LEGAL.value,
            scope=RequirementScope.HABILITATING.value,
            modality=RequirementModality.MANDATORY.value,
            description="Debe aportar RUP vigente.",
            expected_value={},
            criticality=RequirementCriticality.HIGH.value,
            criticality_basis=RequirementBasis.EXPLICIT.value,
            subsanability=RequirementSubsanability.UNKNOWN.value,
            subsanability_basis=RequirementBasis.UNKNOWN.value,
            confidence=Decimal("0.950"),
            evidence_status=RequirementEvidenceStatus.VALIDATED.value,
            review_status=RequirementReviewStatus.PENDING.value,
            requires_human_review=True,
            is_active=True,
        )
        session.add(requirement)
        session.flush()
        snapshot_payload = {
            "rup_snapshots": [
                {
                    "id": str(uuid4()),
                    "status": "SUPPORTED",
                    "valid_until": "2027-01-01",
                }
            ],
            "evidence_links": [],
        }
        snapshot = CompanyProfileSnapshot(
            id=snapshot_id,
            company_id=company_id,
            version=1,
            status=CompanySnapshotStatus.PUBLISHED.value,
            digest="e" * 64,
            payload=snapshot_payload,
            completeness_status="READY_FOR_REVIEW",
            published_at=now,
        )
        session.add(snapshot)
        rule = SpecializedRequirementRule(
            id=uuid4(), **map_specialized_requirement(requirement, domain)
        )
        session.add(rule)
        session.flush()
        manifest = build_input_manifest(
            process=process,
            normalization_run=normalization_run,
            snapshot=snapshot,
            requirements=[requirement],
            domain=domain,
        )
        manifest["specialized_rule_versions"] = [
            {
                "requirement_id": str(requirement.id),
                "rule_id": str(rule.id),
                "version": rule.version,
            }
        ]
        job = SpecializedEvaluationJob(
            id=uuid4(),
            process_id=process_id,
            normalization_run_id=normalization_run.id,
            company_id=company_id,
            company_profile_snapshot_id=snapshot_id,
            domain=domain,
            status=SpecializedEvaluationJobStatus.PENDING.value,
            available_at=now,
            force=False,
        )
        session.add(job)
        session.flush()
        run = SpecializedEvaluationRun(
            id=uuid4(),
            job_id=job.id,
            process_id=process_id,
            normalization_run_id=normalization_run.id,
            company_id=company_id,
            company_profile_snapshot_id=snapshot_id,
            domain=domain,
            status=SpecializedEvaluationRunStatus.PENDING.value,
            input_manifest=manifest,
            input_digest=stable_digest(manifest),
            rule_version=RULE_MAPPING_VERSION,
            requirement_count=1,
        )
        session.add(run)
        session.flush()
        job.run_id = run.id
        session.commit()
        return job.id
