"""Hallazgo canonico de entrada y adaptadores de evaluacion.

Los adaptadores transforman resultados de evaluadores especializados en
``DecisionInputFinding`` sin reinterpretar calculos ni inventar propiedades.
Los requisitos obligatorios sin adaptador quedan ``NOT_EVALUATED``.
"""

from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID, uuid4

from pliegocheck_schemas import (
    DecisionEvaluationDomain,
    DecisionFindingApplicability,
    DecisionFindingOutcome,
    DecisionFindingSourceType,
    DecisionInputFinding,
    FinancialEvaluationResultStatus,
    FinancialEvaluationReviewStatus,
    RequirementCategory,
    RequirementCriticality,
    RequirementModality,
    RequirementScope,
)

CATEGORY_TO_DOMAIN: dict[str, DecisionEvaluationDomain] = {
    RequirementCategory.FINANCIAL.value: DecisionEvaluationDomain.FINANCIAL,
    RequirementCategory.LEGAL.value: DecisionEvaluationDomain.LEGAL,
    RequirementCategory.EXPERIENCE.value: DecisionEvaluationDomain.EXPERIENCE,
    RequirementCategory.TECHNICAL.value: DecisionEvaluationDomain.TECHNICAL,
    RequirementCategory.WORKFORCE.value: DecisionEvaluationDomain.WORKFORCE,
    RequirementCategory.DOCUMENTARY.value: DecisionEvaluationDomain.DOCUMENTARY,
    RequirementCategory.GUARANTEE.value: DecisionEvaluationDomain.GUARANTEE,
    RequirementCategory.SCHEDULE.value: DecisionEvaluationDomain.SCHEDULE,
    RequirementCategory.ECONOMIC.value: DecisionEvaluationDomain.ECONOMIC,
    RequirementCategory.OPERATIONAL.value: DecisionEvaluationDomain.OPERATIONAL,
    RequirementCategory.RISK_AND_INELIGIBILITY.value: (
        DecisionEvaluationDomain.RISK_AND_INELIGIBILITY
    ),
    RequirementCategory.ORGANIZATIONAL.value: DecisionEvaluationDomain.ORGANIZATIONAL,
}

_FINANCIAL_TO_FINDING_OUTCOME: dict[str, DecisionFindingOutcome] = {
    FinancialEvaluationResultStatus.COMPLIES.value: DecisionFindingOutcome.COMPLIES,
    FinancialEvaluationResultStatus.DOES_NOT_COMPLY.value: DecisionFindingOutcome.DOES_NOT_COMPLY,
    FinancialEvaluationResultStatus.PARTIAL.value: DecisionFindingOutcome.PARTIAL,
    FinancialEvaluationResultStatus.UNKNOWN.value: DecisionFindingOutcome.UNKNOWN,
    FinancialEvaluationResultStatus.NOT_APPLICABLE.value: DecisionFindingOutcome.NOT_APPLICABLE,
    FinancialEvaluationResultStatus.CONFLICTING_EVIDENCE.value: (
        DecisionFindingOutcome.CONFLICTING_EVIDENCE
    ),
}


def domain_for_category(category: str) -> DecisionEvaluationDomain:
    return CATEGORY_TO_DOMAIN.get(category, DecisionEvaluationDomain.OTHER)


def applicability_for_requirement(
    requirement: Any, outcome: DecisionFindingOutcome
) -> DecisionFindingApplicability:
    """Determina la aplicabilidad de forma conservadora y documentada.

    - ``NOT_APPLICABLE`` confirmado por el evaluador excluye el requisito.
    - Requisitos informativos (criticidad o alcance) no bloquean.
    - ``OPTIONAL`` explicito es opcional.
    - ``MANDATORY``, ``CONDITIONAL``, ``PROHIBITED`` y ``UNKNOWN`` se tratan
      como obligatorios: la duda nunca relaja un requisito.
    """
    if outcome == DecisionFindingOutcome.NOT_APPLICABLE:
        return DecisionFindingApplicability.NOT_APPLICABLE
    if (
        requirement.criticality == RequirementCriticality.INFORMATIONAL.value
        or requirement.scope == RequirementScope.INFORMATIONAL.value
    ):
        return DecisionFindingApplicability.INFORMATIONAL
    if requirement.modality == RequirementModality.OPTIONAL.value:
        return DecisionFindingApplicability.OPTIONAL
    return DecisionFindingApplicability.MANDATORY


def _base_finding_kwargs(requirement: Any) -> dict[str, Any]:
    return {
        "id": uuid4(),
        "requirement_id": requirement.id,
        "requirement_stable_key": requirement.stable_key,
        "category": requirement.category,
        "scope": requirement.scope,
        "modality": requirement.modality,
        "criticality": requirement.criticality,
        "criticality_basis": requirement.criticality_basis,
        "subsanability": requirement.subsanability,
        "subsanability_basis": requirement.subsanability_basis,
        "evaluation_domain": domain_for_category(requirement.category),
    }


class DecisionEvaluationAdapter(Protocol):
    """Interfaz de adaptadores de evaluacion especializada."""

    domain: DecisionEvaluationDomain

    def supports(self, requirement: Any) -> bool: ...

    def collect_findings(
        self, *, requirements: list[Any], context: dict[str, Any]
    ) -> list[DecisionInputFinding]: ...


class FinancialDecisionEvaluationAdapter:
    """Transforma resultados financieros en hallazgos canonicos.

    No reinterpreta calculos, no eleva evidencia declarada a verificada y no
    marca brechas como aliables ni remediables: el evaluador financiero actual
    no produce esas propiedades (``partner_solvable=False``,
    ``is_remediable=False``, ``submission_blocker=False``).
    """

    domain = DecisionEvaluationDomain.FINANCIAL

    def supports(self, requirement: Any) -> bool:
        return bool(requirement.category == RequirementCategory.FINANCIAL.value)

    def collect_findings(
        self, *, requirements: list[Any], context: dict[str, Any]
    ) -> list[DecisionInputFinding]:
        results_by_requirement: dict[UUID, Any] = context["financial_results_by_requirement"]
        financial_run_id: UUID = context["financial_evaluation_run_id"]
        findings: list[DecisionInputFinding] = []
        for requirement in requirements:
            if not self.supports(requirement):
                continue
            result = results_by_requirement.get(requirement.id)
            if result is None:
                continue
            findings.append(self._to_finding(requirement, result, financial_run_id))
        return findings

    def _to_finding(
        self, requirement: Any, result: Any, financial_run_id: UUID
    ) -> DecisionInputFinding:
        effective_status = result.status
        review_status = result.review_status
        requires_review = bool(result.requires_human_review)
        if (
            review_status == FinancialEvaluationReviewStatus.OVERRIDDEN.value
            and result.reviewed_status
        ):
            effective_status = result.reviewed_status
            requires_review = False
        elif review_status == FinancialEvaluationReviewStatus.CONFIRMED.value:
            requires_review = False
        elif review_status == FinancialEvaluationReviewStatus.REJECTED.value:
            requires_review = True
        outcome = _FINANCIAL_TO_FINDING_OUTCOME.get(
            effective_status, DecisionFindingOutcome.UNKNOWN
        )
        evidence_refs = result.evidence_refs if isinstance(result.evidence_refs, dict) else {}
        references = [
            {"type": "company_evidence_link", "id": str(link.get("id"))}
            for link in evidence_refs.get("links", [])
            if isinstance(link, dict) and link.get("id")
        ]
        references.append({"type": "financial_evaluation_result", "id": str(result.id)})
        warning_codes: list[str] = []
        explanation_parameters = (
            result.explanation_parameters if isinstance(result.explanation_parameters, dict) else {}
        )
        usability = explanation_parameters.get("usability")
        if usability and usability != "VERIFIED":
            warning_codes.append(f"EVIDENCE_{usability}")
        return DecisionInputFinding(
            **_base_finding_kwargs(requirement),
            source_type=DecisionFindingSourceType.FINANCIAL_EVALUATION,
            source_run_id=financial_run_id,
            source_result_id=result.id,
            outcome=outcome,
            applicability=applicability_for_requirement(requirement, outcome),
            evidence_quality=str(usability) if usability else None,
            review_status=review_status,
            requires_human_review=requires_review,
            is_blocking=False,
            is_remediable=False,
            partner_solvable=False,
            submission_blocker=False,
            condition_codes=[],
            warning_codes=warning_codes,
            evidence_references=references,
        )


def not_evaluated_finding(requirement: Any) -> DecisionInputFinding:
    """Hallazgo NOT_EVALUATED para requisitos sin adaptador o sin resultado."""
    outcome = DecisionFindingOutcome.NOT_EVALUATED
    return DecisionInputFinding(
        **_base_finding_kwargs(requirement),
        source_type=DecisionFindingSourceType.MISSING_ADAPTER,
        source_run_id=None,
        source_result_id=None,
        outcome=outcome,
        applicability=applicability_for_requirement(requirement, outcome),
        evidence_quality=None,
        review_status=None,
        requires_human_review=False,
        is_blocking=False,
        is_remediable=False,
        partner_solvable=False,
        submission_blocker=False,
        condition_codes=[],
        warning_codes=["ADAPTER_NOT_AVAILABLE"],
        evidence_references=[],
    )


class DecisionAdapterRegistry:
    """Registro de adaptadores disponibles por dominio."""

    def __init__(self, adapters: list[Any] | None = None) -> None:
        self._adapters = (
            adapters if adapters is not None else [FinancialDecisionEvaluationAdapter()]
        )

    @property
    def adapters(self) -> list[Any]:
        return list(self._adapters)

    def available_domains(self) -> list[DecisionEvaluationDomain]:
        return [adapter.domain for adapter in self._adapters]

    def adapter_for(self, requirement: Any) -> Any | None:
        for adapter in self._adapters:
            if adapter.supports(requirement):
                return adapter
        return None

    def collect_all_findings(
        self, *, requirements: list[Any], context: dict[str, Any]
    ) -> list[DecisionInputFinding]:
        """Ejecuta los adaptadores y completa NOT_EVALUATED para el resto."""
        findings: list[DecisionInputFinding] = []
        covered: set[UUID] = set()
        for adapter in self._adapters:
            adapter_findings = adapter.collect_findings(requirements=requirements, context=context)
            findings.extend(adapter_findings)
            covered.update(finding.requirement_id for finding in adapter_findings)
        for requirement in requirements:
            if requirement.id not in covered:
                findings.append(not_evaluated_finding(requirement))
        findings.sort(key=lambda finding: (str(finding.requirement_id), str(finding.id)))
        return findings


DEFAULT_ADAPTER_REGISTRY = DecisionAdapterRegistry()
