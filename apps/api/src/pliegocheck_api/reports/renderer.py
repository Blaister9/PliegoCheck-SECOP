"""Render deterministico de artefactos de reporte."""

from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass
from html import escape
from typing import Any

from pliegocheck_api.reports.manifest import canonical_json
from pliegocheck_api.reports.templates import ReportTemplates

SCOPE_NOTICE = (
    "Este reporte presenta una decision preliminar generada a partir de reglas deterministicas "
    "y evidencia disponible. No constituye concepto juridico, adjudicacion, garantia de "
    "habilitacion ni recomendacion oficial de participacion."
)
ABSENCE_NOTICE = "La ausencia de informacion o evidencia nunca se interpreta como cumplimiento."


@dataclass(frozen=True)
class RenderedArtifact:
    filename: str
    artifact_type: str
    content_type: str
    content: bytes


def render_artifacts(
    snapshot: dict[str, Any], templates: ReportTemplates
) -> list[RenderedArtifact]:
    matrix = snapshot["requirements_matrix"]
    evidence = snapshot["evidence_index"]
    actions = snapshot["actions"]
    decision_manifest = snapshot["decision_manifest"]
    context = _template_context(snapshot)
    html = _render_template(templates.html, context, html=True)
    markdown = _render_template(templates.markdown, context, html=False)
    return [
        RenderedArtifact(
            "executive-report.html", "EXECUTIVE_HTML", "text/html; charset=utf-8", html.encode()
        ),
        RenderedArtifact(
            "executive-report.md",
            "EXECUTIVE_MARKDOWN",
            "text/markdown; charset=utf-8",
            markdown.encode(),
        ),
        RenderedArtifact(
            "requirements-matrix.json",
            "REQUIREMENTS_MATRIX_JSON",
            "application/json",
            _json_bytes(matrix),
        ),
        RenderedArtifact(
            "requirements-matrix.csv",
            "REQUIREMENTS_MATRIX_CSV",
            "text/csv; charset=utf-8",
            _csv_bytes(matrix),
        ),
        RenderedArtifact(
            "evidence-index.json", "EVIDENCE_INDEX_JSON", "application/json", _json_bytes(evidence)
        ),
        RenderedArtifact("actions.json", "ACTIONS_JSON", "application/json", _json_bytes(actions)),
        RenderedArtifact(
            "decision-manifest.json",
            "DECISION_MANIFEST_JSON",
            "application/json",
            _json_bytes(decision_manifest),
        ),
    ]


def _json_bytes(data: Any) -> bytes:
    return (canonical_json(data) + "\n").encode("utf-8")


def _csv_bytes(rows: list[dict[str, Any]]) -> bytes:
    output = io.StringIO(newline="")
    fieldnames = [
        "requirement_id",
        "stable_key",
        "category",
        "scope",
        "modality",
        "description",
        "decision_finding_outcome",
        "source_domain",
        "source_run_id",
        "source_result_id",
        "requires_human_review",
        "review_status",
        "evidence_count",
        "action_count",
        "warning_codes",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        serialized = dict(row)
        serialized["warning_codes"] = "|".join(row.get("warning_codes") or [])
        writer.writerow(serialized)
    return output.getvalue().encode("utf-8")


def _template_context(snapshot: dict[str, Any]) -> dict[str, str]:
    process = snapshot["process"]
    company = snapshot["company"]
    decision = snapshot["decision"]
    coverage = snapshot.get("coverage") or {}
    matrix = snapshot["requirements_matrix"]
    evidence = snapshot["evidence_index"]
    actions = snapshot["actions"]
    rules = snapshot["rules"]
    findings = snapshot["findings"]
    evaluated_domains = sorted({row["source_domain"] for row in matrix if row["source_domain"]})
    not_evaluated = [row for row in matrix if row["decision_finding_outcome"] == "NOT_EVALUATED"]
    unknown = [row for row in matrix if row["decision_finding_outcome"] == "UNKNOWN"]
    conflicts = [row for row in matrix if row["decision_finding_outcome"] == "CONFLICTING_EVIDENCE"]
    open_actions = [row for row in actions if row["status"] in {"OPEN", "ACKNOWLEDGED"}]
    reason_codes = ", ".join(decision.get("reason_codes") or []) or "Sin codigos de razon."
    triggered_rules = ", ".join(
        rule["rule_code"] for rule in rules if rule["status"] == "TRIGGERED"
    )
    return {
        "process_title": process["title"],
        "contracting_entity": process["contracting_entity"],
        "internal_reference": process["internal_reference"],
        "secop_reference": process.get("secop_reference") or "Sin referencia SECOP",
        "company_name": company.get("legal_name") or "UNKNOWN",
        "company_snapshot_id": str(company.get("snapshot_id") or "UNKNOWN"),
        "created_at": snapshot["created_at"],
        "engine_outcome": decision.get("engine_outcome") or "UNKNOWN",
        "effective_outcome": decision.get("effective_outcome") or "UNKNOWN",
        "policy_version": str(decision.get("policy_version") or "UNKNOWN"),
        "input_digest_short": snapshot["input_digest"][:12],
        "scope_notice": SCOPE_NOTICE,
        "absence_notice": ABSENCE_NOTICE,
        "executive_summary": "\n".join(
            [
                f"Outcome del motor: {decision.get('engine_outcome') or 'UNKNOWN'}",
                f"Outcome efectivo: {decision.get('effective_outcome') or 'UNKNOWN'}",
                f"Override humano: {'si' if decision.get('reviewed_outcome') else 'no'}",
                f"Reason codes: {reason_codes}",
                f"Bloqueos/conflictos: {len(conflicts)}",
                f"Pendientes UNKNOWN: {len(unknown)}",
                f"Acciones abiertas: {len(open_actions)}",
                f"Dimensiones evaluadas: {', '.join(evaluated_domains) or 'ninguna'}",
                f"Requisitos no evaluados: {len(not_evaluated)}",
            ]
        ),
        "decision_summary": "\n".join(
            [
                "Precedencia aplicada por politica: "
                f"{decision.get('policy_name')} {decision.get('policy_version')}",
                f"Reglas disparadas: {triggered_rules or 'ninguna'}",
                f"Regla dominante: {decision.get('dominant_rule') or 'UNKNOWN'}",
                f"Hallazgos canonicos: {len(findings)}",
            ]
        ),
        "coverage_summary": "\n".join(
            [
                f"Total requisitos: {coverage.get('requirements_total', len(matrix))}",
                f"Obligatorios aplicables: {coverage.get('mandatory_applicable_total', 0)}",
                f"Evaluados: {coverage.get('evaluated_total', 0)}",
                f"No evaluados: {coverage.get('not_evaluated_total', len(not_evaluated))}",
                f"Unknown: {coverage.get('unknown_total', len(unknown))}",
                f"Conflicting: {coverage.get('conflicting_total', len(conflicts))}",
            ]
        ),
        "evaluation_summary": "\n".join(snapshot["evaluation_summaries"]),
        "evidence_summary": (
            f"Entradas de evidencia: {len(evidence)}. Documentos originales no incluidos en HTML."
        ),
        "actions_summary": "\n".join(
            f"{row['priority']} {row['action_type']} {row['status']} {row['title_code']}"
            for row in actions
        )
        or "Sin acciones generadas por el motor.",
        "risk_summary": "\n".join(snapshot["risk_summary"]),
        "technical_manifest": json.dumps(snapshot["technical_manifest"], indent=2, sort_keys=True),
    }


def _render_template(template: str, context: dict[str, str], *, html: bool) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        value = context.get(key, "")
        return escape(value, quote=True) if html else value

    return re.sub(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", replace, template)
