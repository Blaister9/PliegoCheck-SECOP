"""Comparación determinística de estados compactos."""

from .models import CandidateChange, CandidateSnapshot


def detect_changes(
    previous: CandidateSnapshot, current: CandidateSnapshot
) -> list[CandidateChange]:
    fields = (
        "outcome",
        "compatibility_score",
        "urgency_status",
        "closing_date",
        "document_state_hash",
        "document_count",
        "document_version_hash",
        "assessment_digest",
        "source_status",
        "addendum_status",
    )
    return [
        CandidateChange(field, getattr(previous, field), getattr(current, field))
        for field in fields
        if getattr(previous, field) != getattr(current, field)
        and not (getattr(previous, field) is None and getattr(current, field) is None)
    ]
