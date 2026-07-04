"""Analisis de cobertura mediante conteos claros; nunca un score."""

from __future__ import annotations

from pliegocheck_schemas import (
    DecisionCoverageCategory,
    DecisionCoverageStatus,
    DecisionCoverageSummary,
    DecisionEvaluationDomain,
    DecisionFindingApplicability,
    DecisionFindingOutcome,
    DecisionInputFinding,
)


class DecisionCoverageAnalyzer:
    """Calcula la cobertura de evaluacion por requisito y por categoria."""

    def __init__(self, available_domains: list[DecisionEvaluationDomain]) -> None:
        self._available_domains = set(available_domains)

    def analyze(self, findings: list[DecisionInputFinding]) -> DecisionCoverageSummary:
        mandatory = [
            finding
            for finding in findings
            if finding.applicability == DecisionFindingApplicability.MANDATORY
        ]
        optional = [
            finding
            for finding in findings
            if finding.applicability == DecisionFindingApplicability.OPTIONAL
        ]
        evaluated = [
            finding
            for finding in findings
            if finding.outcome != DecisionFindingOutcome.NOT_EVALUATED
        ]

        def count(outcome: DecisionFindingOutcome) -> int:
            return sum(1 for finding in findings if finding.outcome == outcome)

        return DecisionCoverageSummary(
            requirements_total=len(findings),
            mandatory_applicable_total=len(mandatory),
            optional_total=len(optional),
            evaluated_total=len(evaluated),
            not_evaluated_total=count(DecisionFindingOutcome.NOT_EVALUATED),
            complies_total=count(DecisionFindingOutcome.COMPLIES),
            does_not_comply_total=count(DecisionFindingOutcome.DOES_NOT_COMPLY),
            partial_total=count(DecisionFindingOutcome.PARTIAL),
            unknown_total=count(DecisionFindingOutcome.UNKNOWN),
            not_applicable_total=count(DecisionFindingOutcome.NOT_APPLICABLE),
            conflicting_total=count(DecisionFindingOutcome.CONFLICTING_EVIDENCE),
            blocking_failure_total=sum(
                1
                for finding in mandatory
                if finding.outcome == DecisionFindingOutcome.DOES_NOT_COMPLY
            ),
            remediable_gap_total=sum(
                1
                for finding in mandatory
                if finding.is_remediable
                and finding.outcome
                in {DecisionFindingOutcome.DOES_NOT_COMPLY, DecisionFindingOutcome.PARTIAL}
            ),
            partner_gap_total=sum(1 for finding in mandatory if finding.partner_solvable),
            submission_blocker_total=sum(1 for finding in findings if finding.submission_blocker),
            human_review_pending_total=sum(
                1 for finding in findings if finding.requires_human_review
            ),
            categories=self._categories(findings),
        )

    def _categories(self, findings: list[DecisionInputFinding]) -> list[DecisionCoverageCategory]:
        by_category: dict[str, list[DecisionInputFinding]] = {}
        for finding in findings:
            by_category.setdefault(finding.category, []).append(finding)
        categories: list[DecisionCoverageCategory] = []
        for category in sorted(by_category):
            items = by_category[category]
            mandatory_total = sum(
                1
                for finding in items
                if finding.applicability == DecisionFindingApplicability.MANDATORY
            )
            evaluated_total = sum(
                1 for finding in items if finding.outcome != DecisionFindingOutcome.NOT_EVALUATED
            )
            not_evaluated_total = len(items) - evaluated_total
            outcomes: dict[str, int] = {}
            for finding in items:
                outcomes[finding.outcome.value] = outcomes.get(finding.outcome.value, 0) + 1
            adapter_available = items[0].evaluation_domain in self._available_domains
            categories.append(
                DecisionCoverageCategory(
                    category=category,
                    requirements_total=len(items),
                    mandatory_total=mandatory_total,
                    evaluated_total=evaluated_total,
                    not_evaluated_total=not_evaluated_total,
                    outcomes=outcomes,
                    adapter_available=adapter_available,
                    coverage_status=self._status(
                        mandatory_total=mandatory_total,
                        evaluated_total=evaluated_total,
                        total=len(items),
                    ),
                )
            )
        return categories

    @staticmethod
    def _status(
        *, mandatory_total: int, evaluated_total: int, total: int
    ) -> DecisionCoverageStatus:
        if mandatory_total == 0:
            return DecisionCoverageStatus.NOT_REQUIRED
        if evaluated_total == 0:
            return DecisionCoverageStatus.MISSING
        if evaluated_total < total:
            return DecisionCoverageStatus.PARTIAL
        return DecisionCoverageStatus.COMPLETE
