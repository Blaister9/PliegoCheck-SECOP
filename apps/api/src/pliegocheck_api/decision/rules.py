"""Reglas tipadas y versionadas del motor de decision.

Cada regla es codigo tipado que consume el contexto y produce un resultado
trazable con hechos, requisitos y hallazgos. La politica aporta parametros;
las reglas nunca evaluan expresiones dinamicas.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from pliegocheck_api.decision.policy import DecisionPolicy
from pliegocheck_schemas import (
    DecisionCoverageStatus,
    DecisionCoverageSummary,
    DecisionFindingApplicability,
    DecisionFindingOutcome,
    DecisionInputFinding,
    DecisionOutcome,
    DecisionReasonCode,
    DecisionRuleStatus,
)

RULES_SEMANTIC_VERSION = "1.0.0"


@dataclass(frozen=True)
class DecisionRuleContext:
    """Entrada inmutable de las reglas. Sin I/O ni reloj global."""

    policy: DecisionPolicy
    findings: list[DecisionInputFinding]
    coverage: DecisionCoverageSummary
    effective_at: datetime
    process_closing_at: datetime | None

    @property
    def mandatory_findings(self) -> list[DecisionInputFinding]:
        return [
            finding
            for finding in self.findings
            if finding.applicability == DecisionFindingApplicability.MANDATORY
        ]


@dataclass(frozen=True)
class DecisionRuleResult:
    rule_code: str
    rule_version: str
    priority: int
    status: DecisionRuleStatus
    suggested_outcome: DecisionOutcome | None
    reason_code: DecisionReasonCode | None
    fact_payload: dict[str, object] = field(default_factory=dict)
    requirement_ids: list[UUID] = field(default_factory=list)
    finding_ids: list[UUID] = field(default_factory=list)


@dataclass(frozen=True)
class DecisionRule:
    rule_code: str
    semantic_version: str
    description: str
    priority: int
    evaluate: Callable[[DecisionRuleContext], DecisionRuleResult]


def _result(
    rule: DecisionRule,
    *,
    status: DecisionRuleStatus,
    suggested_outcome: DecisionOutcome | None = None,
    reason_code: DecisionReasonCode | None = None,
    matched: list[DecisionInputFinding] | None = None,
    facts: dict[str, object] | None = None,
) -> DecisionRuleResult:
    matched = matched or []
    return DecisionRuleResult(
        rule_code=rule.rule_code,
        rule_version=rule.semantic_version,
        priority=rule.priority,
        status=status,
        suggested_outcome=suggested_outcome,
        reason_code=reason_code,
        fact_payload={"matched_count": len(matched), **(facts or {})},
        requirement_ids=[finding.requirement_id for finding in matched],
        finding_ids=[finding.id for finding in matched],
    )


def _rule(
    code: str, description: str, priority: int
) -> Callable[[Callable[[DecisionRule, DecisionRuleContext], DecisionRuleResult]], DecisionRule]:
    def wrap(
        fn: Callable[[DecisionRule, DecisionRuleContext], DecisionRuleResult],
    ) -> DecisionRule:
        def evaluate(ctx: DecisionRuleContext) -> DecisionRuleResult:
            return fn(_RULE_BY_CODE[code], ctx)

        rule = DecisionRule(
            rule_code=code,
            semantic_version=RULES_SEMANTIC_VERSION,
            description=description,
            priority=priority,
            evaluate=evaluate,
        )
        _RULE_BY_CODE[code] = rule
        return rule

    return wrap


_RULE_BY_CODE: dict[str, DecisionRule] = {}


@_rule(
    "SUBMISSION_BLOCKER_CONFIRMED",
    "Un bloqueo operativo explicito impide presentar la oferta.",
    10,
)
def _submission_blocker(rule: DecisionRule, ctx: DecisionRuleContext) -> DecisionRuleResult:
    matched = [finding for finding in ctx.mandatory_findings if finding.submission_blocker]
    if not matched:
        return _result(rule, status=DecisionRuleStatus.NOT_TRIGGERED)
    return _result(
        rule,
        status=DecisionRuleStatus.TRIGGERED,
        suggested_outcome=DecisionOutcome.NO_CARGAR,
        reason_code=DecisionReasonCode.SUBMISSION_BLOCKER_CONFIRMED,
        matched=matched,
    )


@_rule(
    "NON_SUBSANABLE_MANDATORY_FAILURE",
    "Incumplimiento obligatorio confirmado y no subsanable.",
    20,
)
def _non_subsanable_failure(rule: DecisionRule, ctx: DecisionRuleContext) -> DecisionRuleResult:
    matched = [
        finding
        for finding in ctx.mandatory_findings
        if finding.outcome == DecisionFindingOutcome.DOES_NOT_COMPLY
        and finding.subsanability == "NON_SUBSANABLE"
        and not finding.partner_solvable
    ]
    if not matched:
        return _result(rule, status=DecisionRuleStatus.NOT_TRIGGERED)
    return _result(
        rule,
        status=DecisionRuleStatus.TRIGGERED,
        suggested_outcome=DecisionOutcome.NO_GO,
        reason_code=DecisionReasonCode.NON_SUBSANABLE_REQUIREMENT_FAILED,
        matched=matched,
    )


@_rule(
    "BLOCKING_NONCOMPLIANCE",
    "Incumplimiento obligatorio bloqueante confirmado sin remediacion ni aliado.",
    30,
)
def _blocking_noncompliance(rule: DecisionRule, ctx: DecisionRuleContext) -> DecisionRuleResult:
    blocking = set(ctx.policy.no_go_requirements.criticalities)
    matched = [
        finding
        for finding in ctx.mandatory_findings
        if finding.outcome == DecisionFindingOutcome.DOES_NOT_COMPLY
        and (finding.criticality in blocking or finding.is_blocking)
        and not finding.partner_solvable
        and not finding.is_remediable
    ]
    if not matched:
        return _result(rule, status=DecisionRuleStatus.NOT_TRIGGERED)
    return _result(
        rule,
        status=DecisionRuleStatus.TRIGGERED,
        suggested_outcome=DecisionOutcome.NO_GO,
        reason_code=DecisionReasonCode.BLOCKING_REQUIREMENT_FAILED,
        matched=matched,
        facts={"blocking_criticalities": sorted(blocking)},
    )


@_rule(
    "CONFLICTING_CRITICAL_EVIDENCE",
    "Evidencia contradictoria en requisitos obligatorios.",
    40,
)
def _conflicting_evidence(rule: DecisionRule, ctx: DecisionRuleContext) -> DecisionRuleResult:
    matched = [
        finding
        for finding in ctx.mandatory_findings
        if finding.outcome == DecisionFindingOutcome.CONFLICTING_EVIDENCE
    ]
    if not matched:
        return _result(rule, status=DecisionRuleStatus.NOT_TRIGGERED)
    return _result(
        rule,
        status=DecisionRuleStatus.TRIGGERED,
        suggested_outcome=ctx.policy.conflict_behavior,
        reason_code=DecisionReasonCode.CRITICAL_EVIDENCE_CONFLICT,
        matched=matched,
    )


@_rule(
    "MANDATORY_REQUIREMENT_NOT_EVALUATED",
    "Requisitos obligatorios sin evaluador disponible o sin resultado.",
    50,
)
def _mandatory_not_evaluated(rule: DecisionRule, ctx: DecisionRuleContext) -> DecisionRuleResult:
    matched = [
        finding
        for finding in ctx.mandatory_findings
        if finding.outcome == DecisionFindingOutcome.NOT_EVALUATED
    ]
    if not matched:
        return _result(rule, status=DecisionRuleStatus.NOT_TRIGGERED)
    return _result(
        rule,
        status=DecisionRuleStatus.TRIGGERED,
        suggested_outcome=DecisionOutcome.PENDIENTE_INFORMACION,
        reason_code=DecisionReasonCode.MANDATORY_REQUIREMENT_NOT_EVALUATED,
        matched=matched,
        facts={
            "categories": sorted({finding.category for finding in matched}),
        },
    )


@_rule(
    "MANDATORY_REQUIREMENT_UNKNOWN",
    "Requisitos obligatorios con resultado UNKNOWN.",
    60,
)
def _mandatory_unknown(rule: DecisionRule, ctx: DecisionRuleContext) -> DecisionRuleResult:
    matched = [
        finding
        for finding in ctx.mandatory_findings
        if finding.outcome == DecisionFindingOutcome.UNKNOWN
    ]
    if not matched:
        return _result(rule, status=DecisionRuleStatus.NOT_TRIGGERED)
    return _result(
        rule,
        status=DecisionRuleStatus.TRIGGERED,
        suggested_outcome=ctx.policy.unknown_behavior,
        reason_code=DecisionReasonCode.MANDATORY_REQUIREMENT_UNKNOWN,
        matched=matched,
    )


@_rule(
    "MANDATORY_REQUIREMENT_PARTIAL",
    "Requisitos obligatorios PARTIAL sin condicion de remediacion resuelta.",
    70,
)
def _mandatory_partial(rule: DecisionRule, ctx: DecisionRuleContext) -> DecisionRuleResult:
    matched = [
        finding
        for finding in ctx.mandatory_findings
        if finding.outcome == DecisionFindingOutcome.PARTIAL
        and not (finding.is_remediable and finding.condition_codes)
        and not finding.partner_solvable
    ]
    if not matched:
        return _result(rule, status=DecisionRuleStatus.NOT_TRIGGERED)
    return _result(
        rule,
        status=DecisionRuleStatus.TRIGGERED,
        suggested_outcome=ctx.policy.partial_behavior,
        reason_code=DecisionReasonCode.MANDATORY_REQUIREMENT_PARTIAL,
        matched=matched,
    )


@_rule(
    "HUMAN_REVIEW_REQUIRED",
    "Hallazgos obligatorios con revision humana pendiente.",
    80,
)
def _human_review_required(rule: DecisionRule, ctx: DecisionRuleContext) -> DecisionRuleResult:
    matched = [finding for finding in ctx.mandatory_findings if finding.requires_human_review]
    if not matched:
        return _result(rule, status=DecisionRuleStatus.NOT_TRIGGERED)
    blocks = ctx.policy.positive_review_requirements
    suggested = (
        DecisionOutcome.PENDIENTE_INFORMACION
        if blocks.block_positive_outcomes_on_pending_critical_review
        else None
    )
    return _result(
        rule,
        status=DecisionRuleStatus.TRIGGERED,
        suggested_outcome=suggested,
        reason_code=DecisionReasonCode.HUMAN_REVIEW_PENDING,
        matched=matched,
    )


@_rule(
    "PARTNER_SOLVABLE_GAP",
    "Brechas confirmadas explicitamente como resolubles mediante aliado.",
    90,
)
def _partner_solvable_gap(rule: DecisionRule, ctx: DecisionRuleContext) -> DecisionRuleResult:
    matched = [
        finding
        for finding in ctx.mandatory_findings
        if finding.partner_solvable
        and finding.outcome
        in {DecisionFindingOutcome.DOES_NOT_COMPLY, DecisionFindingOutcome.PARTIAL}
    ]
    if not matched:
        return _result(rule, status=DecisionRuleStatus.NOT_TRIGGERED)
    return _result(
        rule,
        status=DecisionRuleStatus.TRIGGERED,
        suggested_outcome=DecisionOutcome.BUSCAR_ALIADO,
        reason_code=DecisionReasonCode.PARTNER_SOLVABLE_GAP_CONFIRMED,
        matched=matched,
    )


@_rule(
    "REMEDIABLE_CONDITION_EXISTS",
    "Brechas marcadas explicitamente como remediables con condicion concreta.",
    100,
)
def _remediable_condition(rule: DecisionRule, ctx: DecisionRuleContext) -> DecisionRuleResult:
    remediable = [
        finding
        for finding in ctx.mandatory_findings
        if finding.is_remediable
        and not finding.partner_solvable
        and finding.outcome
        in {DecisionFindingOutcome.DOES_NOT_COMPLY, DecisionFindingOutcome.PARTIAL}
    ]
    if not remediable:
        return _result(rule, status=DecisionRuleStatus.NOT_TRIGGERED)
    without_condition = [finding for finding in remediable if not finding.condition_codes]
    if without_condition:
        # Remediable sin condicion concreta: no hay GO_CONDICIONADO posible.
        return _result(
            rule,
            status=DecisionRuleStatus.INDETERMINATE,
            suggested_outcome=DecisionOutcome.PENDIENTE_INFORMACION,
            reason_code=DecisionReasonCode.REMEDIABLE_CONDITION_PENDING,
            matched=without_condition,
        )
    return _result(
        rule,
        status=DecisionRuleStatus.TRIGGERED,
        suggested_outcome=DecisionOutcome.GO_CONDICIONADO,
        reason_code=DecisionReasonCode.REMEDIABLE_CONDITION_PENDING,
        matched=remediable,
        facts={
            "condition_codes": sorted(
                {code for finding in remediable for code in finding.condition_codes}
            )
        },
    )


@_rule(
    "ALL_MANDATORY_REQUIREMENTS_COMPLY",
    "Todos los requisitos obligatorios aplicables cumplen.",
    110,
)
def _all_mandatory_comply(rule: DecisionRule, ctx: DecisionRuleContext) -> DecisionRuleResult:
    mandatory = ctx.mandatory_findings
    if not mandatory:
        return _result(rule, status=DecisionRuleStatus.NOT_APPLICABLE)
    if all(finding.outcome == DecisionFindingOutcome.COMPLIES for finding in mandatory):
        return _result(
            rule,
            status=DecisionRuleStatus.TRIGGERED,
            reason_code=DecisionReasonCode.ALL_MANDATORY_REQUIREMENTS_COMPLY,
            matched=mandatory,
        )
    return _result(rule, status=DecisionRuleStatus.NOT_TRIGGERED)


@_rule(
    "FULL_REQUIRED_COVERAGE",
    "Cobertura completa: ningun requisito obligatorio quedo sin evaluar.",
    120,
)
def _full_required_coverage(rule: DecisionRule, ctx: DecisionRuleContext) -> DecisionRuleResult:
    mandatory_not_evaluated = [
        finding
        for finding in ctx.mandatory_findings
        if finding.outcome == DecisionFindingOutcome.NOT_EVALUATED
    ]
    incomplete_categories = [
        category.category
        for category in ctx.coverage.categories
        if category.coverage_status
        in {DecisionCoverageStatus.MISSING, DecisionCoverageStatus.PARTIAL}
    ]
    if mandatory_not_evaluated or incomplete_categories:
        return _result(
            rule,
            status=DecisionRuleStatus.NOT_TRIGGERED,
            matched=mandatory_not_evaluated,
            facts={"incomplete_categories": incomplete_categories},
        )
    return _result(
        rule,
        status=DecisionRuleStatus.TRIGGERED,
        reason_code=DecisionReasonCode.FULL_MANDATORY_COVERAGE,
        facts={"incomplete_categories": []},
    )


class DecisionRuleRegistry:
    """Registro ordenado de las reglas activas del motor."""

    def __init__(self, rules: list[DecisionRule] | None = None) -> None:
        self._rules = sorted(
            rules if rules is not None else list(_RULE_BY_CODE.values()),
            key=lambda rule: rule.priority,
        )

    @property
    def rules(self) -> list[DecisionRule]:
        return list(self._rules)

    def evaluate_all(self, ctx: DecisionRuleContext) -> list[DecisionRuleResult]:
        return [rule.evaluate(ctx) for rule in self._rules]


DEFAULT_RULE_REGISTRY = DecisionRuleRegistry()
