"""DTO puros del detector incremental."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class CandidateSnapshot:
    source_system: str
    source_process_id: str
    opportunity_id: str
    assessment_id: str
    outcome: str
    compatibility_score: Decimal
    urgency_status: str
    information_completeness: Decimal
    closing_date: datetime | None
    document_state_hash: str
    assessment_digest: str
    source_status: str | None = None
    addendum_status: str | None = None


@dataclass(frozen=True)
class CandidateChange:
    kind: str
    old: Any
    new: Any


@dataclass(frozen=True)
class AlertDecision:
    alert_type: str
    severity: str
    title: str
    summary: str
    reason_code: str
    parameters: dict[str, Any]
    material_identity: str
