"""Pruebas de los contratos del piloto controlado."""

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from pliegocheck_schemas import (
    PilotExpectedOutcome,
    PilotReadiness,
    PilotRunSummary,
    PilotStepName,
    PilotStepState,
)

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


def load_example(name: str) -> dict[str, Any]:
    with (EXAMPLES_DIR / name).open(encoding="utf-8") as fh:
        data: dict[str, Any] = json.load(fh)
    return data


def test_valid_pilot_run_summary_example() -> None:
    summary = PilotRunSummary.model_validate(load_example("pilot-run-summary.valid.json"))
    assert summary.decision_outcome == "PENDIENTE_INFORMACION"
    assert summary.synthetic_data_only is True
    assert summary.artifact_count == 9
    assert len(summary.specialized_run_ids) == 3


def test_invalid_pilot_run_summary_example() -> None:
    with pytest.raises(ValidationError):
        PilotRunSummary.model_validate(load_example("pilot-run-summary.invalid.json"))


def test_run_summary_forbids_non_synthetic_flag() -> None:
    payload = load_example("pilot-run-summary.valid.json")
    payload["synthetic_data_only"] = False
    with pytest.raises(ValidationError):
        PilotRunSummary.model_validate(payload)


def test_pilot_step_enums_are_closed() -> None:
    assert "DECISION" in {step.value for step in PilotStepName}
    assert "REPORT_PACKAGE" in {step.value for step in PilotStepName}
    assert {state.value for state in PilotStepState} >= {
        "PENDING",
        "COMPLETED",
        "FAILED",
    }
    with pytest.raises(ValueError):
        PilotStepName("PASO_INVENTADO")


def test_expected_outcome_contract() -> None:
    outcome = PilotExpectedOutcome.model_validate(
        {
            "decision_outcome": "PENDIENTE_INFORMACION",
            "financial_complies_min": 1,
            "financial_does_not_comply_min": 1,
            "unknown_min": 1,
            "not_evaluated_expected": False,
            "action_min": 1,
            "report_artifact_count": 9,
        }
    )
    assert outcome.decision_outcome == "PENDIENTE_INFORMACION"
    with pytest.raises(ValidationError):
        PilotExpectedOutcome.model_validate(
            {
                "decision_outcome": "GO",
                "financial_complies_min": -1,
                "financial_does_not_comply_min": 0,
                "unknown_min": 0,
                "not_evaluated_expected": False,
                "action_min": 0,
                "report_artifact_count": 0,
            }
        )


def test_readiness_contract() -> None:
    readiness = PilotReadiness.model_validate(
        {
            "environment": "test",
            "pilot_mode": False,
            "auth_enabled": True,
            "is_local_environment": True,
            "admin_user_exists": True,
            "pilot_users_present": ["admin@pilot.pliegocheck.local"],
            "pilot_process_present": True,
            "pilot_company_present": True,
            "dataset_available": True,
            "ready": True,
            "warnings": [],
        }
    )
    assert readiness.ready is True
