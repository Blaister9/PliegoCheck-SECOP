"""Evals sinteticos deterministas de reportes de decision."""

from __future__ import annotations

from zipfile import ZipFile

from pliegocheck_api.reports.manifest import artifact_manifest_digest, stable_digest
from pliegocheck_api.reports.package import build_zip
from pliegocheck_api.reports.renderer import render_artifacts
from pliegocheck_api.reports.templates import load_report_templates


def _snapshot(outcome: str = "PENDIENTE_INFORMACION") -> dict:
    return {
        "created_at": "2026-07-04T12:00:00+00:00",
        "input_digest": "a" * 64,
        "process": {
            "id": "p",
            "title": "Proceso <script>alert(1)</script>",
            "contracting_entity": "Entidad",
            "internal_reference": "PC-1",
            "secop_reference": None,
        },
        "company": {"id": "c", "legal_name": "Empresa", "snapshot_id": "s"},
        "decision": {
            "id": "d",
            "engine_outcome": outcome,
            "reviewed_outcome": None,
            "effective_outcome": outcome,
            "reason_codes": ["MANDATORY_REQUIREMENT_UNKNOWN"],
            "policy_name": "pliegocheck-default",
            "policy_version": "1.0.0",
            "dominant_rule": "MANDATORY_REQUIREMENT_UNKNOWN",
        },
        "coverage": {
            "requirements_total": 1,
            "mandatory_applicable_total": 1,
            "evaluated_total": 1,
            "not_evaluated_total": 0,
            "unknown_total": 1,
            "conflicting_total": 0,
        },
        "findings": [{"id": "f", "requirement_id": "r", "outcome": "UNKNOWN"}],
        "rules": [
            {
                "id": "rule",
                "rule_code": "MANDATORY_REQUIREMENT_UNKNOWN",
                "status": "TRIGGERED",
                "suggested_outcome": "PENDIENTE_INFORMACION",
                "reason_code": "MANDATORY_REQUIREMENT_UNKNOWN",
                "fact_payload": {},
            }
        ],
        "requirements_matrix": [
            {
                "requirement_id": "r",
                "stable_key": "stable",
                "category": "FINANCIAL",
                "scope": "HABILITATING",
                "modality": "MANDATORY",
                "description": "Texto con <script>",
                "decision_finding_outcome": "UNKNOWN",
                "source_domain": "FINANCIAL",
                "source_run_id": None,
                "source_result_id": None,
                "requires_human_review": True,
                "review_status": "PENDING",
                "evidence_count": 0,
                "action_count": 1,
                "warning_codes": [],
            }
        ],
        "evidence_index": [
            {
                "requirement_id": "r",
                "evidence_type": "MISSING",
                "document_id": None,
                "segment_id": None,
                "source_label": "Sin evidencia",
                "source_location": {},
                "document_sha256": None,
                "quoted_text": None,
                "validation_status": "MISSING",
            }
        ],
        "actions": [
            {
                "id": "a",
                "action_type": "PROVIDE_INFORMATION",
                "priority": "HIGH",
                "status": "OPEN",
                "title_code": "ACTION_TITLE",
                "description_code": "ACTION_DESC",
                "parameters": {},
                "requirement_ids": ["r"],
                "finding_ids": ["f"],
                "due_at": None,
            }
        ],
        "decision_manifest": {"outcome": outcome},
        "evaluation_summaries": ["Financiera: run x estado COMPLETED."],
        "risk_summary": ["Existen requisitos con resultado UNKNOWN."],
        "technical_manifest": {"report_engine_version": "1.0.0"},
    }


def test_report_renderer_escapes_html_and_does_not_invent_go() -> None:
    artifacts = render_artifacts(_snapshot(), load_report_templates())
    html = next(item.content.decode() for item in artifacts if item.filename.endswith(".html"))
    markdown = next(item.content.decode() for item in artifacts if item.filename.endswith(".md"))
    assert "&lt;script&gt;" in html
    assert "<script>alert" not in html
    assert "PENDIENTE_INFORMACION" in markdown
    assert "GO inventado" not in markdown


def test_package_zip_contains_only_allowed_entries(tmp_path) -> None:
    artifacts = render_artifacts(_snapshot("NO_GO"), load_report_templates())
    data = build_zip(artifacts)
    path = tmp_path / "package.zip"
    path.write_bytes(data)
    with ZipFile(path) as archive:
        names = archive.namelist()
    assert "executive-report.html" in names
    assert ".env" not in names
    assert all("/" not in name and "\\" not in name and ".." not in name for name in names)


def test_digests_are_stable_and_change_with_template_or_action() -> None:
    snapshot = _snapshot("GO")
    first = stable_digest(snapshot)
    second = stable_digest(_snapshot("GO"))
    changed = _snapshot("GO")
    changed["actions"][0]["status"] = "RESOLVED"
    assert first == second
    assert first != stable_digest(changed)
    manifest = [
        {
            "filename": "executive-report.html",
            "artifact_type": "EXECUTIVE_HTML",
            "content_type": "text/html",
            "size_bytes": 1,
            "sha256": "a" * 64,
        }
    ]
    assert artifact_manifest_digest(manifest) == artifact_manifest_digest(list(reversed(manifest)))
