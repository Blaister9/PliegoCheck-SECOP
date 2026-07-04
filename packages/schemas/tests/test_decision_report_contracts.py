"""Pruebas de contratos de reportes de decision."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from pliegocheck_schemas import (
    DecisionReportArtifactType,
    DecisionReportJobStatus,
    DecisionReportPackageStatus,
    DecisionReportRequest,
    RequirementMatrixRow,
)


def test_decision_report_enums_are_closed() -> None:
    assert {item.value for item in DecisionReportJobStatus} == {
        "PENDING",
        "PROCESSING",
        "COMPLETED",
        "COMPLETED_WITH_WARNINGS",
        "FAILED",
        "CANCELLED",
    }
    assert DecisionReportPackageStatus.ARCHIVED.value == "ARCHIVED"
    assert DecisionReportArtifactType.PACKAGE_ZIP.value == "PACKAGE_ZIP"


def test_decision_report_request_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError):
        DecisionReportRequest.model_validate(
            {"decision_run_id": str(uuid4()), "force": False, "outcome": "GO"}
        )


def test_requirement_matrix_row_contract() -> None:
    row = RequirementMatrixRow(
        requirement_id=uuid4(),
        stable_key="stable",
        category="FINANCIAL",
        scope="HABILITATING",
        modality="MANDATORY",
        description="Requisito sintetico",
        decision_finding_outcome="UNKNOWN",
        source_domain="FINANCIAL",
        source_run_id=None,
        source_result_id=None,
        requires_human_review=True,
        review_status="PENDING",
        evidence_count=0,
        action_count=1,
        warning_codes=["MISSING_EVIDENCE"],
    )
    assert row.decision_finding_outcome == "UNKNOWN"
