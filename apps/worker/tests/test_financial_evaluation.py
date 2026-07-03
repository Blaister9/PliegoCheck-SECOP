# mypy: ignore-errors
"""Pruebas del worker de evaluacion financiera."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select

from pliegocheck_api.db import get_sessionmaker
from pliegocheck_api.financial import build_input_manifest, stable_digest
from pliegocheck_api.models import (
    CompanyProfile,
    CompanyProfileSnapshot,
    FinancialEvaluationJob,
    FinancialEvaluationResult,
    FinancialEvaluationRun,
    FinancialRequirementRule,
    Process,
    Requirement,
    RequirementNormalizationJob,
    RequirementNormalizationRun,
)
from pliegocheck_api.prompt_registry import (
    CONSOLIDATION_PROMPT,
    NORMALIZATION_PROMPT,
    ensure_prompt_version,
)
from pliegocheck_schemas import (
    CompanyProfileStatus,
    CompanySnapshotStatus,
    FinancialEvaluationJobStatus,
    FinancialEvaluationRunStatus,
    FinancialOperator,
    FinancialPeriodPolicy,
    FinancialRuleMappingStatus,
    FinancialRuleSourceBasis,
    FinancialRuleType,
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
)
from pliegocheck_worker.financial.orchestrator import (
    claim_next_financial_job,
    financial_run_once,
)


def test_two_workers_do_not_claim_same_financial_job() -> None:
    job_id = _create_financial_job()
    with get_sessionmaker()() as first_session, get_sessionmaker()() as second_session:
        first = claim_next_financial_job(first_session, "financial-a")
        second = claim_next_financial_job(second_session, "financial-b")
    assert first is not None
    assert first.id == job_id
    assert second is None


def test_financial_worker_calculates_derived_liquidity_ratio() -> None:
    _create_financial_job(use_direct_ratio=False)

    result = financial_run_once(worker_id="financial-test")

    assert result["processed"] == 1
    assert result["run_status"] in {"COMPLETED", "COMPLETED_WITH_WARNINGS"}
    with get_sessionmaker()() as session:
        persisted = session.scalars(select(FinancialEvaluationResult)).one()
        assert persisted.status == "COMPLIES"
        assert persisted.actual_value == Decimal("2.00000000")
        assert persisted.calculation_id is not None


def _create_financial_job(*, use_direct_ratio: bool = True):
    now = datetime.now(UTC)
    process_id = uuid4()
    system_process_id = uuid4()
    company_id = uuid4()
    snapshot_id = uuid4()
    with get_sessionmaker()() as session:
        process = Process(
            id=process_id,
            internal_reference=f"FIN-{process_id.hex[:8]}",
            title="Proceso financiero worker",
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
            legal_name="Empresa Worker SAS",
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
            available_at=now,
            started_at=now,
            finished_at=now,
            force=False,
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
            input_manifest={"documents": [], "warnings": []},
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
            category=RequirementCategory.FINANCIAL.value,
            scope=RequirementScope.HABILITATING.value,
            modality=RequirementModality.MANDATORY.value,
            description="El proponente debe acreditar indice de liquidez minimo de 1.5.",
            condition_text=None,
            expected_value={"value": "1.5", "unit": "ratio", "raw_text": "minimo 1.5"},
            criticality=RequirementCriticality.HIGH.value,
            criticality_basis=RequirementBasis.EXPLICIT.value,
            subsanability=RequirementSubsanability.UNKNOWN.value,
            subsanability_basis=RequirementBasis.UNKNOWN.value,
            confidence=Decimal("0.950"),
            evidence_status=RequirementEvidenceStatus.VALIDATED.value,
            review_status=RequirementReviewStatus.PENDING.value,
            requires_human_review=True,
        )
        session.add(requirement)
        session.flush()
        period_id = uuid4()
        metric_a = uuid4()
        metric_b = uuid4()
        metrics = (
            [
                {
                    "id": str(uuid4()),
                    "financial_period_id": str(period_id),
                    "metric_type": "LIQUIDITY_RATIO",
                    "value": "1.75",
                    "unit": "ratio",
                    "status": "VERIFIED",
                    "is_calculated": False,
                    "formula_inputs": {},
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                }
            ]
            if use_direct_ratio
            else [
                {
                    "id": str(metric_a),
                    "financial_period_id": str(period_id),
                    "metric_type": "CURRENT_ASSETS",
                    "value": "200",
                    "unit": "COP",
                    "status": "VERIFIED",
                    "is_calculated": False,
                    "formula_inputs": {},
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                },
                {
                    "id": str(metric_b),
                    "financial_period_id": str(period_id),
                    "metric_type": "CURRENT_LIABILITIES",
                    "value": "100",
                    "unit": "COP",
                    "status": "VERIFIED",
                    "is_calculated": False,
                    "formula_inputs": {},
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                },
            ]
        )
        snapshot_payload = {
            "company": {"id": str(company_id), "legal_name": "Empresa Worker SAS"},
            "financial_periods": [
                {
                    "id": str(period_id),
                    "company_id": str(company_id),
                    "period_start": "2025-01-01",
                    "period_end": "2025-12-31",
                    "currency": "COP",
                    "source_type": "FINANCIAL_STATEMENT",
                    "status": "VERIFIED",
                    "metrics": metrics,
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                }
            ],
            "evidence_links": [],
            "evidence_documents": [],
        }
        snapshot = CompanyProfileSnapshot(
            id=snapshot_id,
            company_id=company_id,
            version=1,
            status=CompanySnapshotStatus.PUBLISHED.value,
            digest=stable_digest(snapshot_payload),
            payload=snapshot_payload,
            completeness_status="READY_FOR_REVIEW",
            published_at=now,
        )
        session.add(snapshot)
        rule = FinancialRequirementRule(
            id=uuid4(),
            requirement_id=requirement.id,
            normalization_run_id=normalization_run.id,
            rule_type=FinancialRuleType.DERIVED_METRIC.value,
            metric_type="LIQUIDITY_RATIO",
            operator=FinancialOperator.GREATER_THAN_OR_EQUAL.value,
            required_value=Decimal("1.5"),
            required_min_value=None,
            required_max_value=None,
            unit="ratio",
            currency=None,
            period_policy=FinancialPeriodPolicy.LATEST_BEFORE_PROCESS_CLOSING.value,
            period_year=None,
            condition_group={},
            source_basis=FinancialRuleSourceBasis.EXPLICIT_EXPECTED_VALUE.value,
            mapping_status=FinancialRuleMappingStatus.MAPPED.value,
            mapping_warnings=[],
            requires_human_review=False,
            version=1,
            is_manual_override=False,
        )
        session.add(rule)
        session.flush()
        manifest = build_input_manifest(
            process=process,
            normalization_run=normalization_run,
            snapshot=snapshot,
            requirements=[requirement],
        )
        manifest["financial_rule_versions"] = [
            {"requirement_id": str(requirement.id), "rule_id": str(rule.id), "version": 1}
        ]
        job = FinancialEvaluationJob(
            id=uuid4(),
            process_id=process_id,
            normalization_run_id=normalization_run.id,
            company_id=company_id,
            company_profile_snapshot_id=snapshot_id,
            status=FinancialEvaluationJobStatus.PENDING.value,
            available_at=now,
            force=False,
        )
        session.add(job)
        session.flush()
        run = FinancialEvaluationRun(
            id=uuid4(),
            job_id=job.id,
            process_id=process_id,
            normalization_run_id=normalization_run.id,
            company_id=company_id,
            company_profile_snapshot_id=snapshot_id,
            status=FinancialEvaluationRunStatus.PENDING.value,
            input_manifest=manifest,
            input_digest=stable_digest(manifest),
            rule_version="financial-rule-mapper:1.0.0",
            formula_versions={"LIQUIDITY_RATIO": "1.0.0"},
            requirement_count=1,
            evaluated_count=0,
            complies_count=0,
            does_not_comply_count=0,
            partial_count=0,
            unknown_count=0,
            not_applicable_count=0,
            conflicting_count=0,
            warning_count=0,
        )
        session.add(run)
        session.flush()
        job.run_id = run.id
        session.commit()
        return job.id
