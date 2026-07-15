from pathlib import Path

ROOT = Path(__file__).parents[2]
GATE = (ROOT / "docs/pilot-go-no-go.md").read_text(encoding="utf-8")
SCORECARD = (ROOT / "docs/supervised-pilot-scorecard.md").read_text(encoding="utf-8")
READINESS = (ROOT / "docs/pilot-readiness-assessment.md").read_text(encoding="utf-8")


def test_gate_has_all_states():
    for value in (
        "PILOT_READY",
        "PILOT_READY_WITH_CONDITIONS",
        "REMEDIATION_REQUIRED",
        "PILOT_BLOCKED",
    ):
        assert value in GATE


def test_gate_requires_real_user():
    assert "usuario" in GATE.lower() and "PILOT_READY" in GATE


def test_gate_is_not_production():
    assert "no equivale" in GATE.lower() and "producción" in GATE.lower()


def test_readiness_uses_controlled_states():
    for value in ("VERIFIED", "PARTIAL", "NOT_VERIFIED", "BLOCKED", "NOT_APPLICABLE"):
        assert value in READINESS


def test_readiness_records_base():
    assert "75045eaecff05a26e67d0bbd71f1f7343de61ed8" in READINESS


def test_scorecard_dimensions():
    for value in (
        "functional",
        "usability",
        "data quality",
        "explainability",
        "security",
        "operations",
        "reliability",
        "notification usefulness",
        "recovery",
        "documentation",
    ):
        assert value in SCORECARD


def test_scorecard_no_numeric_score():
    assert "/100" not in SCORECARD


def test_pending_human_validation():
    assert "USER_VALIDATION_PENDING" in SCORECARD


def test_no_win_probability():
    assert "probabilidad de adjudicación" in GATE.lower()


def test_no_automatic_recommendation():
    assert "recomendación automática" in GATE.lower()
