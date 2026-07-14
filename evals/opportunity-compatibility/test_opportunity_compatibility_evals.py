from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from pliegocheck_api.opportunities.engine import assess
from pliegocheck_api.opportunities.models import CompanySnapshotInput, ProcessInput
from pliegocheck_api.opportunities.policy import load_policy
from pliegocheck_schemas import OpportunityComponent, OpportunityComponentStatus

EFFECTIVE = datetime(2026, 7, 13, 12, tzinfo=UTC)


def snapshot(**overrides):
    payload = {
        "company": {
            "economic_activity_codes": ["interventoria ingenieria"],
            "department": "Cundinamarca",
            "city": "Bogota",
        },
        "unspsc_codes": [{"code": "81101500"}],
        "experience_records": [
            {
                "contract_title": "Interventoria de ingenieria civil",
                "description": "supervision de obras",
                "unspsc_codes": ["81101500"],
                "total_contract_value": "500000000",
            }
        ],
        "rup_snapshots": [{"financial_capacity": "500000000"}],
        "financial_periods": [{"period": "2025"}],
        "capabilities": [
            {
                "name": "Interventoria",
                "description": "ingenieria civil",
                "territorial_scope": "nacional",
            }
        ],
        "legal_registrations": [{"registration_type": "RUP"}],
    }
    payload.update(overrides)
    return CompanySnapshotInput("snapshot-1", "a" * 64, payload)


def process(**overrides):
    values = dict(
        identity="SECOP_II:fixture",
        title="Interventoria de ingenieria civil",
        entity_name="Entidad publica",
        description="Supervision de obras de ingenieria",
        unspsc_codes=("81101500",),
        status="Publicado",
        estimated_value=Decimal("100000000"),
        currency="COP",
        department="Cundinamarca",
        municipality="Bogota",
        publication_date=EFFECTIVE - timedelta(days=1),
        closing_date=EFFECTIVE + timedelta(days=10),
        document_status="DOCUMENT_LINKS_AVAILABLE",
        source_system="SECOP_II",
        source_reference="fixture",
        payload_hash="b" * 64,
    )
    values.update(overrides)
    return ProcessInput(**values)


def component(result, name):
    return next(item for item in result.components if item.component == name)


def test_strong_screening_is_deterministic_and_reviewed_first():
    policy = load_policy()
    first = assess(snapshot(), process(), policy, EFFECTIVE)
    second = assess(snapshot(), process(), policy, EFFECTIVE)
    assert first == second
    assert first.input_digest == second.input_digest
    assert first.outcome == "REVISAR_PRIMERO"
    assert first.compatibility_score >= 75
    assert (
        component(first, OpportunityComponent.RELEVANCE).status
        is OpportunityComponentStatus.STRONG_MATCH
    )
    assert component(first, OpportunityComponent.UNSPSC_MATCH).reason_code == "UNSPSC_PRODUCT_MATCH"


@pytest.mark.parametrize(
    ("code", "reason"),
    [
        ("81101500", "UNSPSC_PRODUCT_MATCH"),
        ("81101599", "UNSPSC_CLASS_MATCH"),
        ("81109999", "UNSPSC_FAMILY_MATCH"),
        ("81999999", "UNSPSC_SEGMENT_MATCH"),
    ],
)
def test_unspsc_hierarchy(code, reason):
    result = assess(snapshot(), process(unspsc_codes=(code,)), load_policy(), EFFECTIVE)
    assert component(result, OpportunityComponent.UNSPSC_MATCH).reason_code == reason


def test_unknown_does_not_add_positive_score_and_missing_is_explicit():
    result = assess(
        snapshot(unspsc_codes=[], financial_periods=[]),
        process(unspsc_codes=(), estimated_value=None, closing_date=None),
        load_policy(),
        EFFECTIVE,
    )
    unknowns = [
        item for item in result.components if item.status is OpportunityComponentStatus.UNKNOWN
    ]
    assert unknowns
    assert all(item.score == 0 and item.weighted_score == 0 for item in unknowns)
    assert {"closing_date", "estimated_value", "unspsc_codes"} <= set(
        result.missing_information["missing_fields"]
    )
    assert result.urgency_status == "UNKNOWN"


def test_urgency_never_changes_compatibility():
    policy = load_policy()
    normal = assess(
        snapshot(), process(closing_date=EFFECTIVE + timedelta(days=10)), policy, EFFECTIVE
    )
    critical = assess(
        snapshot(), process(closing_date=EFFECTIVE + timedelta(hours=12)), policy, EFFECTIVE
    )
    assert normal.compatibility_score == critical.compatibility_score
    assert normal.urgency_status == "NORMAL"
    assert critical.urgency_status == "CRITICAL"


@pytest.mark.parametrize(
    "closing,status",
    [
        (EFFECTIVE - timedelta(hours=1), "EXPIRED"),
        (EFFECTIVE + timedelta(hours=24), "CRITICAL"),
        (EFFECTIVE + timedelta(days=3), "URGENT"),
        (EFFECTIVE + timedelta(days=10), "NORMAL"),
        (EFFECTIVE + timedelta(days=30), "LONG_HORIZON"),
    ],
)
def test_urgency_bands(closing, status):
    assert (
        assess(snapshot(), process(closing_date=closing), load_policy(), EFFECTIVE).urgency_status
        == status
    )


def test_closed_expired_and_irrelevant_are_discarded():
    policy = load_policy()
    assert assess(snapshot(), process(status="cerrado"), policy, EFFECTIVE).outcome == "DESCARTAR"
    assert (
        assess(
            snapshot(), process(closing_date=EFFECTIVE - timedelta(days=1)), policy, EFFECTIVE
        ).outcome
        == "DESCARTAR"
    )
    assert (
        assess(
            snapshot(),
            process(title="Suministro de alimentos", description="mercado escolar"),
            policy,
            EFFECTIVE,
        ).outcome
        == "DESCARTAR"
    )


def test_outcome_variants_are_conservative():
    policy = load_policy()
    potential = assess(
        snapshot(), process(closing_date=EFFECTIVE + timedelta(hours=12)), policy, EFFECTIVE
    )
    insufficient = assess(
        snapshot(
            experience_records=[], financial_periods=[], capabilities=[], legal_registrations=[]
        ),
        process(
            closing_date=None,
            estimated_value=None,
            unspsc_codes=(),
            document_status="DOCUMENTS_NOT_AVAILABLE",
        ),
        policy,
        EFFECTIVE,
    )
    partner = assess(snapshot(), process(estimated_value=Decimal("900000000")), policy, EFFECTIVE)
    low = assess(
        snapshot(experience_records=[]),
        process(
            title="Interventoria logística alimentos aseo transporte mantenimiento vigilancia",
            description="Abastecimiento comunicaciones operación servicios generales",
            unspsc_codes=(),
            estimated_value=None,
            document_status="DOCUMENTS_NOT_AVAILABLE",
        ),
        policy,
        EFFECTIVE,
    )
    assert potential.outcome == "OPORTUNIDAD_POTENCIAL"
    assert insufficient.outcome == "INFORMACION_INSUFICIENTE"
    assert partner.outcome == "REQUIERE_ALIADO"
    assert low.outcome == "POCO_COMPATIBLE"
    assert partner.partner_reasons and all(
        item["partner_resolvable"] == "unknown" for item in partner.partner_reasons
    )


def test_document_and_geographic_states_are_explicit():
    policy = load_policy()
    ready = assess(snapshot(), process(), policy, EFFECTIVE)
    missing = assess(
        snapshot(),
        process(document_status="DOCUMENTS_NOT_AVAILABLE", department=None, municipality=None),
        policy,
        EFFECTIVE,
    )
    assert (
        component(ready, OpportunityComponent.DOCUMENT_READINESS).status
        is OpportunityComponentStatus.MATCH
    )
    assert (
        component(missing, OpportunityComponent.DOCUMENT_READINESS).status
        is OpportunityComponentStatus.UNKNOWN
    )
    assert (
        component(missing, OpportunityComponent.GEOGRAPHIC_FIT).status
        is OpportunityComponentStatus.UNKNOWN
    )
