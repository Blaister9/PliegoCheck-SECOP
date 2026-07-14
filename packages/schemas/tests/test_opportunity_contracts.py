from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from pliegocheck_schemas import (
    OpportunityDiscoveryRequest,
    OpportunityInboxFilters,
    OpportunityReviewRequest,
)


def test_discovery_contract_is_strict_and_requires_aware_time() -> None:
    payload = OpportunityDiscoveryRequest(
        company_profile_id=uuid4(),
        company_snapshot_id=uuid4(),
        candidate_ids=[uuid4()],
        effective_at=datetime.now(UTC),
    )
    assert payload.force is False
    with pytest.raises(ValidationError):
        OpportunityDiscoveryRequest.model_validate({**payload.model_dump(), "unknown": True})


def test_filters_and_review_actions_are_closed_enums() -> None:
    assert OpportunityInboxFilters(sort="priority").limit == 20
    with pytest.raises(ValidationError):
        OpportunityInboxFilters(sort="arbitrary")
    with pytest.raises(ValidationError):
        OpportunityReviewRequest.model_validate({"action": "APPROVE"})
