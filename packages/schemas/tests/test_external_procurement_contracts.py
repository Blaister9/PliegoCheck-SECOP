"""Contratos canonicos del conector SECOP."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from pliegocheck_schemas import (
    ExternalProcurementSearchRequest,
    ExternalProcurementSourceSystem,
)


def test_search_request_defaults_are_bounded() -> None:
    payload = ExternalProcurementSearchRequest(query="vigilancia")
    assert payload.source_system is ExternalProcurementSourceSystem.SECOP_II
    assert payload.limit == 20
    assert payload.offset == 0


def test_search_request_rejects_invalid_ranges_and_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ExternalProcurementSearchRequest(min_value=Decimal("10"), max_value=Decimal("1"))
    with pytest.raises(ValidationError):
        ExternalProcurementSearchRequest.model_validate({"limit": 101})
    with pytest.raises(ValidationError):
        ExternalProcurementSearchRequest.model_validate({"unknown_filter": "x"})
