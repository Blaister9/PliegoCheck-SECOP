from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN = (
    "probabilidad de ganar",
    "probabilidad de adjudicacion",
    "probabilidad de adjudicación",
    "chance de ganar",
    "debe ofertar",
    "oferta garantizada",
    "win probability",
    "award probability",
)


def test_opportunity_module_uses_review_compatibility_language():
    roots = [
        ROOT / "apps/api/src/pliegocheck_api/opportunities",
        ROOT / "apps/web/app/opportunities",
        ROOT / "apps/api/src/pliegocheck_api/opportunity_monitoring",
        ROOT / "apps/web/app/monitors",
        ROOT / "apps/web/app/alerts",
        ROOT / "packages/schemas/src/pliegocheck_schemas/opportunities.py",
        ROOT / "packages/schemas/src/pliegocheck_schemas/opportunity_monitoring.py",
    ]
    findings = []
    for root in roots:
        paths = [root] if root.is_file() else list(root.rglob("*")) if root.exists() else []
        for path in paths:
            if path.is_file() and path.suffix in {".py", ".ts", ".tsx"}:
                text = path.read_text(encoding="utf-8").lower()
                findings.extend(
                    f"{path.relative_to(ROOT)}: {term}" for term in FORBIDDEN if term in text
                )
    assert not findings, "\n".join(findings)
