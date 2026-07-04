"""Pruebas de los contratos del motor de decision."""

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from pliegocheck_schemas import (
    DecisionActionUpdateRequest,
    DecisionOutcome,
    DecisionReasonCode,
    DecisionRequest,
    DecisionReviewRequest,
)

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


def load_example(name: str) -> dict[str, Any]:
    with (EXAMPLES_DIR / name).open(encoding="utf-8") as fh:
        data: dict[str, Any] = json.load(fh)
    return data


def test_decision_outcomes_are_closed() -> None:
    assert {outcome.value for outcome in DecisionOutcome} == {
        "GO",
        "GO_CONDICIONADO",
        "BUSCAR_ALIADO",
        "NO_GO",
        "NO_CARGAR",
        "PENDIENTE_INFORMACION",
    }


def test_valid_decision_request_example() -> None:
    request = DecisionRequest.model_validate(load_example("decision-request.valid.json"))
    assert request.force is False


def test_invalid_decision_request_example() -> None:
    with pytest.raises(ValidationError):
        DecisionRequest.model_validate(load_example("decision-request.invalid.json"))


def test_review_override_requires_outcome_and_reason() -> None:
    with pytest.raises(ValidationError):
        DecisionReviewRequest.model_validate({"action": "OVERRIDE", "reason": "razon valida"})
    with pytest.raises(ValidationError):
        DecisionReviewRequest.model_validate(
            {"action": "OVERRIDE", "reviewed_outcome": "NO_GO", "reason": "   "}
        )
    review = DecisionReviewRequest.model_validate(
        {"action": "OVERRIDE", "reviewed_outcome": "NO_GO", "reason": "Incumplimiento confirmado."}
    )
    assert review.reviewed_outcome == DecisionOutcome.NO_GO


def test_reject_requires_reason() -> None:
    with pytest.raises(ValidationError):
        DecisionReviewRequest.model_validate({"action": "REJECT"})
    review = DecisionReviewRequest.model_validate(
        {"action": "REJECT", "reason": "La evidencia base es insuficiente."}
    )
    assert review.reviewed_outcome is None


def test_confirm_does_not_require_reason() -> None:
    review = DecisionReviewRequest.model_validate({"action": "CONFIRM"})
    assert review.reason is None


def test_action_update_cannot_reopen() -> None:
    with pytest.raises(ValidationError):
        DecisionActionUpdateRequest.model_validate({"status": "OPEN"})
    update = DecisionActionUpdateRequest.model_validate({"status": "RESOLVED"})
    assert update.status.value == "RESOLVED"


def test_reason_codes_are_closed_and_stable() -> None:
    values = {code.value for code in DecisionReasonCode}
    assert "SUBMISSION_BLOCKER_CONFIRMED" in values
    assert "ALL_MANDATORY_REQUIREMENTS_COMPLY" in values
    assert "ADAPTER_NOT_AVAILABLE" in values
    with pytest.raises(ValueError):
        DecisionReasonCode("RAZON_INVENTADA")
