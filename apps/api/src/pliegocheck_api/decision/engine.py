"""Motor deterministico de decision preliminar.

Funcion pura: sin I/O, sin base de datos, sin reloj global y sin IA.
Mismos inputs (hallazgos + politica + reloj efectivo) producen misma salida.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from pliegocheck_api.decision.policy import DecisionPolicy
from pliegocheck_api.decision.rules import (
    DEFAULT_RULE_REGISTRY,
    DecisionRuleContext,
    DecisionRuleRegistry,
    DecisionRuleResult,
)
from pliegocheck_schemas import (
    DecisionCoverageSummary,
    DecisionFindingApplicability,
    DecisionFindingOutcome,
    DecisionInputFinding,
    DecisionOutcome,
    DecisionReasonCode,
    DecisionRuleStatus,
)


@dataclass(frozen=True)
class DecisionContext:
    """Entrada completa del motor. Todo explicito; nada global."""

    policy: DecisionPolicy
    findings: list[DecisionInputFinding]
    coverage: DecisionCoverageSummary
    effective_at: datetime
    process_closing_at: datetime | None = None


@dataclass(frozen=True)
class DecisionEngineOutput:
    engine_outcome: DecisionOutcome
    reason_codes: list[DecisionReasonCode]
    triggered_rules: list[DecisionRuleResult]
    rule_evaluations: list[DecisionRuleResult]
    coverage: DecisionCoverageSummary
    blocking_findings: list[UUID] = field(default_factory=list)
    conditional_findings: list[UUID] = field(default_factory=list)
    partner_findings: list[UUID] = field(default_factory=list)
    unknown_findings: list[UUID] = field(default_factory=list)
    conflicting_findings: list[UUID] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    requires_human_review: bool = False


class DeterministicDecisionEngine:
    """Aplica reglas tipadas y precedencia unica de la politica."""

    def __init__(self, rule_registry: DecisionRuleRegistry | None = None) -> None:
        self._registry = rule_registry or DEFAULT_RULE_REGISTRY

    def decide(self, context: DecisionContext) -> DecisionEngineOutput:
        rule_ctx = DecisionRuleContext(
            policy=context.policy,
            findings=context.findings,
            coverage=context.coverage,
            effective_at=context.effective_at,
            process_closing_at=context.process_closing_at,
        )
        evaluations = self._registry.evaluate_all(rule_ctx)
        triggered = [
            result
            for result in evaluations
            if result.status in {DecisionRuleStatus.TRIGGERED, DecisionRuleStatus.INDETERMINATE}
        ]
        suggestions = [
            result.suggested_outcome for result in triggered if result.suggested_outcome is not None
        ]

        by_code = {result.rule_code: result for result in evaluations}
        go_prereqs_met = (
            by_code["ALL_MANDATORY_REQUIREMENTS_COMPLY"].status == DecisionRuleStatus.TRIGGERED
            and by_code["FULL_REQUIRED_COVERAGE"].status == DecisionRuleStatus.TRIGGERED
        )

        reason_codes: list[DecisionReasonCode] = []
        for result in triggered:
            if result.reason_code is not None and result.reason_code not in reason_codes:
                reason_codes.append(result.reason_code)

        if suggestions:
            outcome = min(suggestions, key=context.policy.outcome_rank)
        elif go_prereqs_met:
            outcome = DecisionOutcome.GO
        else:
            # Conservador: sin bloqueos explicitos pero sin cumplimiento
            # completo verificable, nunca un resultado positivo.
            outcome = DecisionOutcome.PENDIENTE_INFORMACION
            if DecisionReasonCode.MANDATORY_REQUIREMENT_UNRESOLVED not in reason_codes:
                reason_codes.append(DecisionReasonCode.MANDATORY_REQUIREMENT_UNRESOLVED)

        warnings = self._warnings(context)
        requires_review = (
            any(finding.requires_human_review for finding in context.findings)
            or by_code["CONFLICTING_CRITICAL_EVIDENCE"].status == DecisionRuleStatus.TRIGGERED
        )

        def finding_ids(code: str) -> list[UUID]:
            result = by_code.get(code)
            return list(result.finding_ids) if result is not None else []

        blocking = sorted(
            set(finding_ids("BLOCKING_NONCOMPLIANCE"))
            | set(finding_ids("NON_SUBSANABLE_MANDATORY_FAILURE"))
            | set(finding_ids("SUBMISSION_BLOCKER_CONFIRMED")),
            key=str,
        )
        unknown = sorted(
            set(finding_ids("MANDATORY_REQUIREMENT_UNKNOWN"))
            | set(finding_ids("MANDATORY_REQUIREMENT_NOT_EVALUATED")),
            key=str,
        )
        return DecisionEngineOutput(
            engine_outcome=outcome,
            reason_codes=reason_codes,
            triggered_rules=triggered,
            rule_evaluations=evaluations,
            coverage=context.coverage,
            blocking_findings=blocking,
            conditional_findings=finding_ids("REMEDIABLE_CONDITION_EXISTS"),
            partner_findings=finding_ids("PARTNER_SOLVABLE_GAP"),
            unknown_findings=unknown,
            conflicting_findings=finding_ids("CONFLICTING_CRITICAL_EVIDENCE"),
            warnings=warnings,
            requires_human_review=requires_review,
        )

    @staticmethod
    def _warnings(context: DecisionContext) -> list[str]:
        warnings: list[str] = []
        optional_failed = sum(
            1
            for finding in context.findings
            if finding.applicability == DecisionFindingApplicability.OPTIONAL
            and finding.outcome == DecisionFindingOutcome.DOES_NOT_COMPLY
        )
        if optional_failed:
            warnings.append(f"OPTIONAL_REQUIREMENTS_FAILED:{optional_failed}")
        missing_adapter_categories = sorted(
            {
                category.category
                for category in context.coverage.categories
                if not category.adapter_available and category.mandatory_total > 0
            }
        )
        for category in missing_adapter_categories:
            warnings.append(f"ADAPTER_NOT_AVAILABLE:{category}")
        return warnings
