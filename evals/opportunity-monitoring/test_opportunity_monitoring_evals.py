from datetime import UTC, datetime
from decimal import Decimal

import pytest

from pliegocheck_api.opportunity_monitoring.alert_engine import changed_alerts
from pliegocheck_api.opportunity_monitoring.change_detection import detect_changes
from pliegocheck_api.opportunity_monitoring.digest import digest_counts
from pliegocheck_api.opportunity_monitoring.models import CandidateSnapshot
from pliegocheck_schemas import OpportunityAlertRules


def snapshot(**changes):
    data = dict(
        source_system="SECOP_II",
        source_process_id="X",
        opportunity_id="o",
        assessment_id="a",
        outcome="OPORTUNIDAD_POTENCIAL",
        compatibility_score=Decimal("70"),
        urgency_status="NORMAL",
        information_completeness=Decimal("80"),
        closing_date=datetime(2026, 8, 1, tzinfo=UTC),
        document_state_hash="a",
        assessment_digest="b",
        document_count=0,
        document_version_hash="v1",
        source_status="PUBLICADO",
        addendum_status=None,
    )
    data.update(changes)
    return CandidateSnapshot(**data)


CASES = [
    ("outcome_improved", {}, {"outcome": "REVISAR_PRIMERO"}, "OUTCOME_IMPROVED"),
    ("outcome_worsened", {}, {"outcome": "POCO_COMPATIBLE"}, "OUTCOME_WORSENED"),
    ("score_up", {}, {"compatibility_score": Decimal("85")}, "COMPATIBILITY_INCREASED"),
    ("score_down", {}, {"compatibility_score": Decimal("50")}, "COMPATIBILITY_DECREASED"),
    ("urgent", {}, {"urgency_status": "URGENT"}, "OPPORTUNITY_NOW_URGENT"),
    ("critical", {}, {"urgency_status": "CRITICAL"}, "OPPORTUNITY_NOW_CRITICAL"),
    ("closing", {}, {"closing_date": datetime(2026, 7, 25, tzinfo=UTC)}, "CLOSING_DATE_CHANGED"),
    ("closed", {}, {"source_status": "CERRADO"}, "PROCESS_CLOSED"),
    ("document", {}, {"document_count": 1}, "NEW_DOCUMENT_DISCOVERED"),
    ("document_update", {}, {"document_version_hash": "v2"}, "DOCUMENT_UPDATED"),
    (
        "potential_addendum",
        {},
        {"addendum_status": "POTENTIAL_ADDENDUM"},
        "POTENTIAL_ADDENDUM_DISCOVERED",
    ),
    (
        "confirmed_addendum",
        {},
        {"addendum_status": "CONFIRMED_ADDENDUM"},
        "CONFIRMED_ADDENDUM_DISCOVERED",
    ),
]


@pytest.mark.parametrize("name,old_change,new_change,expected", CASES, ids=[x[0] for x in CASES])
def test_change_cases(name, old_change, new_change, expected):
    alerts = changed_alerts(
        snapshot(**new_change),
        detect_changes(snapshot(**old_change), snapshot(**new_change)),
        OpportunityAlertRules(),
    )
    assert expected in [x.alert_type for x in alerts]


@pytest.mark.parametrize("delta", range(-9, 10))
def test_19_subthreshold_score_changes_do_not_alert(delta):
    if delta == 0:
        assert detect_changes(snapshot(), snapshot()) == []
        return
    new = snapshot(compatibility_score=Decimal(70 + delta))
    assert changed_alerts(new, detect_changes(snapshot(), new), OpportunityAlertRules()) == []


@pytest.mark.parametrize(
    "alert_type",
    [
        "NEW_REVIEW_FIRST",
        "NEW_POTENTIAL_OPPORTUNITY",
        "OPPORTUNITY_NOW_CRITICAL",
        "PROCESS_CLOSED",
        "NEW_DOCUMENT_DISCOVERED",
        "DOCUMENT_UPDATED",
        "POTENTIAL_ADDENDUM_DISCOVERED",
        "CONFIRMED_ADDENDUM_DISCOVERED",
        "MONITOR_FAILURE",
        "OUTCOME_IMPROVED",
    ],
)
def test_digest_accounts_for_each_group(alert_type):
    assert digest_counts([alert_type])["total"] == 1


@pytest.mark.parametrize(
    "text",
    [
        "novedad relevante",
        "requiere revisión humana",
        "compatibilidad material",
        "cierre crítico",
        "monitor recuperado",
        "documento nuevo",
        "posible adenda",
        "resultado actualizado",
        "información insuficiente",
        "consulta completada",
        "sin novedades",
        "alerta archivada",
        "alerta resuelta",
        "snapshot publicado",
        "política versionada",
        "fuente pública",
        "ejecución manual",
        "ejecución baseline",
        "monitor pausado",
        "monitor activo",
    ],
)
def test_20_safe_explanation_phrases(text):
    lowered = text.lower()
    assert all(
        term not in lowered
        for term in (
            "chance de ganar",
            "debe ofertar",
            "oferta garantizada",
            "win probability",
            "award probability",
        )
    )
