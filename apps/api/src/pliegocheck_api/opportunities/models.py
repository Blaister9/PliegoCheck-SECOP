"""DTOs puros del motor de oportunidades; sin dependencias ORM."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from pliegocheck_schemas import OpportunityComponent, OpportunityComponentStatus


@dataclass(frozen=True)
class CompanySnapshotInput:
    snapshot_id: str
    digest: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class ProcessInput:
    identity: str
    title: str
    entity_name: str
    description: str | None
    unspsc_codes: tuple[str, ...]
    status: str | None
    estimated_value: Decimal | None
    currency: str | None
    department: str | None
    municipality: str | None
    publication_date: datetime | None
    closing_date: datetime | None
    document_status: str
    source_system: str
    source_reference: str | None
    payload_hash: str


@dataclass(frozen=True)
class ComponentResult:
    component: OpportunityComponent
    status: OpportunityComponentStatus
    score: Decimal
    weight: Decimal
    reason_code: str
    explanation_parameters: dict[str, Any] = field(default_factory=dict)
    evidence_refs: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def weighted_score(self) -> Decimal:
        return (self.score * self.weight).quantize(Decimal("0.01"))


@dataclass(frozen=True)
class AssessmentResult:
    outcome: str
    compatibility_score: Decimal
    urgency_score: Decimal
    information_completeness: Decimal
    urgency_status: str
    days_remaining: Decimal | None
    components: tuple[ComponentResult, ...]
    missing_information: dict[str, list[str]]
    partner_reasons: tuple[dict[str, Any], ...]
    summary: str
    warnings: tuple[str, ...]
    input_digest: str
