import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


REQUIRED_DOCS = [
    "docs/ADR-014-controlled-mvp-closure.md",
    "docs/mvp-final-findings.md",
    "docs/mvp-controlled-scope.md",
    "docs/known-limitations.md",
    "docs/mvp-acceptance-criteria.md",
    "docs/non-production-criteria.md",
    "docs/final-demo-guide.md",
    "docs/mvp-closure-checklist.md",
    "docs/mvp-delivery-index.md",
]


REQUIRED_COMMANDS = [
    "pnpm pilot:eval",
    "pnpm controlled:eval",
    "pnpm controlled:data-scan",
    "pnpm mvp:eval",
    "pnpm mvp:data-scan",
    "pnpm check",
]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_mvp_closure_documents_exist_and_are_non_empty() -> None:
    for relative_path in REQUIRED_DOCS:
        document = ROOT / relative_path
        assert document.exists(), relative_path
        assert document.read_text(encoding="utf-8").strip(), relative_path


def test_release_candidate_is_final_mvp_controlled_candidate() -> None:
    content = read_text("docs/release-candidate.md")

    assert "0.14.0-mvp-controlled" in content
    assert "No se recibió retroalimentación real de usuarios piloto en esta microfase." in content
    for command in REQUIRED_COMMANDS:
        assert command in content


def test_roadmap_marks_microfase_14_closed_and_microfase_15_next() -> None:
    content = read_text("docs/roadmap.md")

    assert "Microfase 14" in content
    assert "completada" in content.lower()
    assert "Microfase 15" in content
    assert "Decisión ejecutiva sobre evolución a piloto real o pausa técnica" in content


def test_final_findings_have_no_open_blocker() -> None:
    content = read_text("docs/mvp-final-findings.md")
    table_rows = [line.upper() for line in content.splitlines() if line.startswith("| MVPF-")]

    assert "No se recibió retroalimentación real de usuarios piloto en esta microfase." in content
    assert not any("BLOCKER" in line and "OPEN" in line for line in table_rows)
    for category in ["BLOCKER", "HIGH", "MEDIUM", "LOW", "DEFERRED", "CLOSED"]:
        assert category in content


def test_acceptance_and_non_production_criteria_are_explicit() -> None:
    acceptance = read_text("docs/mvp-acceptance-criteria.md")
    non_production = read_text("docs/non-production-criteria.md")

    for command in [
        "pnpm pilot:eval",
        "pnpm controlled:eval",
        "pnpm controlled:data-scan",
        "pnpm mvp:eval",
        "pnpm mvp:data-scan",
    ]:
        assert command in acceptance
    assert "no equivale a aprobacion productiva" in acceptance.lower()
    assert "NO GO" in non_production
    assert "validacion real con usuarios piloto" in non_production.lower()


def test_package_scripts_include_mvp_closure_and_check_integration() -> None:
    package_json = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    scripts = package_json["scripts"]

    assert scripts["mvp:eval"] == "uv run pytest evals/mvp-closure"
    assert scripts["mvp:data-scan"] == "pnpm controlled:data-scan"
    for script_name in [
        "pilot:eval",
        "controlled:eval",
        "controlled:data-scan",
        "mvp:eval",
        "mvp:data-scan",
    ]:
        assert f"pnpm {script_name}" in scripts["check"]


def test_delivery_index_links_commands_and_core_docs() -> None:
    content = read_text("docs/mvp-delivery-index.md")

    for relative_path in REQUIRED_DOCS:
        if relative_path == "docs/mvp-delivery-index.md":
            continue
        assert Path(relative_path).name in content
    for command in REQUIRED_COMMANDS:
        assert command in content
