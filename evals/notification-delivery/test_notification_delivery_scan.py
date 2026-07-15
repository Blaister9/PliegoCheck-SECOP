"""Semantic and secret scan focused on external notification delivery."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEMANTIC_FORBIDDEN = (
    "probabilidad de ganar",
    "debe presentar oferta",
    "oferta garantizada",
    "award probability",
    "win probability",
)
SECRET_ASSIGNMENT = re.compile(
    r"^(PLIEGOCHECK_(?:SMTP_PASSWORD|WEBHOOK_SECRET)[A-Z0-9_]*)=(.+)$", re.MULTILINE
)


def _source_files() -> list[Path]:
    roots = [
        ROOT / "apps/api/src/pliegocheck_api/notification_delivery",
        ROOT / "apps/web/app/settings/notifications",
        ROOT / "apps/web/app/notification-deliveries",
        ROOT / "apps/web/app/operations/notifications",
        ROOT / "docs",
    ]
    return [
        path
        for root in roots
        for path in ([root] if root.is_file() else root.rglob("*"))
        if path.is_file() and path.suffix.lower() in {".py", ".ts", ".tsx", ".md"}
    ]


def test_notification_language_does_not_claim_commercial_outcomes() -> None:
    findings = []
    for path in _source_files():
        content = path.read_text(encoding="utf-8").lower()
        findings.extend(
            f"{path.relative_to(ROOT)}: {term}" for term in SEMANTIC_FORBIDDEN if term in content
        )
    assert not findings, "\n".join(findings)


def test_notification_examples_do_not_embed_delivery_secrets() -> None:
    findings = []
    for name in (".env.example", ".env.local.example", ".env.pilot.example"):
        path = ROOT / name
        for key, value in SECRET_ASSIGNMENT.findall(path.read_text(encoding="utf-8")):
            if value.strip() and "CHANGEME" not in value and "not-real" not in value:
                findings.append(f"{name}: {key}")
    assert not findings, "\n".join(findings)
