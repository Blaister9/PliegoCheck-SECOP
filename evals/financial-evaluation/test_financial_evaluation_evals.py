# mypy: ignore-errors
"""Evals sinteticos del motor financiero deterministico."""

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from pliegocheck_api.financial import evaluate_financial_requirement, map_financial_requirement
from pliegocheck_schemas import RequirementCategory


@pytest.mark.parametrize(
    ("description", "metric_value", "expected_status"),
    [
        ("indice de liquidez minimo de 1.2", "1.3", "COMPLIES"),
        ("indice de liquidez minimo de 1.2", "1.1", "DOES_NOT_COMPLY"),
        ("endeudamiento maximo de 70%", "0.65", "COMPLIES"),
        ("endeudamiento maximo de 70%", "0.71", "DOES_NOT_COMPLY"),
        ("capital de trabajo minimo de 1000 COP", "1200", "COMPLIES"),
        ("capital de trabajo minimo de 1000 COP", "800", "DOES_NOT_COMPLY"),
        ("rentabilidad del activo minimo de 5%", "0.06", "COMPLIES"),
        ("rentabilidad del activo minimo de 5%", "0.04", "DOES_NOT_COMPLY"),
        ("rentabilidad del patrimonio minimo de 8%", "0.09", "COMPLIES"),
        ("rentabilidad del patrimonio minimo de 8%", "0.07", "DOES_NOT_COMPLY"),
        ("cobertura de intereses minimo de 2", "3", "COMPLIES"),
        ("cobertura de intereses minimo de 2", "1", "DOES_NOT_COMPLY"),
    ],
)
def test_direct_metric_comparisons(
    description: str, metric_value: str, expected_status: str
) -> None:
    requirement = _requirement(description, expected_raw=description)
    rule_payload = map_financial_requirement(requirement, _process())
    snapshot = _snapshot(rule_payload["metric_type"], metric_value, status="VERIFIED")

    result = evaluate_financial_requirement(
        requirement=requirement,
        rule=SimpleNamespace(**rule_payload),
        snapshot_payload=snapshot,
        process_closing_at=datetime(2026, 12, 31, tzinfo=UTC),
    )

    assert result["status"] == expected_status


@pytest.mark.parametrize(
    ("metrics", "expected_status", "explanation"),
    [
        (
            {"CURRENT_ASSETS": "200", "CURRENT_LIABILITIES": "100"},
            "COMPLIES",
            "VALUE_MEETS_MINIMUM",
        ),
        (
            {"CURRENT_ASSETS": "100", "CURRENT_LIABILITIES": "100"},
            "DOES_NOT_COMPLY",
            "VALUE_BELOW_MINIMUM",
        ),
        ({"CURRENT_ASSETS": "200"}, "UNKNOWN", "METRIC_MISSING"),
        ({"CURRENT_ASSETS": "200", "CURRENT_LIABILITIES": "0"}, "UNKNOWN", "DIVISION_BY_ZERO"),
        ({"TOTAL_LIABILITIES": "50", "TOTAL_ASSETS": "100"}, "COMPLIES", "VALUE_MEETS_MAXIMUM"),
        (
            {"TOTAL_LIABILITIES": "90", "TOTAL_ASSETS": "100"},
            "DOES_NOT_COMPLY",
            "VALUE_EXCEEDS_MAXIMUM",
        ),
    ],
)
def test_derived_metric_formulas(
    metrics: dict[str, str], expected_status: str, explanation: str
) -> None:
    description = "indice de liquidez minimo de 1.5"
    if "TOTAL_LIABILITIES" in metrics:
        description = "endeudamiento maximo de 70%"
    requirement = _requirement(description, expected_raw=description)
    rule_payload = map_financial_requirement(requirement, _process())
    snapshot = _snapshot_from_metrics(metrics)

    result = evaluate_financial_requirement(
        requirement=requirement,
        rule=SimpleNamespace(**rule_payload),
        snapshot_payload=snapshot,
        process_closing_at=datetime(2026, 12, 31, tzinfo=UTC),
    )

    assert result["status"] == expected_status
    assert result["explanation_code"] == explanation


@pytest.mark.parametrize(
    ("status", "link_role", "expected_status", "explanation"),
    [
        ("DECLARED", "PRIMARY", "UNKNOWN", "DECLARED_VALUE_NOT_VERIFIED"),
        ("SUPPORTED", "PRIMARY", "COMPLIES", "VALUE_MEETS_MINIMUM"),
        ("VERIFIED", "PRIMARY", "COMPLIES", "VALUE_MEETS_MINIMUM"),
        ("VERIFIED", "CONFLICTING", "CONFLICTING_EVIDENCE", "EVIDENCE_CONFLICT"),
        ("REJECTED", "PRIMARY", "UNKNOWN", "DECLARED_VALUE_NOT_VERIFIED"),
        ("EXPIRED", "PRIMARY", "UNKNOWN", "DECLARED_VALUE_NOT_VERIFIED"),
    ],
)
def test_evidence_quality_blocks_or_flags(
    status: str, link_role: str, expected_status: str, explanation: str
) -> None:
    requirement = _requirement("indice de liquidez minimo de 1.2", expected_raw="minimo 1.2")
    rule_payload = map_financial_requirement(requirement, _process())
    snapshot = _snapshot("LIQUIDITY_RATIO", "1.5", status=status, link_role=link_role)

    result = evaluate_financial_requirement(
        requirement=requirement,
        rule=SimpleNamespace(**rule_payload),
        snapshot_payload=snapshot,
        process_closing_at=datetime(2026, 12, 31, tzinfo=UTC),
    )

    assert result["status"] == expected_status
    assert result["explanation_code"] == explanation


def _process():
    return SimpleNamespace(id=uuid4(), closing_at=datetime(2026, 12, 31, tzinfo=UTC))


def _requirement(description: str, *, expected_raw: str):
    return SimpleNamespace(
        id=uuid4(),
        process_id=uuid4(),
        normalization_run_id=uuid4(),
        stable_key="e" * 64,
        category=RequirementCategory.FINANCIAL.value,
        description=description,
        condition_text=None,
        expected_value={"value": None, "unit": None, "raw_text": expected_raw},
    )


def _snapshot(
    metric_type: str,
    value: str,
    *,
    status: str,
    link_role: str = "PRIMARY",
) -> dict:
    metric_id = uuid4()
    link = {
        "id": str(uuid4()),
        "document_id": str(uuid4()),
        "subject_type": "FINANCIAL_METRIC",
        "subject_id": str(metric_id),
        "evidence_role": link_role,
        "review_status": "VERIFIED" if status == "VERIFIED" else "PENDING",
        "validation_status": "DOCUMENT_ONLY",
    }
    return {
        "financial_periods": [
            {
                "id": str(uuid4()),
                "period_start": "2025-01-01",
                "period_end": "2025-12-31",
                "currency": "COP",
                "source_type": "FINANCIAL_STATEMENT",
                "status": "VERIFIED",
                "metrics": [
                    {
                        "id": str(metric_id),
                        "metric_type": metric_type,
                        "value": value,
                        "unit": "ratio" if metric_type not in {"WORKING_CAPITAL"} else "COP",
                        "status": status,
                    }
                ],
            }
        ],
        "evidence_links": [link],
    }


def _snapshot_from_metrics(metrics: dict[str, str]) -> dict:
    return {
        "financial_periods": [
            {
                "id": str(uuid4()),
                "period_start": "2025-01-01",
                "period_end": "2025-12-31",
                "currency": "COP",
                "source_type": "FINANCIAL_STATEMENT",
                "status": "VERIFIED",
                "metrics": [
                    {
                        "id": str(uuid4()),
                        "metric_type": metric_type,
                        "value": value,
                        "unit": "COP",
                        "status": "VERIFIED",
                    }
                    for metric_type, value in metrics.items()
                ],
            }
        ],
        "evidence_links": [],
    }
