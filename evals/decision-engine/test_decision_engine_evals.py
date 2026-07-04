# mypy: ignore-errors
"""Evals del motor deterministico de decision.

Tablas de decision con hallazgos sinteticos sobre el motor puro: sin IA,
sin base de datos y sin resultados probabilisticos.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from pliegocheck_api.decision.coverage import DecisionCoverageAnalyzer
from pliegocheck_api.decision.engine import DecisionContext, DeterministicDecisionEngine
from pliegocheck_api.decision.findings import DEFAULT_ADAPTER_REGISTRY
from pliegocheck_api.decision.manifest import stable_decision_digest
from pliegocheck_api.decision.policy import load_active_policy
from pliegocheck_schemas import (
    DecisionEvaluationDomain,
    DecisionFindingApplicability,
    DecisionFindingOutcome,
    DecisionFindingSourceType,
    DecisionInputFinding,
    DecisionOutcome,
)

POLICY, _PAYLOAD, POLICY_HASH = load_active_policy()
ENGINE = DeterministicDecisionEngine()
ANALYZER = DecisionCoverageAnalyzer(DEFAULT_ADAPTER_REGISTRY.available_domains())
EFFECTIVE_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)

_DOMAIN_BY_CATEGORY = {
    "FINANCIAL": DecisionEvaluationDomain.FINANCIAL,
    "LEGAL": DecisionEvaluationDomain.LEGAL,
    "TECHNICAL": DecisionEvaluationDomain.TECHNICAL,
    "EXPERIENCE": DecisionEvaluationDomain.EXPERIENCE,
    "DOCUMENTARY": DecisionEvaluationDomain.DOCUMENTARY,
    "ORGANIZATIONAL": DecisionEvaluationDomain.ORGANIZATIONAL,
    "RISK_AND_INELIGIBILITY": DecisionEvaluationDomain.RISK_AND_INELIGIBILITY,
}


def finding(
    category: str = "FINANCIAL",
    outcome: DecisionFindingOutcome = DecisionFindingOutcome.COMPLIES,
    **overrides,
) -> DecisionInputFinding:
    values = {
        "id": uuid4(),
        "requirement_id": uuid4(),
        "requirement_stable_key": "a" * 64,
        "category": category,
        "scope": "HABILITATING",
        "modality": "MANDATORY",
        "criticality": "BLOCKING",
        "criticality_basis": "EXPLICIT",
        "subsanability": "UNKNOWN",
        "subsanability_basis": "UNKNOWN",
        "evaluation_domain": _DOMAIN_BY_CATEGORY.get(category, DecisionEvaluationDomain.OTHER),
        "source_type": DecisionFindingSourceType.SYNTHETIC,
        "source_run_id": None,
        "source_result_id": None,
        "outcome": outcome,
        "applicability": DecisionFindingApplicability.MANDATORY,
        "requires_human_review": False,
        "is_blocking": False,
        "is_remediable": False,
        "partner_solvable": False,
        "submission_blocker": False,
        "condition_codes": [],
        "warning_codes": [],
        "evidence_references": [],
    }
    values.update(overrides)
    return DecisionInputFinding(**values)


def decide(findings: list[DecisionInputFinding]):
    coverage = ANALYZER.analyze(findings)
    return ENGINE.decide(
        DecisionContext(
            policy=POLICY, findings=findings, coverage=coverage, effective_at=EFFECTIVE_AT
        )
    )


C = DecisionFindingOutcome.COMPLIES
DNC = DecisionFindingOutcome.DOES_NOT_COMPLY
PART = DecisionFindingOutcome.PARTIAL
UNK = DecisionFindingOutcome.UNKNOWN
NA = DecisionFindingOutcome.NOT_APPLICABLE
CONF = DecisionFindingOutcome.CONFLICTING_EVIDENCE
NE = DecisionFindingOutcome.NOT_EVALUATED


def test_01_full_compliance_produces_go() -> None:
    out = decide([finding(outcome=C), finding("LEGAL", C)])
    assert out.engine_outcome == DecisionOutcome.GO


def test_02_remediable_condition_produces_go_condicionado() -> None:
    out = decide(
        [
            finding(outcome=C),
            finding(
                "LEGAL",
                DNC,
                is_remediable=True,
                condition_codes=["APORTAR_CERTIFICADO_ACTUALIZADO"],
                subsanability="SUBSANABLE",
            ),
        ]
    )
    assert out.engine_outcome == DecisionOutcome.GO_CONDICIONADO
    assert out.conditional_findings


def test_03_partner_solvable_gap_produces_buscar_aliado() -> None:
    out = decide([finding(outcome=C), finding("EXPERIENCE", DNC, partner_solvable=True)])
    assert out.engine_outcome == DecisionOutcome.BUSCAR_ALIADO
    assert out.partner_findings


def test_04_blocking_noncompliance_produces_no_go() -> None:
    out = decide([finding(outcome=DNC)])
    assert out.engine_outcome == DecisionOutcome.NO_GO
    assert out.blocking_findings


def test_05_non_subsanable_mandatory_failure_produces_no_go() -> None:
    out = decide([finding(outcome=DNC, subsanability="NON_SUBSANABLE")])
    assert out.engine_outcome == DecisionOutcome.NO_GO
    assert any(rule.rule_code == "NON_SUBSANABLE_MANDATORY_FAILURE" for rule in out.triggered_rules)


def test_06_explicit_submission_blocker_produces_no_cargar() -> None:
    out = decide([finding("DOCUMENTARY", DNC, submission_blocker=True)])
    assert out.engine_outcome == DecisionOutcome.NO_CARGAR


def test_07_mandatory_not_evaluated_produces_pendiente() -> None:
    out = decide([finding(outcome=C), finding("LEGAL", NE)])
    assert out.engine_outcome == DecisionOutcome.PENDIENTE_INFORMACION


def test_08_unknown_produces_pendiente() -> None:
    out = decide([finding(outcome=UNK)])
    assert out.engine_outcome == DecisionOutcome.PENDIENTE_INFORMACION


def test_09_critical_conflict_produces_pendiente_and_review() -> None:
    out = decide([finding(outcome=CONF)])
    assert out.engine_outcome == DecisionOutcome.PENDIENTE_INFORMACION
    assert out.requires_human_review is True
    assert out.conflicting_findings


def test_10_financial_only_with_legal_not_evaluated_produces_pendiente() -> None:
    out = decide(
        [
            finding(outcome=C, source_type=DecisionFindingSourceType.FINANCIAL_EVALUATION),
            finding("LEGAL", NE, source_type=DecisionFindingSourceType.MISSING_ADAPTER),
        ]
    )
    assert out.engine_outcome == DecisionOutcome.PENDIENTE_INFORMACION
    assert out.unknown_findings


def test_11_optional_failure_does_not_block() -> None:
    out = decide(
        [
            finding(outcome=C),
            finding(
                "TECHNICAL",
                DNC,
                modality="OPTIONAL",
                applicability=DecisionFindingApplicability.OPTIONAL,
            ),
        ]
    )
    assert out.engine_outcome == DecisionOutcome.GO
    assert any(warning.startswith("OPTIONAL_REQUIREMENTS_FAILED") for warning in out.warnings)


def test_12_not_applicable_is_excluded() -> None:
    out = decide(
        [
            finding(outcome=C),
            finding("LEGAL", NA, applicability=DecisionFindingApplicability.NOT_APPLICABLE),
        ]
    )
    assert out.engine_outcome == DecisionOutcome.GO


def test_13_informational_requirement_does_not_block() -> None:
    out = decide(
        [
            finding(outcome=C),
            finding(
                "LEGAL",
                NE,
                criticality="INFORMATIONAL",
                applicability=DecisionFindingApplicability.INFORMATIONAL,
            ),
        ]
    )
    assert out.engine_outcome == DecisionOutcome.GO


def test_14_partial_without_resolution_is_not_positive() -> None:
    out = decide([finding(outcome=PART)])
    assert out.engine_outcome == DecisionOutcome.PENDIENTE_INFORMACION


def test_15_partner_gap_with_missing_information_is_pendiente() -> None:
    out = decide(
        [
            finding("EXPERIENCE", DNC, partner_solvable=True),
            finding("LEGAL", NE),
        ]
    )
    assert out.engine_outcome == DecisionOutcome.PENDIENTE_INFORMACION


def test_16_condition_without_action_codes_is_not_go_condicionado() -> None:
    out = decide([finding(outcome=DNC, is_remediable=True, condition_codes=[])])
    assert out.engine_outcome == DecisionOutcome.PENDIENTE_INFORMACION
    assert any(
        rule.rule_code == "REMEDIABLE_CONDITION_EXISTS" and rule.status.value == "INDETERMINATE"
        for rule in out.rule_evaluations
    )


def test_17_go_impossible_with_pending_critical_review() -> None:
    out = decide([finding(outcome=C, requires_human_review=True)])
    assert out.engine_outcome == DecisionOutcome.PENDIENTE_INFORMACION
    assert out.requires_human_review is True


def test_18_no_go_precedence_over_pendiente() -> None:
    out = decide([finding(outcome=DNC), finding("LEGAL", NE)])
    assert out.engine_outcome == DecisionOutcome.NO_GO


def test_19_no_cargar_precedence_over_no_go() -> None:
    out = decide(
        [
            finding(outcome=DNC),
            finding("DOCUMENTARY", DNC, submission_blocker=True),
        ]
    )
    assert out.engine_outcome == DecisionOutcome.NO_CARGAR


def test_20_same_inputs_same_output() -> None:
    findings = [finding(outcome=C), finding("LEGAL", NE)]
    first = decide(findings)
    second = decide(findings)
    assert first.engine_outcome == second.engine_outcome
    assert first.reason_codes == second.reason_codes
    assert [rule.rule_code for rule in first.triggered_rules] == [
        rule.rule_code for rule in second.triggered_rules
    ]


def test_21_policy_change_changes_digest() -> None:
    manifest = {
        "process_id": "p",
        "requirement_ids": ["r1"],
        "policy_hash": POLICY_HASH,
        "engine_version": "1.0.0",
        "effective_at": "2026-07-01T12:00:00+00:00",
    }
    other = dict(manifest, policy_hash="f" * 64)
    assert stable_decision_digest(manifest) != stable_decision_digest(other)


def test_22_effective_at_is_not_part_of_digest() -> None:
    manifest = {
        "process_id": "p",
        "requirement_ids": ["r1"],
        "policy_hash": POLICY_HASH,
        "engine_version": "1.0.0",
        "effective_at": "2026-07-01T12:00:00+00:00",
    }
    later = dict(manifest, effective_at="2026-08-01T12:00:00+00:00")
    assert stable_decision_digest(manifest) == stable_decision_digest(later)


def test_23_precedence_is_total_and_documented() -> None:
    assert [outcome.value for outcome in POLICY.precedence] == [
        "NO_CARGAR",
        "NO_GO",
        "PENDIENTE_INFORMACION",
        "BUSCAR_ALIADO",
        "GO_CONDICIONADO",
        "GO",
    ]


def test_24_every_outcome_is_reachable() -> None:
    scenarios = {
        DecisionOutcome.GO: [finding(outcome=C)],
        DecisionOutcome.GO_CONDICIONADO: [
            finding(outcome=DNC, is_remediable=True, condition_codes=["X"])
        ],
        DecisionOutcome.BUSCAR_ALIADO: [finding(outcome=DNC, partner_solvable=True)],
        DecisionOutcome.NO_GO: [finding(outcome=DNC)],
        DecisionOutcome.NO_CARGAR: [finding(outcome=DNC, submission_blocker=True)],
        DecisionOutcome.PENDIENTE_INFORMACION: [finding(outcome=UNK)],
    }
    for expected, findings in scenarios.items():
        assert decide(findings).engine_outcome == expected


def test_25_engine_has_no_ai_dependencies() -> None:
    import pliegocheck_api.decision.actions as actions_module
    import pliegocheck_api.decision.coverage as coverage_module
    import pliegocheck_api.decision.engine as engine_module
    import pliegocheck_api.decision.findings as findings_module
    import pliegocheck_api.decision.policy as policy_module
    import pliegocheck_api.decision.rules as rules_module

    for module in (
        engine_module,
        rules_module,
        coverage_module,
        findings_module,
        policy_module,
        actions_module,
    ):
        with open(module.__file__, encoding="utf-8") as source_file:
            source = source_file.read().lower()
        for forbidden in ("openai", "anthropic", "embedding", "llm", "prompt("):
            assert forbidden not in source, f"{module.__name__} contiene {forbidden}"


def test_26_output_has_no_probabilistic_score() -> None:
    out = decide([finding(outcome=C)])
    payload = {
        "reason_codes": [code.value for code in out.reason_codes],
        "warnings": out.warnings,
    }
    text = str(payload).lower()
    for forbidden in ("probability", "score", "confidence"):
        assert forbidden not in text


@pytest.mark.parametrize(
    "uncertain_outcome",
    [UNK, NE, CONF, PART],
)
def test_27_no_false_go_with_uncertainty(uncertain_outcome: DecisionFindingOutcome) -> None:
    out = decide([finding(outcome=C), finding("LEGAL", uncertain_outcome)])
    assert out.engine_outcome != DecisionOutcome.GO
    assert out.engine_outcome != DecisionOutcome.GO_CONDICIONADO
    assert out.engine_outcome != DecisionOutcome.BUSCAR_ALIADO
