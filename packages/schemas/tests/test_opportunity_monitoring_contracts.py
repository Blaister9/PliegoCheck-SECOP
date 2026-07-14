# mypy: ignore-errors
from uuid import uuid4

import pytest
from pydantic import ValidationError

from pliegocheck_schemas import OpportunityAlertRules, OpportunityMonitorCreateRequest


def test_monitor_contract_is_closed_and_baseline_is_quiet():
    payload = OpportunityMonitorCreateRequest(
        name="SECOP infraestructura",
        company_profile_id=uuid4(),
        company_snapshot_id=uuid4(),
        frequency="HOURLY",
        filters={"candidate_ids": [uuid4()]},
        source_systems=["SECOP_I"],
    )
    assert payload.alert_rules.alert_on_initial_results is False
    with pytest.raises(ValidationError):
        OpportunityMonitorCreateRequest.model_validate({**payload.model_dump(), "unsafe_sql": "x"})


@pytest.mark.parametrize(
    "field,value",
    [
        ("compatibility_change_threshold", 0),
        ("minimum_compatibility_score", 101),
        ("minimum_information_completeness", -1),
        ("urgent_days", 0),
        ("critical_hours", 169),
    ],
)
def test_alert_thresholds_are_bounded(field, value):
    with pytest.raises(ValidationError):
        OpportunityAlertRules.model_validate({field: value})
