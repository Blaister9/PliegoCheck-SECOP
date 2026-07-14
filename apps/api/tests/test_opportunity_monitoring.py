# mypy: ignore-errors
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from pliegocheck_api.opportunity_monitoring.alert_engine import (
    alert_fingerprint,
    changed_alerts,
    initial_alerts,
)
from pliegocheck_api.opportunity_monitoring.change_detection import detect_changes
from pliegocheck_api.opportunity_monitoring.models import CandidateSnapshot
from pliegocheck_api.opportunity_monitoring.scheduling import next_run_at
from pliegocheck_schemas import OpportunityAlertRules, OpportunityMonitorFrequency


def state(**changes):
    values = dict(
        source_system="SECOP_I",
        source_process_id="P-1",
        opportunity_id="o",
        assessment_id="a",
        outcome="OPORTUNIDAD_POTENCIAL",
        compatibility_score=Decimal("70"),
        urgency_status="NORMAL",
        information_completeness=Decimal("80"),
        closing_date=datetime(2026, 7, 20, tzinfo=UTC),
        document_state_hash="a" * 64,
        assessment_digest="b" * 64,
        document_count=0,
        document_version_hash="c" * 64,
        source_status="PUBLICADO",
        addendum_status=None,
    )
    values.update(changes)
    return CandidateSnapshot(**values)


def test_baseline_default_quiet_and_opt_in_alerts():
    assert initial_alerts(state(), OpportunityAlertRules())
    assert OpportunityAlertRules().alert_on_initial_results is False


def test_material_change_and_fingerprint_are_deterministic():
    old = state()
    new = state(compatibility_score=Decimal("85"))
    decisions = changed_alerts(new, detect_changes(old, new), OpportunityAlertRules())
    assert [x.alert_type for x in decisions] == ["COMPATIBILITY_INCREASED"]
    assert alert_fingerprint("m", new, decisions[0], "p", "s") == alert_fingerprint(
        "m", new, decisions[0], "p", "s"
    )


def test_small_score_change_and_unknown_do_not_alert():
    old = state(compatibility_score=Decimal("70"))
    new = state(compatibility_score=Decimal("75"))
    assert changed_alerts(new, detect_changes(old, new), OpportunityAlertRules()) == []
    same = state(outcome="INFORMACION_INSUFICIENTE")
    assert detect_changes(same, same) == []


def test_document_inventory_distinguishes_new_document_version_and_addendum():
    rules = OpportunityAlertRules()
    old = state(document_count=1, document_version_hash="1" * 64)
    added = state(document_count=2, document_version_hash="2" * 64)
    updated = state(document_count=1, document_version_hash="2" * 64)
    addendum = state(addendum_status="CONFIRMED_ADDENDUM")

    assert [
        decision.alert_type for decision in changed_alerts(added, detect_changes(old, added), rules)
    ] == ["NEW_DOCUMENT_DISCOVERED"]
    assert [
        decision.alert_type
        for decision in changed_alerts(updated, detect_changes(old, updated), rules)
    ] == ["DOCUMENT_UPDATED"]
    assert "CONFIRMED_ADDENDUM_DISCOVERED" in [
        decision.alert_type
        for decision in changed_alerts(addendum, detect_changes(state(), addendum), rules)
    ]


def test_next_run_collapses_missed_intervals_without_drift():
    scheduled = datetime(2026, 7, 14, 8, tzinfo=UTC)
    now = scheduled + timedelta(hours=10, minutes=5)
    assert next_run_at(
        scheduled, OpportunityMonitorFrequency.HOURLY, "America/Bogota", now=now
    ) == scheduled + timedelta(hours=11)


def test_weekdays_skips_weekend():
    friday = datetime(2026, 7, 17, 13, tzinfo=UTC)
    assert (
        next_run_at(
            friday, OpportunityMonitorFrequency.WEEKDAYS, "America/Bogota", now=friday
        ).weekday()
        == 0
    )
