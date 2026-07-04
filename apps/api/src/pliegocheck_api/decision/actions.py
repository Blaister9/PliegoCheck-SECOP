"""Generacion deterministica de acciones requeridas desde reglas disparadas.

Sin IA y sin fechas inventadas: ``due_at`` queda vacio porque hoy no existe
una fuente explicita para derivarlo.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pliegocheck_api.decision.engine import DecisionEngineOutput
from pliegocheck_schemas import (
    DecisionActionPriority,
    DecisionActionType,
    DecisionEvaluationDomain,
    DecisionInputFinding,
)

_RULE_ACTION_MAP: dict[str, tuple[DecisionActionType, DecisionActionPriority, str]] = {
    "SUBMISSION_BLOCKER_CONFIRMED": (
        DecisionActionType.DO_NOT_SUBMIT,
        DecisionActionPriority.CRITICAL,
        "ACTION_DO_NOT_SUBMIT",
    ),
    "NON_SUBSANABLE_MANDATORY_FAILURE": (
        DecisionActionType.REVIEW_REQUIREMENT,
        DecisionActionPriority.CRITICAL,
        "ACTION_REVIEW_NON_SUBSANABLE_FAILURE",
    ),
    "BLOCKING_NONCOMPLIANCE": (
        DecisionActionType.REVIEW_REQUIREMENT,
        DecisionActionPriority.CRITICAL,
        "ACTION_REVIEW_BLOCKING_FAILURE",
    ),
    "CONFLICTING_CRITICAL_EVIDENCE": (
        DecisionActionType.RESOLVE_CONFLICT,
        DecisionActionPriority.HIGH,
        "ACTION_RESOLVE_EVIDENCE_CONFLICT",
    ),
    "MANDATORY_REQUIREMENT_NOT_EVALUATED": (
        DecisionActionType.COMPLETE_MANDATORY_EVALUATION,
        DecisionActionPriority.HIGH,
        "ACTION_COMPLETE_MANDATORY_EVALUATION",
    ),
    "MANDATORY_REQUIREMENT_UNKNOWN": (
        DecisionActionType.PROVIDE_INFORMATION,
        DecisionActionPriority.HIGH,
        "ACTION_PROVIDE_MISSING_INFORMATION",
    ),
    "MANDATORY_REQUIREMENT_PARTIAL": (
        DecisionActionType.PROVIDE_INFORMATION,
        DecisionActionPriority.MEDIUM,
        "ACTION_RESOLVE_PARTIAL_REQUIREMENT",
    ),
    "HUMAN_REVIEW_REQUIRED": (
        DecisionActionType.REVIEW_EVIDENCE,
        DecisionActionPriority.HIGH,
        "ACTION_COMPLETE_HUMAN_REVIEW",
    ),
    "PARTNER_SOLVABLE_GAP": (
        DecisionActionType.SEEK_PARTNER,
        DecisionActionPriority.HIGH,
        "ACTION_SEEK_PARTNER",
    ),
    "REMEDIABLE_CONDITION_EXISTS": (
        DecisionActionType.CONFIRM_SUBSANABILITY,
        DecisionActionPriority.HIGH,
        "ACTION_FULFILL_REMEDIATION_CONDITION",
    ),
}


def build_action_payloads(
    output: DecisionEngineOutput,
    findings_by_id: dict[UUID, DecisionInputFinding],
) -> list[dict[str, Any]]:
    """Una accion por regla disparada que requiere trabajo del usuario."""
    payloads: list[dict[str, Any]] = []
    for result in output.triggered_rules:
        mapping = _RULE_ACTION_MAP.get(result.rule_code)
        if mapping is None or not result.finding_ids:
            continue
        action_type, priority, title_code = mapping
        matched = [
            findings_by_id[finding_id]
            for finding_id in result.finding_ids
            if finding_id in findings_by_id
        ]
        if result.rule_code == "MANDATORY_REQUIREMENT_UNKNOWN" and any(
            finding.evaluation_domain == DecisionEvaluationDomain.FINANCIAL for finding in matched
        ):
            action_type = DecisionActionType.CORRECT_FINANCIAL_GAP
            title_code = "ACTION_CORRECT_FINANCIAL_GAP"
        parameters: dict[str, Any] = {
            "rule_code": result.rule_code,
            "categories": sorted({finding.category for finding in matched}),
        }
        condition_codes = sorted({code for finding in matched for code in finding.condition_codes})
        if condition_codes:
            parameters["condition_codes"] = condition_codes
        payloads.append(
            {
                "action_type": action_type.value,
                "priority": priority.value,
                "title_code": title_code,
                "description_code": f"{title_code}_DESCRIPTION",
                "parameters": parameters,
                "requirement_ids": [str(item) for item in result.requirement_ids],
                "finding_ids": [str(item) for item in result.finding_ids],
                "due_at": None,
            }
        )
    return payloads
