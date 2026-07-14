"""Agrupación pura del digest interno."""

from collections import Counter
from collections.abc import Iterable


def digest_counts(alert_types: Iterable[str]) -> dict[str, int]:
    counts = Counter(alert_types)
    priority = counts["NEW_REVIEW_FIRST"] + counts["NEW_POTENTIAL_OPPORTUNITY"]
    critical = counts["OPPORTUNITY_NOW_CRITICAL"] + counts["PROCESS_CLOSED"]
    documents = sum(
        counts[key]
        for key in (
            "NEW_DOCUMENT_DISCOVERED",
            "DOCUMENT_UPDATED",
            "POTENTIAL_ADDENDUM_DISCOVERED",
            "CONFIRMED_ADDENDUM_DISCOVERED",
        )
    )
    failures = counts["MONITOR_FAILURE"]
    return {
        "priority_opportunities": priority,
        "critical_closings": critical,
        "documents_and_addenda": documents,
        "monitor_failures": failures,
        "relevant_changes": sum(counts.values()) - priority - critical - documents - failures,
        "total": sum(counts.values()),
    }
