"""Pruebas de contratos de perfil de empresa."""

import json
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from pliegocheck_schemas import (
    COMPANY_PROFILE_SCHEMA_VERSION,
    CompanyEvidenceLinkCreate,
    CompanyEvidenceSubjectType,
    CompanyFinancialMetricCreate,
    CompanyFinancialPeriodCreate,
    CompanyProfileCreate,
    CompanyProfileSnapshotCreate,
)

EXAMPLES = Path("packages/schemas/examples")


def test_company_profile_example_validates() -> None:
    payload = json.loads((EXAMPLES / "company-profile.valid.json").read_text(encoding="utf-8"))
    parsed = CompanyProfileCreate.model_validate(payload)
    assert parsed.legal_name == "Empresa Sintetica SAS"
    assert parsed.tax_id == "900123456"
    assert COMPANY_PROFILE_SCHEMA_VERSION == "1.0.0"


def test_company_profile_invalid_example_rejects_extra_and_blank() -> None:
    payload = json.loads((EXAMPLES / "company-profile.invalid.json").read_text(encoding="utf-8"))
    with pytest.raises(ValidationError):
        CompanyProfileCreate.model_validate(payload)


def test_financial_period_dates_and_decimal_metric() -> None:
    with pytest.raises(ValidationError):
        CompanyFinancialPeriodCreate.model_validate(
            {
                "period_start": "2025-12-31",
                "period_end": "2025-01-01",
                "currency": "COP",
                "source_type": "RUP",
            }
        )
    metric = CompanyFinancialMetricCreate.model_validate(
        {"metric_type": "LIQUIDITY_RATIO", "value": "1.75", "unit": "ratio"}
    )
    assert metric.value == Decimal("1.75")


def test_evidence_link_document_only_and_snapshot_contracts() -> None:
    link = CompanyEvidenceLinkCreate.model_validate(
        {
            "document_id": "00000000-0000-0000-0000-000000000001",
            "subject_type": "COMPANY_PROFILE",
            "subject_id": "00000000-0000-0000-0000-000000000002",
        }
    )
    assert link.subject_type is CompanyEvidenceSubjectType.COMPANY_PROFILE
    snapshot = CompanyProfileSnapshotCreate()
    assert snapshot.allow_incomplete is False
