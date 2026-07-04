"""Carga de templates versionados sin motor ejecutable."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pliegocheck_api.reports import REPORT_TEMPLATE_VERSION
from pliegocheck_api.reports.manifest import bytes_digest


class ReportTemplateError(Exception):
    """Template ausente o invalido."""


@dataclass(frozen=True)
class ReportTemplates:
    version: str
    root: Path
    html: str
    markdown: str
    template_hash: str


def repository_root() -> Path:
    return Path(__file__).resolve().parents[5]


def load_report_templates(version: str = REPORT_TEMPLATE_VERSION) -> ReportTemplates:
    root = repository_root() / "config" / "report-templates" / f"v{version.split('.')[0]}"
    metadata_path = root / "template.json"
    html_path = root / "executive-report.html.template"
    markdown_path = root / "executive-report.md.template"
    if not metadata_path.is_file() or not html_path.is_file() or not markdown_path.is_file():
        raise ReportTemplateError("No se encontro la version de template solicitada.")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("semantic_version") != version:
        raise ReportTemplateError("La metadata del template no coincide con la version solicitada.")
    html = html_path.read_text(encoding="utf-8")
    markdown = markdown_path.read_text(encoding="utf-8")
    digest = bytes_digest(
        metadata_path.read_bytes()
        + b"\n"
        + html_path.read_bytes()
        + b"\n"
        + markdown_path.read_bytes()
    )
    return ReportTemplates(
        version=version, root=root, html=html, markdown=markdown, template_hash=digest
    )
