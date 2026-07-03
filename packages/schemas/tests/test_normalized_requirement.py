"""Pruebas del contrato NormalizedRequirement v2."""

import json
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from pydantic import ValidationError

from pliegocheck_schemas import (
    NORMALIZED_REQUIREMENT_SCHEMA_VERSION,
    ExpectedValue,
    NormalizedRequirement,
    RequirementBasis,
    RequirementCandidate,
    RequirementCandidateEvidence,
    RequirementCategory,
    RequirementCriticality,
    RequirementEvidenceRole,
    RequirementModality,
    RequirementNormalizationAgentOutput,
    RequirementScope,
    RequirementSubsanability,
    SourceLocation,
)

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


def load_example(name: str) -> dict[str, Any]:
    with (EXAMPLES_DIR / name).open(encoding="utf-8") as fh:
        data: dict[str, Any] = json.load(fh)
    return data


def test_valid_example_is_accepted() -> None:
    requirement = NormalizedRequirement.model_validate(
        load_example("normalized-requirement.valid.json")
    )
    assert NORMALIZED_REQUIREMENT_SCHEMA_VERSION == "2.0.0"
    assert requirement.category is RequirementCategory.FINANCIAL
    assert requirement.scope is RequirementScope.HABILITATING
    assert requirement.modality is RequirementModality.MANDATORY
    assert requirement.requires_human_review is True


def test_invalid_example_is_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        NormalizedRequirement.model_validate(load_example("normalized-requirement.invalid.json"))
    failed_fields = {error["loc"][0] for error in excinfo.value.errors()}
    assert {"id", "stable_key", "category", "description", "confidence"} <= failed_fields
    assert any(error["loc"] == ("expected_value", "extra") for error in excinfo.value.errors())


def test_requirement_extra_fields_are_rejected() -> None:
    payload = load_example("normalized-requirement.valid.json")
    payload["status"] = "COMPLIES"
    with pytest.raises(ValidationError):
        NormalizedRequirement.model_validate(payload)


def test_agent_output_requires_structured_evidence() -> None:
    output = RequirementNormalizationAgentOutput(
        schema_version="2.0.0",
        agent="RequirementNormalizationAgent",
        prompt_version="1.0.0",
        process_id=UUID("22222222-2222-2222-2222-222222222222"),
        batch_index=0,
        candidates=[
            RequirementCandidate(
                candidate_id="B000-C001",
                category=RequirementCategory.FINANCIAL,
                scope=RequirementScope.HABILITATING,
                modality=RequirementModality.MANDATORY,
                description="El proponente debe acreditar indice de liquidez minimo de 1.2.",
                condition_text=None,
                expected_value=ExpectedValue(value=1.2, unit=None, raw_text="1.2"),
                criticality=RequirementCriticality.UNKNOWN,
                criticality_basis=RequirementBasis.UNKNOWN,
                subsanability=RequirementSubsanability.UNKNOWN,
                subsanability_basis=RequirementBasis.UNKNOWN,
                confidence=0.8,
                evidence=[
                    RequirementCandidateEvidence(
                        segment_id=UUID("44444444-4444-4444-4444-444444444444"),
                        evidence_role=RequirementEvidenceRole.PRIMARY,
                        quoted_text="indice de liquidez minimo de 1.2",
                        quote_start=None,
                        quote_end=None,
                        source_location=SourceLocation(
                            page_number=1,
                            paragraph_index=None,
                            table_index=None,
                            sheet_name=None,
                            row_start=None,
                            row_end=None,
                            line_start=None,
                            line_end=None,
                            section=None,
                        ),
                    )
                ],
                requires_human_review=True,
                uncertainty_reason=None,
            )
        ],
        warnings=[],
    )
    assert output.candidates[0].evidence[0].evidence_role is RequirementEvidenceRole.PRIMARY


def test_agent_output_rejects_decision_like_extra_fields() -> None:
    payload = {
        "schema_version": "2.0.0",
        "agent": "RequirementNormalizationAgent",
        "prompt_version": "1.0.0",
        "process_id": "22222222-2222-2222-2222-222222222222",
        "batch_index": 0,
        "candidates": [],
        "warnings": [],
        "decision": "GO",
    }
    with pytest.raises(ValidationError):
        RequirementNormalizationAgentOutput.model_validate(payload)
