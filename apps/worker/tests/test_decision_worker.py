# mypy: ignore-errors
"""Pruebas del worker y componentes del motor de decision."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from pliegocheck_api.db import get_sessionmaker
from pliegocheck_api.decision import DECISION_ENGINE_VERSION
from pliegocheck_api.decision.coverage import DecisionCoverageAnalyzer
from pliegocheck_api.decision.findings import (
    DEFAULT_ADAPTER_REGISTRY,
    FinancialDecisionEvaluationAdapter,
    not_evaluated_finding,
)
from pliegocheck_api.decision.policy import DecisionPolicy, load_active_policy
from pliegocheck_api.models import (
    CompanyProfile,
    CompanyProfileSnapshot,
    DecisionJob,
    DecisionPolicyVersion,
    DecisionRun,
    FinancialEvaluationJob,
    FinancialEvaluationRun,
    Process,
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
    DecisionEvaluationDomain,
    DecisionFindingOutcome,
    DecisionJobStatus,
    DecisionRunStatus,
    FinancialEvaluationJobStatus,
    FinancialEvaluationRunStatus,
    NormalizationProvider,
    ProcessSource,
    ProcessStatus,
    RequirementNormalizationStatus,
)
from pliegocheck_worker.decision.orchestrator import claim_next_decision_job


@dataclass
class StubRequirement:
    id: UUID = field(default_factory=uuid4)
    stable_key: str = "f" * 64
    category: str = "FINANCIAL"
    scope: str = "HABILITATING"
    modality: str = "MANDATORY"
    criticality: str = "HIGH"
    criticality_basis: str = "EXPLICIT"
    subsanability: str = "UNKNOWN"
    subsanability_basis: str = "UNKNOWN"


@dataclass
class StubFinancialResult:
    id: UUID = field(default_factory=uuid4)
    status: str = "COMPLIES"
    review_status: str = "PENDING"
    reviewed_status: str | None = None
    requires_human_review: bool = False
    evidence_refs: dict[str, Any] = field(default_factory=lambda: {"links": []})
    explanation_parameters: dict[str, Any] = field(default_factory=dict)


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("COMPLIES", DecisionFindingOutcome.COMPLIES),
        ("DOES_NOT_COMPLY", DecisionFindingOutcome.DOES_NOT_COMPLY),
        ("PARTIAL", DecisionFindingOutcome.PARTIAL),
        ("UNKNOWN", DecisionFindingOutcome.UNKNOWN),
        ("NOT_APPLICABLE", DecisionFindingOutcome.NOT_APPLICABLE),
        ("CONFLICTING_EVIDENCE", DecisionFindingOutcome.CONFLICTING_EVIDENCE),
    ],
)
def test_financial_adapter_preserves_every_outcome(
    status: str, expected: DecisionFindingOutcome
) -> None:
    adapter = FinancialDecisionEvaluationAdapter()
    requirement = StubRequirement()
    result = StubFinancialResult(status=status)
    findings = adapter.collect_findings(
        requirements=[requirement],
        context={
            "financial_results_by_requirement": {requirement.id: result},
            "financial_evaluation_run_id": uuid4(),
        },
    )
    assert len(findings) == 1
    finding = findings[0]
    assert finding.outcome == expected
    assert finding.partner_solvable is False
    assert finding.is_remediable is False
    assert finding.submission_blocker is False
    assert any(ref["type"] == "financial_evaluation_result" for ref in finding.evidence_references)


def test_financial_adapter_respects_override() -> None:
    adapter = FinancialDecisionEvaluationAdapter()
    requirement = StubRequirement()
    result = StubFinancialResult(
        status="COMPLIES",
        review_status="OVERRIDDEN",
        reviewed_status="DOES_NOT_COMPLY",
        requires_human_review=True,
    )
    finding = adapter.collect_findings(
        requirements=[requirement],
        context={
            "financial_results_by_requirement": {requirement.id: result},
            "financial_evaluation_run_id": uuid4(),
        },
    )[0]
    assert finding.outcome == DecisionFindingOutcome.DOES_NOT_COMPLY
    assert finding.requires_human_review is False
    assert finding.review_status == "OVERRIDDEN"


def test_registry_fills_not_evaluated_for_missing_adapter() -> None:
    financial = StubRequirement()
    legal = StubRequirement(category="LEGAL")
    result = StubFinancialResult()
    findings = DEFAULT_ADAPTER_REGISTRY.collect_all_findings(
        requirements=[financial, legal],
        context={
            "financial_results_by_requirement": {financial.id: result},
            "financial_evaluation_run_id": uuid4(),
        },
    )
    by_category = {finding.category: finding for finding in findings}
    assert by_category["FINANCIAL"].outcome == DecisionFindingOutcome.COMPLIES
    assert by_category["LEGAL"].outcome == DecisionFindingOutcome.NOT_EVALUATED
    assert by_category["LEGAL"].source_type.value == "MISSING_ADAPTER"


def test_financial_requirement_without_result_is_not_evaluated() -> None:
    financial = StubRequirement()
    findings = DEFAULT_ADAPTER_REGISTRY.collect_all_findings(
        requirements=[financial],
        context={
            "financial_results_by_requirement": {},
            "financial_evaluation_run_id": uuid4(),
        },
    )
    assert findings[0].outcome == DecisionFindingOutcome.NOT_EVALUATED


def test_coverage_counts_are_exact() -> None:
    analyzer = DecisionCoverageAnalyzer([DecisionEvaluationDomain.FINANCIAL])
    financial = StubRequirement()
    legal = StubRequirement(category="LEGAL")
    result = StubFinancialResult()
    findings = DEFAULT_ADAPTER_REGISTRY.collect_all_findings(
        requirements=[financial, legal],
        context={
            "financial_results_by_requirement": {financial.id: result},
            "financial_evaluation_run_id": uuid4(),
        },
    )
    coverage = analyzer.analyze(findings)
    assert coverage.requirements_total == 2
    assert coverage.mandatory_applicable_total == 2
    assert coverage.evaluated_total == 1
    assert coverage.not_evaluated_total == 1
    assert coverage.complies_total == 1
    categories = {category.category: category for category in coverage.categories}
    assert categories["FINANCIAL"].coverage_status.value == "COMPLETE"
    assert categories["FINANCIAL"].adapter_available is True
    assert categories["LEGAL"].coverage_status.value == "MISSING"
    assert categories["LEGAL"].adapter_available is False
    payload = coverage.model_dump()
    assert "percentage" not in str(payload).lower()
    assert "score" not in str(payload).lower()


def test_policy_loads_with_stable_hash() -> None:
    first_policy, _first_payload, first_hash = load_active_policy()
    second_policy, _second_payload, second_hash = load_active_policy()
    assert first_hash == second_hash
    assert first_policy.semantic_version == second_policy.semantic_version


def test_policy_rejects_positive_uncertainty_behavior() -> None:
    _policy, payload, _digest = load_active_policy()
    broken = dict(payload, unknown_behavior="GO")
    with pytest.raises(ValidationError):
        DecisionPolicy.model_validate(broken)


def test_policy_rejects_incomplete_precedence() -> None:
    _policy, payload, _digest = load_active_policy()
    broken = dict(payload, precedence=["GO", "NO_GO"])
    with pytest.raises(ValidationError):
        DecisionPolicy.model_validate(broken)


def test_two_workers_do_not_claim_same_decision_job() -> None:
    job_id = _create_decision_job()
    with get_sessionmaker()() as first_session, get_sessionmaker()() as second_session:
        first = claim_next_decision_job(first_session, "worker-a")
        second = claim_next_decision_job(second_session, "worker-b")
        assert first is not None and first.id == job_id
        assert second is None


def test_not_evaluated_finding_never_positive_fields() -> None:
    requirement = StubRequirement(category="TECHNICAL")
    finding = not_evaluated_finding(requirement)
    assert finding.outcome == DecisionFindingOutcome.NOT_EVALUATED
    assert finding.partner_solvable is False
    assert finding.is_remediable is False
    assert "ADAPTER_NOT_AVAILABLE" in finding.warning_codes


def _create_decision_job() -> UUID:
    now = datetime.now(UTC)
    with get_sessionmaker()() as session:
        process = Process(
            id=uuid4(),
            internal_reference=f"PC-{uuid4().hex[:8]}",
            title="Proceso decision worker",
            contracting_entity="Entidad",
            status=ProcessStatus.READY_FOR_INVENTORY.value,
            source=ProcessSource.MANUAL.value,
            currency="COP",
        )
        session.add(process)
        normalization_prompt = ensure_prompt_version(session, NORMALIZATION_PROMPT)
        consolidation_prompt = ensure_prompt_version(session, CONSOLIDATION_PROMPT)
        normalization_job = RequirementNormalizationJob(
            id=uuid4(),
            process_id=process.id,
            status=RequirementNormalizationStatus.COMPLETED.value,
            force=False,
            available_at=now,
        )
        session.add(normalization_job)
        session.flush()
        normalization_run = RequirementNormalizationRun(
            id=uuid4(),
            job_id=normalization_job.id,
            process_id=process.id,
            status=RequirementNormalizationStatus.COMPLETED.value,
            provider=NormalizationProvider.FAKE.value,
            model="fake",
            reasoning_effort="none",
            prompt_version_id=normalization_prompt.id,
            consolidation_prompt_version_id=consolidation_prompt.id,
            input_manifest={},
            input_digest="1" * 64,
            source_extraction_ids=[],
            segment_count=0,
            batch_count=0,
            candidate_count=0,
            accepted_requirement_count=0,
            rejected_candidate_count=0,
            warning_count=0,
            input_tokens=0,
            output_tokens=0,
            reasoning_tokens=0,
            provider_response_ids=[],
        )
        session.add(normalization_run)
        company_id = uuid4()
        system_process = Process(
            id=uuid4(),
            internal_reference=f"CPDOC-{company_id.hex[:8]}",
            title="Documentos de empresa",
            contracting_entity="Empresa",
            status=ProcessStatus.DRAFT.value,
            source=ProcessSource.MANUAL.value,
            is_system=True,
        )
        session.add(system_process)
        session.flush()
        company = CompanyProfile(
            id=company_id,
            system_process_id=system_process.id,
            internal_reference=f"CP-{company_id.hex[:8]}",
            legal_name="Empresa Worker SAS",
            status=CompanyProfileStatus.READY_FOR_REVIEW.value,
            economic_activity_codes=[],
        )
        session.add(company)
        session.flush()
        snapshot = CompanyProfileSnapshot(
            id=uuid4(),
            company_id=company.id,
            version=1,
            status=CompanySnapshotStatus.PUBLISHED.value,
            digest="2" * 64,
            payload={},
            completeness_status="COMPLETE",
            published_at=now,
        )
        session.add(snapshot)
        financial_job = FinancialEvaluationJob(
            id=uuid4(),
            process_id=process.id,
            normalization_run_id=normalization_run.id,
            company_id=company.id,
            company_profile_snapshot_id=snapshot.id,
            status=FinancialEvaluationJobStatus.COMPLETED.value,
            available_at=now,
        )
        session.add(financial_job)
        session.flush()
        financial_run = FinancialEvaluationRun(
            id=uuid4(),
            job_id=financial_job.id,
            process_id=process.id,
            normalization_run_id=normalization_run.id,
            company_id=company.id,
            company_profile_snapshot_id=snapshot.id,
            status=FinancialEvaluationRunStatus.COMPLETED.value,
            input_manifest={},
            input_digest="3" * 64,
            rule_version="financial-rule-mapper:1.0.0",
            formula_versions={},
        )
        session.add(financial_run)
        policy_version = DecisionPolicyVersion(
            id=uuid4(),
            policy_name="pliegocheck-default",
            semantic_version="1.0.0",
            content_sha256="4" * 64,
            policy_payload={},
            engine_version=DECISION_ENGINE_VERSION,
        )
        session.add(policy_version)
        session.flush()
        job = DecisionJob(
            id=uuid4(),
            process_id=process.id,
            normalization_run_id=normalization_run.id,
            company_id=company.id,
            company_profile_snapshot_id=snapshot.id,
            financial_evaluation_run_id=financial_run.id,
            status=DecisionJobStatus.PENDING.value,
            available_at=now,
        )
        session.add(job)
        session.flush()
        run = DecisionRun(
            id=uuid4(),
            job_id=job.id,
            process_id=process.id,
            normalization_run_id=normalization_run.id,
            company_id=company.id,
            company_profile_snapshot_id=snapshot.id,
            financial_evaluation_run_id=financial_run.id,
            policy_version_id=policy_version.id,
            status=DecisionRunStatus.PENDING.value,
            input_manifest={"requirement_ids": []},
            input_digest="5" * 64,
            engine_version=DECISION_ENGINE_VERSION,
            effective_at=now,
        )
        session.add(run)
        session.flush()
        job.run_id = run.id
        session.commit()
        return job.id
