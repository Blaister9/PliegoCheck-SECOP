"""Pruebas de contratos de evaluacion financiera."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from pliegocheck_schemas import (
    FINANCIAL_EVALUATION_SCHEMA_VERSION,
    FinancialEvaluationRequest,
    FinancialEvaluationResultReviewRequest,
    FinancialEvaluationReviewStatus,
    FinancialMetricInput,
    FinancialMetricUsability,
    FinancialRequirementRuleUpdate,
)


def test_financial_evaluation_request_validates() -> None:
    request = FinancialEvaluationRequest.model_validate(
        {
            "normalization_run_id": "00000000-0000-0000-0000-000000000001",
            "company_id": "00000000-0000-0000-0000-000000000002",
            "company_profile_snapshot_id": "00000000-0000-0000-0000-000000000003",
        }
    )
    assert FINANCIAL_EVALUATION_SCHEMA_VERSION == "1.0.0"
    assert request.force is False


def test_financial_override_requires_result_and_reason() -> None:
    with pytest.raises(ValidationError):
        FinancialEvaluationResultReviewRequest.model_validate(
            {"review_status": FinancialEvaluationReviewStatus.OVERRIDDEN.value}
        )
    valid = FinancialEvaluationResultReviewRequest.model_validate(
        {
            "review_status": "OVERRIDDEN",
            "override_result": "UNKNOWN",
            "override_reason": "Evidencia insuficiente.",
        }
    )
    assert valid.override_result is not None


def test_financial_metric_input_uses_decimal_and_evidence_quality() -> None:
    metric = FinancialMetricInput.model_validate(
        {
            "record_id": None,
            "metric_type": "LIQUIDITY_RATIO",
            "value": "1.75",
            "unit": "ratio",
            "currency": None,
            "period_start": "2025-01-01",
            "period_end": "2025-12-31",
            "evidence_status": "SUPPORTED",
        }
    )
    assert metric.value == Decimal("1.75")
    assert metric.evidence_status is FinancialMetricUsability.SUPPORTED


def test_rule_patch_requires_no_unrelated_extra_fields() -> None:
    with pytest.raises(ValidationError):
        FinancialRequirementRuleUpdate.model_validate(
            {"metric_type": "LIQUIDITY_RATIO", "unexpected": True}
        )
