from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_gate_is_conservative_and_package_is_complete() -> None:
    gate = (ROOT / "docs" / "restricted-deployment-go-no-go.md").read_text(encoding="utf-8")
    assert "PACKAGE_READY_WITH_CONDITIONS" in gate
    assert "Resultado vigente" in gate
    assert "servidor institucional" in gate.lower()
    assert "SSO" in gate and "MFA" in gate
    assert "PACKAGE_READY` no" in gate
    required = [
        "ADR-022-restricted-institutional-deployment.md",
        "restricted-deployment-architecture.md",
        "restricted-deployment-runbook.md",
        "restricted-deployment-security-review.md",
        "restricted-data-policy.md",
        "restricted-incident-response.md",
    ]
    assert all((ROOT / "docs" / name).is_file() for name in required)


def test_package_does_not_claim_real_institutional_deployment() -> None:
    architecture = (ROOT / "docs" / "restricted-deployment-architecture.md").read_text(
        encoding="utf-8"
    )
    assert "Despliegue en servidor institucional real: no ejecutado." in architecture
    assert "RESTRICTED_SINGLE_HOST" in architecture
