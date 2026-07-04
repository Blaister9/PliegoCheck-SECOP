"""Pruebas de contratos de evaluaciones especializadas."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from pliegocheck_schemas import (
    SpecializedEvaluationDomain,
    SpecializedEvaluationRequest,
    SpecializedEvaluationResultReviewRequest,
    SpecializedEvaluationResultStatus,
    SpecializedEvaluationReviewStatus,
)


def test_specialized_request_accepts_supported_domains() -> None:
    payload = SpecializedEvaluationRequest(
        normalization_run_id=uuid4(),
        company_id=uuid4(),
        company_profile_snapshot_id=uuid4(),
        domain=SpecializedEvaluationDomain.LEGAL,
        force=False,
    )

    assert payload.domain == SpecializedEvaluationDomain.LEGAL


def test_specialized_review_override_requires_reason() -> None:
    with pytest.raises(ValidationError):
        SpecializedEvaluationResultReviewRequest(
            review_status=SpecializedEvaluationReviewStatus.OVERRIDDEN,
            override_result=SpecializedEvaluationResultStatus.DOES_NOT_COMPLY,
        )
