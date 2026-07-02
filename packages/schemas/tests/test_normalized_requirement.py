"""Pruebas del contrato NormalizedRequirement: ejemplos, validaciones y enums."""

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from pliegocheck_schemas import (
    NORMALIZED_REQUIREMENT_SCHEMA_VERSION,
    NormalizedRequirement,
    RequirementCategory,
    RequirementStatus,
)

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


def load_example(name: str) -> dict[str, Any]:
    with (EXAMPLES_DIR / name).open(encoding="utf-8") as fh:
        data: dict[str, Any] = json.load(fh)
    return data


def valid_payload() -> dict[str, Any]:
    return load_example("normalized-requirement.valid.json")


def test_valid_example_is_accepted() -> None:
    requirement = NormalizedRequirement.model_validate(valid_payload())
    assert requirement.schema_version == NORMALIZED_REQUIREMENT_SCHEMA_VERSION
    assert requirement.requirement_id == "REQ-001"
    assert requirement.category is RequirementCategory.FINANCIAL
    assert requirement.status is RequirementStatus.UNKNOWN
    assert requirement.evidence_ids == []
    assert requirement.requires_human_review is True


def test_invalid_example_is_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        NormalizedRequirement.model_validate(load_example("normalized-requirement.invalid.json"))
    failed_fields = {error["loc"][0] for error in excinfo.value.errors()}
    assert {"requirement_id", "category", "description", "evidence_ids", "confidence"} <= (
        failed_fields
    )
    assert any(error["loc"] == ("source_location", "page") for error in excinfo.value.errors())


@pytest.mark.parametrize(
    "field",
    ["schema_version", "requirement_id", "status", "confidence", "requires_human_review"],
)
def test_top_level_fields_are_required(field: str) -> None:
    payload = valid_payload()
    del payload[field]
    with pytest.raises(ValidationError):
        NormalizedRequirement.model_validate(payload)


def test_blank_identifiers_are_rejected() -> None:
    payload = valid_payload()
    payload["requirement_id"] = "   "
    with pytest.raises(ValidationError):
        NormalizedRequirement.model_validate(payload)


def test_confidence_out_of_range_is_rejected() -> None:
    for value in (-0.1, 1.1):
        payload = valid_payload()
        payload["confidence"] = value
        with pytest.raises(ValidationError):
            NormalizedRequirement.model_validate(payload)


def test_page_must_be_positive_when_present() -> None:
    payload = valid_payload()
    payload["source_location"] = {"page": 0, "section": "3.2"}
    with pytest.raises(ValidationError):
        NormalizedRequirement.model_validate(payload)
    payload["source_location"] = {"page": None, "section": "3.2"}
    assert NormalizedRequirement.model_validate(payload).source_location.page is None


def test_unknown_schema_version_is_rejected() -> None:
    payload = valid_payload()
    payload["schema_version"] = "9.9.9"
    with pytest.raises(ValidationError):
        NormalizedRequirement.model_validate(payload)


def test_enums_are_closed() -> None:
    payload = valid_payload()
    payload["status"] = "TAL_VEZ"
    with pytest.raises(ValidationError):
        NormalizedRequirement.model_validate(payload)


def test_extra_fields_are_rejected() -> None:
    payload = valid_payload()
    payload["campo_inventado"] = "valor"
    with pytest.raises(ValidationError):
        NormalizedRequirement.model_validate(payload)


def test_scalar_values_are_accepted_for_comparable_fields() -> None:
    payload = valid_payload()
    payload["expected_value"] = 1.2
    payload["company_value"] = "certificado"
    requirement = NormalizedRequirement.model_validate(payload)
    assert requirement.expected_value == 1.2
    assert requirement.company_value == "certificado"
