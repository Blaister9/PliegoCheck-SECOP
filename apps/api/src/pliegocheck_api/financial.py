# mypy: ignore-errors
"""Motor deterministico para evaluar requisitos financieros contra snapshots.

Este modulo no llama modelos de IA. Solo transforma requisitos normalizados,
snapshots publicados de empresa y reglas explicitas en resultados trazables.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from hashlib import sha256
from typing import Any
from uuid import UUID

from pliegocheck_schemas import (
    CompanyEvidenceReviewStatus,
    CompanyEvidenceRole,
    CompanyEvidenceSubjectType,
    CompanyRecordStatus,
    FinancialCalculationStatus,
    FinancialEvaluationResultStatus,
    FinancialExplanationCode,
    FinancialMetricType,
    FinancialMetricUsability,
    FinancialOperator,
    FinancialPeriodPolicy,
    FinancialRuleMappingStatus,
    FinancialRuleSourceBasis,
    FinancialRuleType,
    RequirementCategory,
)

RULE_MAPPING_VERSION = "financial-rule-mapper:1.0.0"
FORMULA_SEMANTIC_VERSION = "1.0.0"

FORMULA_DEFINITIONS: dict[str, dict[str, Any]] = {
    FinancialMetricType.WORKING_CAPITAL.value: {
        "expression": "CURRENT_ASSETS - CURRENT_LIABILITIES",
        "inputs": [
            FinancialMetricType.CURRENT_ASSETS.value,
            FinancialMetricType.CURRENT_LIABILITIES.value,
        ],
        "unit": "COP",
        "scale": Decimal("0.01"),
    },
    FinancialMetricType.LIQUIDITY_RATIO.value: {
        "expression": "CURRENT_ASSETS / CURRENT_LIABILITIES",
        "inputs": [
            FinancialMetricType.CURRENT_ASSETS.value,
            FinancialMetricType.CURRENT_LIABILITIES.value,
        ],
        "unit": "ratio",
        "scale": Decimal("0.000001"),
    },
    FinancialMetricType.DEBT_RATIO.value: {
        "expression": "TOTAL_LIABILITIES / TOTAL_ASSETS",
        "inputs": [
            FinancialMetricType.TOTAL_LIABILITIES.value,
            FinancialMetricType.TOTAL_ASSETS.value,
        ],
        "unit": "ratio",
        "scale": Decimal("0.000001"),
    },
    FinancialMetricType.INTEREST_COVERAGE.value: {
        "expression": "OPERATING_PROFIT / INTEREST_EXPENSE",
        "inputs": [
            FinancialMetricType.OPERATING_PROFIT.value,
            FinancialMetricType.INTEREST_EXPENSE.value,
        ],
        "unit": "ratio",
        "scale": Decimal("0.000001"),
    },
    FinancialMetricType.RETURN_ON_ASSETS.value: {
        "expression": "NET_PROFIT / TOTAL_ASSETS",
        "inputs": [
            FinancialMetricType.NET_PROFIT.value,
            FinancialMetricType.TOTAL_ASSETS.value,
        ],
        "unit": "ratio",
        "scale": Decimal("0.000001"),
    },
    FinancialMetricType.RETURN_ON_EQUITY.value: {
        "expression": "NET_PROFIT / EQUITY",
        "inputs": [
            FinancialMetricType.NET_PROFIT.value,
            FinancialMetricType.EQUITY.value,
        ],
        "unit": "ratio",
        "scale": Decimal("0.000001"),
    },
}

FORMULA_VERSIONS: dict[str, str] = {
    metric_type: FORMULA_SEMANTIC_VERSION for metric_type in FORMULA_DEFINITIONS
}

MONEY_METRICS = {
    FinancialMetricType.CURRENT_ASSETS.value,
    FinancialMetricType.CURRENT_LIABILITIES.value,
    FinancialMetricType.TOTAL_ASSETS.value,
    FinancialMetricType.TOTAL_LIABILITIES.value,
    FinancialMetricType.EQUITY.value,
    FinancialMetricType.REVENUE.value,
    FinancialMetricType.OPERATING_PROFIT.value,
    FinancialMetricType.NET_PROFIT.value,
    FinancialMetricType.INTEREST_EXPENSE.value,
    FinancialMetricType.WORKING_CAPITAL.value,
}

RATIO_METRICS = {
    FinancialMetricType.LIQUIDITY_RATIO.value,
    FinancialMetricType.DEBT_RATIO.value,
    FinancialMetricType.INTEREST_COVERAGE.value,
    FinancialMetricType.RETURN_ON_ASSETS.value,
    FinancialMetricType.RETURN_ON_EQUITY.value,
}


@dataclass(frozen=True)
class MetricResolution:
    value: Decimal | None
    unit: str | None
    currency: str | None
    metric_inputs: list[dict[str, Any]]
    evidence_refs: dict[str, Any]
    usability: str
    calculation: dict[str, Any] | None = None
    error_code: str | None = None


def stable_digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(canonical.encode("utf-8")).hexdigest()


def formula_manifest() -> dict[str, str]:
    return dict(FORMULA_VERSIONS)


def build_input_manifest(
    *,
    process: Any,
    normalization_run: Any,
    snapshot: Any,
    requirements: list[Any],
) -> dict[str, Any]:
    payload = snapshot.payload if isinstance(snapshot.payload, dict) else {}
    periods = payload.get("financial_periods", [])
    period_ids = [str(item.get("id")) for item in periods if isinstance(item, dict)]
    metric_ids: list[str] = []
    for period in periods:
        if not isinstance(period, dict):
            continue
        for metric in period.get("metrics", []):
            if isinstance(metric, dict) and metric.get("id"):
                metric_ids.append(str(metric["id"]))
    evidence_ids = [
        str(link["id"])
        for link in payload.get("evidence_links", [])
        if isinstance(link, dict) and link.get("id")
    ]
    return {
        "process_id": str(process.id),
        "normalization_run_id": str(normalization_run.id),
        "company_id": str(snapshot.company_id),
        "company_profile_snapshot_id": str(snapshot.id),
        "company_snapshot_digest": snapshot.digest,
        "requirement_ids": [str(requirement.id) for requirement in requirements],
        "requirement_stable_keys": [requirement.stable_key for requirement in requirements],
        "financial_period_ids": sorted(period_ids),
        "financial_metric_ids": sorted(metric_ids),
        "evidence_ids": sorted(evidence_ids),
        "formula_versions": formula_manifest(),
        "rule_mapping_version": RULE_MAPPING_VERSION,
    }


def map_financial_requirement(requirement: Any, process: Any) -> dict[str, Any]:
    if requirement.category != RequirementCategory.FINANCIAL.value:
        return _rule_payload(
            requirement,
            rule_type=FinancialRuleType.UNSUPPORTED.value,
            metric_type=None,
            operator=None,
            required_value=None,
            unit=None,
            currency=None,
            period_policy=FinancialPeriodPolicy.UNKNOWN.value,
            period_year=None,
            source_basis=FinancialRuleSourceBasis.UNKNOWN.value,
            mapping_status=FinancialRuleMappingStatus.UNSUPPORTED.value,
            mapping_warnings=["NOT_FINANCIAL_REQUIREMENT"],
            requires_human_review=True,
        )

    text = _requirement_text(requirement)
    normalized = _normalize_text(text)
    metric_type = _detect_metric_type(normalized)
    operator = _detect_operator(normalized)
    value, min_value, max_value, value_warnings = _detect_required_value(requirement, normalized)
    unit, currency = _detect_unit_currency(requirement, normalized, metric_type)
    period_policy, period_year = _detect_period_policy(normalized, process)
    warnings = list(value_warnings)
    mapping_status = FinancialRuleMappingStatus.MAPPED.value
    rule_type = FinancialRuleType.DIRECT_METRIC.value

    if metric_type is None:
        warnings.append("METRIC_TYPE_NOT_DETECTED")
        mapping_status = FinancialRuleMappingStatus.AMBIGUOUS.value
        rule_type = FinancialRuleType.UNSUPPORTED.value
    elif metric_type in FORMULA_DEFINITIONS:
        rule_type = FinancialRuleType.DERIVED_METRIC.value

    if operator is None:
        warnings.append("OPERATOR_NOT_DETECTED")
        mapping_status = FinancialRuleMappingStatus.AMBIGUOUS.value
    if value is None and min_value is None and max_value is None:
        warnings.append("REQUIRED_VALUE_NOT_DETECTED")
        mapping_status = FinancialRuleMappingStatus.AMBIGUOUS.value

    source_basis = (
        FinancialRuleSourceBasis.EXPLICIT_EXPECTED_VALUE.value
        if requirement.expected_value
        else FinancialRuleSourceBasis.EXPLICIT_DESCRIPTION.value
    )
    if mapping_status == FinancialRuleMappingStatus.AMBIGUOUS.value:
        source_basis = FinancialRuleSourceBasis.UNKNOWN.value

    return _rule_payload(
        requirement,
        rule_type=rule_type,
        metric_type=metric_type,
        operator=operator,
        required_value=value,
        required_min_value=min_value,
        required_max_value=max_value,
        unit=unit,
        currency=currency,
        period_policy=period_policy,
        period_year=period_year,
        source_basis=source_basis,
        mapping_status=mapping_status,
        mapping_warnings=warnings,
        requires_human_review=mapping_status != FinancialRuleMappingStatus.MAPPED.value,
    )


def evaluate_financial_requirement(
    *,
    requirement: Any,
    rule: Any,
    snapshot_payload: dict[str, Any],
    process_closing_at: datetime | None,
) -> dict[str, Any]:
    if _get(rule, "mapping_status") != FinancialRuleMappingStatus.MAPPED.value:
        code = (
            FinancialExplanationCode.RULE_UNSUPPORTED
            if _get(rule, "mapping_status") == FinancialRuleMappingStatus.UNSUPPORTED.value
            else FinancialExplanationCode.RULE_AMBIGUOUS
        )
        return _result_payload(
            rule=rule,
            status=FinancialEvaluationResultStatus.UNKNOWN.value,
            explanation_code=code.value,
            explanation_parameters={"warnings": _get(rule, "mapping_warnings") or []},
            requires_human_review=True,
        )

    period, period_error = _resolve_period(snapshot_payload, rule, process_closing_at)
    if period is None:
        return _result_payload(
            rule=rule,
            status=FinancialEvaluationResultStatus.UNKNOWN.value,
            financial_period_id=None,
            explanation_code=(
                FinancialExplanationCode.EVIDENCE_CONFLICT.value
                if period_error == "CONFLICT"
                else FinancialExplanationCode.PERIOD_NOT_RESOLVED.value
            ),
            explanation_parameters={"reason": period_error or "NO_PERIOD"},
            requires_human_review=True,
        )

    metric_type = _get(rule, "metric_type")
    resolution = _resolve_metric(snapshot_payload, period, metric_type)
    if resolution.error_code == FinancialExplanationCode.EVIDENCE_CONFLICT.value:
        return _result_payload(
            rule=rule,
            status=FinancialEvaluationResultStatus.CONFLICTING_EVIDENCE.value,
            financial_period_id=_uuid_or_none(period.get("id")),
            metric_inputs=resolution.metric_inputs,
            evidence_refs=resolution.evidence_refs,
            calculation=resolution.calculation,
            explanation_code=FinancialExplanationCode.EVIDENCE_CONFLICT.value,
            explanation_parameters={"metric_type": metric_type},
            requires_human_review=True,
        )
    if resolution.error_code == FinancialExplanationCode.DIVISION_BY_ZERO.value:
        return _result_payload(
            rule=rule,
            status=FinancialEvaluationResultStatus.UNKNOWN.value,
            financial_period_id=_uuid_or_none(period.get("id")),
            metric_inputs=resolution.metric_inputs,
            evidence_refs=resolution.evidence_refs,
            calculation=resolution.calculation,
            explanation_code=FinancialExplanationCode.DIVISION_BY_ZERO.value,
            explanation_parameters={"metric_type": metric_type},
            requires_human_review=True,
        )
    if resolution.value is None:
        return _result_payload(
            rule=rule,
            status=FinancialEvaluationResultStatus.UNKNOWN.value,
            financial_period_id=_uuid_or_none(period.get("id")),
            metric_inputs=resolution.metric_inputs,
            evidence_refs=resolution.evidence_refs,
            calculation=resolution.calculation,
            explanation_code=FinancialExplanationCode.METRIC_MISSING.value,
            explanation_parameters={"metric_type": metric_type},
            requires_human_review=True,
        )
    if resolution.usability == FinancialMetricUsability.CONFLICTING.value:
        return _result_payload(
            rule=rule,
            status=FinancialEvaluationResultStatus.CONFLICTING_EVIDENCE.value,
            actual_value=resolution.value,
            actual_unit=resolution.unit,
            currency=resolution.currency,
            financial_period_id=_uuid_or_none(period.get("id")),
            metric_inputs=resolution.metric_inputs,
            evidence_refs=resolution.evidence_refs,
            calculation=resolution.calculation,
            explanation_code=FinancialExplanationCode.EVIDENCE_CONFLICT.value,
            explanation_parameters={"metric_type": metric_type},
            requires_human_review=True,
        )

    unit_error = _validate_units(rule, resolution, metric_type)
    if unit_error is not None:
        return _result_payload(
            rule=rule,
            status=FinancialEvaluationResultStatus.UNKNOWN.value,
            actual_value=resolution.value,
            actual_unit=resolution.unit,
            currency=resolution.currency,
            financial_period_id=_uuid_or_none(period.get("id")),
            metric_inputs=resolution.metric_inputs,
            evidence_refs=resolution.evidence_refs,
            calculation=resolution.calculation,
            explanation_code=unit_error,
            explanation_parameters={"metric_type": metric_type},
            requires_human_review=True,
        )
    if resolution.usability in {
        FinancialMetricUsability.DECLARED_ONLY.value,
        FinancialMetricUsability.REJECTED.value,
        FinancialMetricUsability.EXPIRED.value,
        FinancialMetricUsability.MISSING.value,
    }:
        return _result_payload(
            rule=rule,
            status=FinancialEvaluationResultStatus.UNKNOWN.value,
            actual_value=resolution.value,
            actual_unit=resolution.unit,
            currency=resolution.currency,
            financial_period_id=_uuid_or_none(period.get("id")),
            metric_inputs=resolution.metric_inputs,
            evidence_refs=resolution.evidence_refs,
            calculation=resolution.calculation,
            explanation_code=FinancialExplanationCode.DECLARED_VALUE_NOT_VERIFIED.value,
            explanation_parameters={"metric_type": metric_type, "usability": resolution.usability},
            requires_human_review=True,
        )

    comparison_status, explanation_code = _compare(rule, resolution.value)
    return _result_payload(
        rule=rule,
        status=comparison_status,
        actual_value=resolution.value,
        actual_unit=resolution.unit,
        currency=resolution.currency,
        financial_period_id=_uuid_or_none(period.get("id")),
        metric_inputs=resolution.metric_inputs,
        evidence_refs=resolution.evidence_refs,
        calculation=resolution.calculation,
        explanation_code=explanation_code,
        explanation_parameters={
            "metric_type": metric_type,
            "usability": resolution.usability,
        },
        requires_human_review=(
            bool(_get(rule, "requires_human_review"))
            or resolution.usability != FinancialMetricUsability.VERIFIED.value
        ),
    )


def _rule_payload(requirement: Any, **values: Any) -> dict[str, Any]:
    payload = {
        "requirement_id": requirement.id,
        "normalization_run_id": requirement.normalization_run_id,
        "rule_type": values["rule_type"],
        "metric_type": values["metric_type"],
        "operator": values["operator"],
        "required_value": values.get("required_value"),
        "required_min_value": values.get("required_min_value"),
        "required_max_value": values.get("required_max_value"),
        "unit": values.get("unit"),
        "currency": values.get("currency"),
        "period_policy": values["period_policy"],
        "period_year": values.get("period_year"),
        "condition_group": values.get("condition_group") or {},
        "source_basis": values["source_basis"],
        "mapping_status": values["mapping_status"],
        "mapping_warnings": values["mapping_warnings"],
        "requires_human_review": values["requires_human_review"],
        "version": 1,
        "is_manual_override": False,
        "override_reason": None,
    }
    return payload


def _result_payload(
    *,
    rule: Any,
    status: str,
    actual_value: Decimal | None = None,
    actual_unit: str | None = None,
    currency: str | None = None,
    financial_period_id: UUID | None = None,
    metric_inputs: list[dict[str, Any]] | None = None,
    evidence_refs: dict[str, Any] | None = None,
    calculation: dict[str, Any] | None = None,
    explanation_code: str,
    explanation_parameters: dict[str, Any] | None = None,
    requires_human_review: bool = False,
) -> dict[str, Any]:
    return {
        "status": status,
        "metric_type": _get(rule, "metric_type"),
        "operator": _get(rule, "operator"),
        "required_value": _get(rule, "required_value"),
        "required_min_value": _get(rule, "required_min_value"),
        "required_max_value": _get(rule, "required_max_value"),
        "required_unit": _get(rule, "unit"),
        "actual_value": actual_value,
        "actual_unit": actual_unit,
        "currency": currency,
        "financial_period_id": financial_period_id,
        "calculation": calculation,
        "explanation_code": explanation_code,
        "explanation_parameters": explanation_parameters or {},
        "metric_inputs": metric_inputs or [],
        "evidence_refs": evidence_refs or {},
        "requires_human_review": requires_human_review,
    }


def _requirement_text(requirement: Any) -> str:
    expected = requirement.expected_value or {}
    pieces = [
        requirement.description or "",
        requirement.condition_text or "",
        str(expected.get("raw_text") or ""),
        str(expected.get("value") or ""),
        str(expected.get("unit") or ""),
    ]
    return " ".join(piece for piece in pieces if piece)


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _detect_metric_type(text: str) -> str | None:
    checks: list[tuple[str, str]] = [
        ("capital de trabajo", FinancialMetricType.WORKING_CAPITAL.value),
        ("working capital", FinancialMetricType.WORKING_CAPITAL.value),
        ("cobertura de intereses", FinancialMetricType.INTEREST_COVERAGE.value),
        ("interest coverage", FinancialMetricType.INTEREST_COVERAGE.value),
        ("indice de liquidez", FinancialMetricType.LIQUIDITY_RATIO.value),
        ("liquidez", FinancialMetricType.LIQUIDITY_RATIO.value),
        ("liquidity", FinancialMetricType.LIQUIDITY_RATIO.value),
        ("endeudamiento", FinancialMetricType.DEBT_RATIO.value),
        ("debt ratio", FinancialMetricType.DEBT_RATIO.value),
        ("rentabilidad del activo", FinancialMetricType.RETURN_ON_ASSETS.value),
        ("return on assets", FinancialMetricType.RETURN_ON_ASSETS.value),
        (" roa", FinancialMetricType.RETURN_ON_ASSETS.value),
        ("rentabilidad del patrimonio", FinancialMetricType.RETURN_ON_EQUITY.value),
        ("return on equity", FinancialMetricType.RETURN_ON_EQUITY.value),
        (" roe", FinancialMetricType.RETURN_ON_EQUITY.value),
        ("activo corriente", FinancialMetricType.CURRENT_ASSETS.value),
        ("current assets", FinancialMetricType.CURRENT_ASSETS.value),
        ("pasivo corriente", FinancialMetricType.CURRENT_LIABILITIES.value),
        ("current liabilities", FinancialMetricType.CURRENT_LIABILITIES.value),
        ("total activos", FinancialMetricType.TOTAL_ASSETS.value),
        ("activos totales", FinancialMetricType.TOTAL_ASSETS.value),
        ("total assets", FinancialMetricType.TOTAL_ASSETS.value),
        ("total pasivos", FinancialMetricType.TOTAL_LIABILITIES.value),
        ("pasivos totales", FinancialMetricType.TOTAL_LIABILITIES.value),
        ("total liabilities", FinancialMetricType.TOTAL_LIABILITIES.value),
        ("patrimonio", FinancialMetricType.EQUITY.value),
        ("equity", FinancialMetricType.EQUITY.value),
        ("ingresos", FinancialMetricType.REVENUE.value),
        ("revenue", FinancialMetricType.REVENUE.value),
        ("utilidad operacional", FinancialMetricType.OPERATING_PROFIT.value),
        ("operating profit", FinancialMetricType.OPERATING_PROFIT.value),
        ("utilidad neta", FinancialMetricType.NET_PROFIT.value),
        ("net profit", FinancialMetricType.NET_PROFIT.value),
        ("gasto de intereses", FinancialMetricType.INTEREST_EXPENSE.value),
        ("interest expense", FinancialMetricType.INTEREST_EXPENSE.value),
    ]
    haystack = f" {text} "
    for marker, metric_type in checks:
        if marker in haystack:
            return metric_type
    return None


def _detect_operator(text: str) -> str | None:
    if " entre " in f" {text} " and " y " in f" {text} ":
        return FinancialOperator.BETWEEN_INCLUSIVE.value
    checks: list[tuple[str, str]] = [
        (">=", FinancialOperator.GREATER_THAN_OR_EQUAL.value),
        ("mayor o igual", FinancialOperator.GREATER_THAN_OR_EQUAL.value),
        ("minimo", FinancialOperator.GREATER_THAN_OR_EQUAL.value),
        ("no inferior", FinancialOperator.GREATER_THAN_OR_EQUAL.value),
        (">", FinancialOperator.GREATER_THAN.value),
        ("mayor que", FinancialOperator.GREATER_THAN.value),
        ("superior a", FinancialOperator.GREATER_THAN.value),
        ("<=", FinancialOperator.LESS_THAN_OR_EQUAL.value),
        ("menor o igual", FinancialOperator.LESS_THAN_OR_EQUAL.value),
        ("maximo", FinancialOperator.LESS_THAN_OR_EQUAL.value),
        ("no superior", FinancialOperator.LESS_THAN_OR_EQUAL.value),
        ("<", FinancialOperator.LESS_THAN.value),
        ("menor que", FinancialOperator.LESS_THAN.value),
        ("inferior a", FinancialOperator.LESS_THAN.value),
    ]
    for marker, operator in checks:
        if marker in text:
            return operator
    return None


def _detect_required_value(
    requirement: Any, normalized_text: str
) -> tuple[Decimal | None, Decimal | None, Decimal | None, list[str]]:
    expected = requirement.expected_value or {}
    raw = " ".join(
        str(part)
        for part in [expected.get("value"), expected.get("raw_text"), normalized_text]
        if part not in {None, ""}
    )
    percent = "%" in raw or "por ciento" in _normalize_text(raw)
    direct = _to_decimal(expected.get("value"), percent=percent)
    if direct is not None:
        return direct, None, None, []
    numbers = _extract_numbers(raw, percent=percent)
    if (
        _detect_operator(normalized_text)
        in {
            FinancialOperator.BETWEEN_INCLUSIVE.value,
            FinancialOperator.BETWEEN_EXCLUSIVE.value,
        }
        and len(numbers) >= 2
    ):
        return None, numbers[0], numbers[1], []
    if numbers:
        return numbers[0], None, None, []
    return None, None, None, ["NUMERIC_VALUE_NOT_FOUND"]


def _detect_unit_currency(
    requirement: Any, text: str, metric_type: str | None
) -> tuple[str | None, str | None]:
    expected = requirement.expected_value or {}
    unit = expected.get("unit")
    unit_text = _normalize_text(str(unit or ""))
    if metric_type in RATIO_METRICS:
        return "ratio", None
    if metric_type in MONEY_METRICS:
        currency = "COP" if "cop" in text or "$" in text or "pesos" in text else None
        if unit_text in {"cop", "pesos", "peso", "moneda"}:
            currency = "COP"
        return currency, currency
    return str(unit) if unit else None, None


def _detect_period_policy(text: str, process: Any) -> tuple[str, int | None]:
    years = [int(item) for item in re.findall(r"\b(20\d{2}|19\d{2})\b", text)]
    if years:
        return FinancialPeriodPolicy.EXACT_YEAR.value, years[-1]
    if getattr(process, "closing_at", None) is not None:
        return FinancialPeriodPolicy.LATEST_BEFORE_PROCESS_CLOSING.value, None
    return FinancialPeriodPolicy.LATEST_AVAILABLE.value, None


def _resolve_period(
    snapshot_payload: dict[str, Any], rule: Any, process_closing_at: datetime | None
) -> tuple[dict[str, Any] | None, str | None]:
    periods = [
        period
        for period in snapshot_payload.get("financial_periods", [])
        if isinstance(period, dict)
        and period.get("status") not in {CompanyRecordStatus.REJECTED.value}
    ]
    policy = _get(rule, "period_policy")
    year = _get(rule, "period_year")
    if policy == FinancialPeriodPolicy.EXACT_YEAR.value and year is not None:
        candidates = [
            period for period in periods if _parse_date(period.get("period_end")).year == int(year)
        ]
    elif (
        policy == FinancialPeriodPolicy.LATEST_BEFORE_PROCESS_CLOSING.value
        and process_closing_at is not None
    ):
        closing_date = process_closing_at.date()
        candidates = [
            period for period in periods if _parse_date(period.get("period_end")) <= closing_date
        ]
    elif policy in {
        FinancialPeriodPolicy.LATEST_AVAILABLE.value,
        FinancialPeriodPolicy.LATEST_BEFORE_PROCESS_CLOSING.value,
    }:
        candidates = periods
    else:
        return None, "POLICY_UNSUPPORTED"
    if not candidates:
        return None, "NO_CANDIDATE_PERIOD"
    candidates = sorted(
        candidates,
        key=lambda item: _parse_date(item.get("period_end")),
        reverse=True,
    )
    latest_end = _parse_date(candidates[0].get("period_end"))
    latest = [
        period for period in candidates if _parse_date(period.get("period_end")) == latest_end
    ]
    if len({str(period.get("id")) for period in latest}) > 1:
        return None, "CONFLICT"
    return latest[0], None


def _resolve_metric(
    snapshot_payload: dict[str, Any], period: dict[str, Any], metric_type: str
) -> MetricResolution:
    metrics = [
        metric
        for metric in period.get("metrics", [])
        if isinstance(metric, dict) and metric.get("metric_type") == metric_type
    ]
    if metrics:
        return _direct_metric_resolution(snapshot_payload, period, metric_type, metrics)
    if metric_type in FORMULA_DEFINITIONS:
        return _calculated_metric_resolution(snapshot_payload, period, metric_type)
    return MetricResolution(
        value=None,
        unit=None,
        currency=period.get("currency"),
        metric_inputs=[],
        evidence_refs={"links": []},
        usability=FinancialMetricUsability.MISSING.value,
    )


def _direct_metric_resolution(
    snapshot_payload: dict[str, Any],
    period: dict[str, Any],
    metric_type: str,
    metrics: list[dict[str, Any]],
) -> MetricResolution:
    values = {_to_decimal(metric.get("value")) for metric in metrics}
    values.discard(None)
    links = _links_for_subjects(snapshot_payload, [metric.get("id") for metric in metrics])
    metric_inputs = [
        _metric_input(metric, period, _usability(metric, links), links) for metric in metrics
    ]
    if len(values) > 1:
        return MetricResolution(
            value=None,
            unit=metrics[0].get("unit"),
            currency=period.get("currency"),
            metric_inputs=metric_inputs,
            evidence_refs={"links": [_link_ref(link) for link in links]},
            usability=FinancialMetricUsability.CONFLICTING.value,
            error_code=FinancialExplanationCode.EVIDENCE_CONFLICT.value,
        )
    metric = metrics[0]
    usability = _usability(metric, links)
    return MetricResolution(
        value=_to_decimal(metric.get("value")),
        unit=_metric_unit(metric, period, metric_type),
        currency=period.get("currency"),
        metric_inputs=metric_inputs,
        evidence_refs={"links": [_link_ref(link) for link in links]},
        usability=usability,
    )


def _calculated_metric_resolution(
    snapshot_payload: dict[str, Any], period: dict[str, Any], metric_type: str
) -> MetricResolution:
    formula = FORMULA_DEFINITIONS[metric_type]
    input_resolutions: dict[str, MetricResolution] = {
        input_metric: _resolve_metric(snapshot_payload, period, input_metric)
        for input_metric in formula["inputs"]
    }
    metric_inputs: list[dict[str, Any]] = []
    evidence_refs: list[dict[str, Any]] = []
    for resolution in input_resolutions.values():
        metric_inputs.extend(resolution.metric_inputs)
        evidence_refs.extend(resolution.evidence_refs.get("links", []))
    input_values = {
        name: str(resolution.value) if resolution.value is not None else None
        for name, resolution in input_resolutions.items()
    }
    calculation = {
        "financial_period_id": _uuid_or_none(period.get("id")),
        "metric_type": metric_type,
        "formula_name": metric_type,
        "formula_version": FORMULA_SEMANTIC_VERSION,
        "input_values": input_values,
        "raw_result": None,
        "rounded_result": None,
        "unit": formula["unit"],
        "status": FinancialCalculationStatus.COMPLETED.value,
        "warning_codes": [],
    }
    if any(resolution.error_code for resolution in input_resolutions.values()):
        calculation["status"] = FinancialCalculationStatus.CONFLICTING_INPUT.value
        return MetricResolution(
            value=None,
            unit=formula["unit"],
            currency=period.get("currency") if metric_type in MONEY_METRICS else None,
            metric_inputs=metric_inputs,
            evidence_refs={"links": evidence_refs},
            usability=FinancialMetricUsability.CONFLICTING.value,
            calculation=calculation,
            error_code=FinancialExplanationCode.EVIDENCE_CONFLICT.value,
        )
    if any(resolution.value is None for resolution in input_resolutions.values()):
        calculation["status"] = FinancialCalculationStatus.MISSING_INPUT.value
        return MetricResolution(
            value=None,
            unit=formula["unit"],
            currency=period.get("currency") if metric_type in MONEY_METRICS else None,
            metric_inputs=metric_inputs,
            evidence_refs={"links": evidence_refs},
            usability=FinancialMetricUsability.MISSING.value,
            calculation=calculation,
        )
    try:
        value = _calculate(
            metric_type,
            {name: item.value for name, item in input_resolutions.items()},
        )
    except ZeroDivisionError:
        calculation["status"] = FinancialCalculationStatus.DIVISION_BY_ZERO.value
        return MetricResolution(
            value=None,
            unit=formula["unit"],
            currency=period.get("currency") if metric_type in MONEY_METRICS else None,
            metric_inputs=metric_inputs,
            evidence_refs={"links": evidence_refs},
            usability=FinancialMetricUsability.MISSING.value,
            calculation=calculation,
            error_code=FinancialExplanationCode.DIVISION_BY_ZERO.value,
        )
    rounded = value.quantize(formula["scale"], rounding=ROUND_HALF_UP)
    calculation["raw_result"] = value
    calculation["rounded_result"] = rounded
    direct = [
        metric
        for metric in period.get("metrics", [])
        if isinstance(metric, dict) and metric.get("metric_type") == metric_type
    ]
    if direct:
        direct_value = _to_decimal(direct[0].get("value"))
        if direct_value is not None and direct_value != rounded:
            calculation["warning_codes"].append("DECLARED_CALCULATED_VALUE_DIFFER")
    usability = _combined_usability(
        [resolution.usability for resolution in input_resolutions.values()]
    )
    return MetricResolution(
        value=rounded,
        unit=formula["unit"],
        currency=period.get("currency") if metric_type in MONEY_METRICS else None,
        metric_inputs=metric_inputs,
        evidence_refs={"links": evidence_refs},
        usability=usability,
        calculation=calculation,
    )


def _calculate(metric_type: str, values: dict[str, Decimal]) -> Decimal:
    if metric_type == FinancialMetricType.WORKING_CAPITAL.value:
        return (
            values[FinancialMetricType.CURRENT_ASSETS.value]
            - values[FinancialMetricType.CURRENT_LIABILITIES.value]
        )
    if metric_type == FinancialMetricType.LIQUIDITY_RATIO.value:
        denominator = values[FinancialMetricType.CURRENT_LIABILITIES.value]
        if denominator == 0:
            raise ZeroDivisionError
        return values[FinancialMetricType.CURRENT_ASSETS.value] / denominator
    if metric_type == FinancialMetricType.DEBT_RATIO.value:
        denominator = values[FinancialMetricType.TOTAL_ASSETS.value]
        if denominator == 0:
            raise ZeroDivisionError
        return values[FinancialMetricType.TOTAL_LIABILITIES.value] / denominator
    if metric_type == FinancialMetricType.INTEREST_COVERAGE.value:
        denominator = values[FinancialMetricType.INTEREST_EXPENSE.value]
        if denominator == 0:
            raise ZeroDivisionError
        return values[FinancialMetricType.OPERATING_PROFIT.value] / denominator
    if metric_type == FinancialMetricType.RETURN_ON_ASSETS.value:
        denominator = values[FinancialMetricType.TOTAL_ASSETS.value]
        if denominator == 0:
            raise ZeroDivisionError
        return values[FinancialMetricType.NET_PROFIT.value] / denominator
    if metric_type == FinancialMetricType.RETURN_ON_EQUITY.value:
        denominator = values[FinancialMetricType.EQUITY.value]
        if denominator == 0:
            raise ZeroDivisionError
        return values[FinancialMetricType.NET_PROFIT.value] / denominator
    raise ValueError(f"formula no soportada: {metric_type}")


def _links_for_subjects(
    snapshot_payload: dict[str, Any], subject_ids: list[Any]
) -> list[dict[str, Any]]:
    ids = {str(subject_id) for subject_id in subject_ids if subject_id}
    return [
        link
        for link in snapshot_payload.get("evidence_links", [])
        if isinstance(link, dict)
        and link.get("subject_type") == CompanyEvidenceSubjectType.FINANCIAL_METRIC.value
        and str(link.get("subject_id")) in ids
    ]


def _usability(metric: dict[str, Any], links: list[dict[str, Any]]) -> str:
    if any(link.get("evidence_role") == CompanyEvidenceRole.CONFLICTING.value for link in links):
        return FinancialMetricUsability.CONFLICTING.value
    status = metric.get("status")
    if status == CompanyRecordStatus.REJECTED.value:
        return FinancialMetricUsability.REJECTED.value
    if status == CompanyRecordStatus.EXPIRED.value:
        return FinancialMetricUsability.EXPIRED.value
    if status == CompanyRecordStatus.VERIFIED.value or any(
        link.get("review_status") == CompanyEvidenceReviewStatus.VERIFIED.value for link in links
    ):
        return FinancialMetricUsability.VERIFIED.value
    if status == CompanyRecordStatus.SUPPORTED.value or any(
        link.get("review_status") == CompanyEvidenceReviewStatus.SUPPORTED.value for link in links
    ):
        return FinancialMetricUsability.SUPPORTED.value
    return FinancialMetricUsability.DECLARED_ONLY.value


def _combined_usability(values: list[str]) -> str:
    if not values or any(value == FinancialMetricUsability.MISSING.value for value in values):
        return FinancialMetricUsability.MISSING.value
    if any(value == FinancialMetricUsability.CONFLICTING.value for value in values):
        return FinancialMetricUsability.CONFLICTING.value
    if any(value == FinancialMetricUsability.REJECTED.value for value in values):
        return FinancialMetricUsability.REJECTED.value
    if any(value == FinancialMetricUsability.EXPIRED.value for value in values):
        return FinancialMetricUsability.EXPIRED.value
    if all(value == FinancialMetricUsability.VERIFIED.value for value in values):
        return FinancialMetricUsability.VERIFIED.value
    if all(
        value in {FinancialMetricUsability.VERIFIED.value, FinancialMetricUsability.SUPPORTED.value}
        for value in values
    ):
        return FinancialMetricUsability.SUPPORTED.value
    return FinancialMetricUsability.DECLARED_ONLY.value


def _metric_input(
    metric: dict[str, Any],
    period: dict[str, Any],
    usability: str,
    links: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "record_id": _uuid_or_none(metric.get("id")),
        "metric_type": metric.get("metric_type"),
        "value": _to_decimal(metric.get("value")),
        "unit": _metric_unit(metric, period, metric.get("metric_type")),
        "currency": period.get("currency"),
        "period_start": _parse_date(period.get("period_start")),
        "period_end": _parse_date(period.get("period_end")),
        "evidence_status": usability,
        "review_status": metric.get("status"),
        "evidence_ids": [_uuid_or_none(link.get("id")) for link in links if link.get("id")],
        "source_type": period.get("source_type"),
    }


def _metric_unit(
    metric: dict[str, Any], period: dict[str, Any], metric_type: str | None
) -> str | None:
    if metric.get("unit"):
        return metric.get("unit")
    if metric_type in RATIO_METRICS:
        return "ratio"
    if metric_type in MONEY_METRICS:
        return period.get("currency")
    return None


def _link_ref(link: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": link.get("id"),
        "document_id": link.get("document_id"),
        "subject_id": link.get("subject_id"),
        "evidence_role": link.get("evidence_role"),
        "review_status": link.get("review_status"),
        "validation_status": link.get("validation_status"),
        "quoted_text": link.get("quoted_text"),
    }


def _validate_units(rule: Any, resolution: MetricResolution, metric_type: str) -> str | None:
    rule_currency = _get(rule, "currency")
    if rule_currency and resolution.currency and rule_currency != resolution.currency:
        return FinancialExplanationCode.CURRENCY_MISMATCH.value
    rule_unit = _get(rule, "unit")
    if (
        rule_unit
        and resolution.unit
        and _normalize_unit(rule_unit) != _normalize_unit(resolution.unit)
    ):
        return FinancialExplanationCode.UNIT_MISMATCH.value
    if (
        metric_type in RATIO_METRICS
        and resolution.unit
        and _normalize_unit(resolution.unit) != "ratio"
    ):
        return FinancialExplanationCode.UNIT_MISMATCH.value
    return None


def _normalize_unit(unit: str) -> str:
    normalized = _normalize_text(str(unit)).strip()
    if normalized in {"%", "porcentaje", "percent", "ratio", "indice"}:
        return "ratio"
    if normalized in {"cop", "peso", "pesos", "$"}:
        return "COP"
    return normalized


def _compare(rule: Any, actual: Decimal) -> tuple[str, str]:
    operator = _get(rule, "operator")
    required = _get(rule, "required_value")
    min_value = _get(rule, "required_min_value")
    max_value = _get(rule, "required_max_value")
    complies = False
    if operator == FinancialOperator.GREATER_THAN_OR_EQUAL.value and required is not None:
        complies = actual >= required
        return (
            FinancialEvaluationResultStatus.COMPLIES.value
            if complies
            else FinancialEvaluationResultStatus.DOES_NOT_COMPLY.value,
            FinancialExplanationCode.VALUE_MEETS_MINIMUM.value
            if complies
            else FinancialExplanationCode.VALUE_BELOW_MINIMUM.value,
        )
    if operator == FinancialOperator.GREATER_THAN.value and required is not None:
        complies = actual > required
        return (
            FinancialEvaluationResultStatus.COMPLIES.value
            if complies
            else FinancialEvaluationResultStatus.DOES_NOT_COMPLY.value,
            FinancialExplanationCode.VALUE_MEETS_MINIMUM.value
            if complies
            else FinancialExplanationCode.VALUE_BELOW_MINIMUM.value,
        )
    if operator == FinancialOperator.LESS_THAN_OR_EQUAL.value and required is not None:
        complies = actual <= required
        return (
            FinancialEvaluationResultStatus.COMPLIES.value
            if complies
            else FinancialEvaluationResultStatus.DOES_NOT_COMPLY.value,
            FinancialExplanationCode.VALUE_MEETS_MAXIMUM.value
            if complies
            else FinancialExplanationCode.VALUE_EXCEEDS_MAXIMUM.value,
        )
    if operator == FinancialOperator.LESS_THAN.value and required is not None:
        complies = actual < required
        return (
            FinancialEvaluationResultStatus.COMPLIES.value
            if complies
            else FinancialEvaluationResultStatus.DOES_NOT_COMPLY.value,
            FinancialExplanationCode.VALUE_MEETS_MAXIMUM.value
            if complies
            else FinancialExplanationCode.VALUE_EXCEEDS_MAXIMUM.value,
        )
    if operator == FinancialOperator.BETWEEN_INCLUSIVE.value and min_value and max_value:
        complies = min_value <= actual <= max_value
        return (
            FinancialEvaluationResultStatus.COMPLIES.value
            if complies
            else FinancialEvaluationResultStatus.DOES_NOT_COMPLY.value,
            FinancialExplanationCode.VALUE_WITHIN_RANGE.value
            if complies
            else FinancialExplanationCode.VALUE_OUTSIDE_RANGE.value,
        )
    return (
        FinancialEvaluationResultStatus.UNKNOWN.value,
        FinancialExplanationCode.RULE_AMBIGUOUS.value,
    )


def _extract_numbers(value: str, *, percent: bool = False) -> list[Decimal]:
    numbers = []
    for match in re.findall(r"(?<![a-zA-Z])[-+]?\d+(?:[.,]\d+)?(?![a-zA-Z])", value):
        parsed = _to_decimal(match, percent=percent)
        if parsed is not None:
            numbers.append(parsed)
    return numbers


def _to_decimal(value: Any, *, percent: bool = False) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        if isinstance(value, int | float | Decimal):
            parsed = Decimal(str(value))
        else:
            text = str(value).strip()
            if not text:
                return None
            text = text.replace("$", "").replace("COP", "").replace("cop", "")
            text = text.replace("%", "").strip()
            if "," in text and "." in text:
                text = text.replace(".", "").replace(",", ".")
            else:
                text = text.replace(",", ".")
            parsed = Decimal(text)
    except (InvalidOperation, ValueError):
        return None
    if percent:
        return parsed / Decimal("100")
    return parsed


def _parse_date(value: Any) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return date.fromisoformat(str(value))


def _uuid_or_none(value: Any) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def _get(obj: Any, name: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name)
