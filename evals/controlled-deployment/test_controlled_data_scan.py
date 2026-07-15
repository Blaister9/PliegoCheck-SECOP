"""Escaneo estatico de datos reales, secretos y rutas fisicas en artefactos piloto."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAN_ROOTS = [
    ROOT / "pilot",
    ROOT / "docs",
    ROOT / "evals",
    ROOT / "scripts",
    ROOT / ".env.example",
    ROOT / ".env.local.example",
    ROOT / ".env.pilot.example",
]

SECRET_MARKERS = [
    "OPENAI_API_KEY=sk-",
    "ANTHROPIC_API_KEY=",
    "AWS_ACCESS_KEY_ID=",
    "AWS_SECRET_ACCESS_KEY=",
    "BEGIN RSA",
    "BEGIN OPENSSH",
    "PRIVATE KEY",
    "password_hash",
    "session_token",
    "Set-Cookie",
]
REAL_DATA_MARKERS = [
    "899999",
    "900373",
    "830092",
    "@gov.co",
    "@alcaldia",
    "@colombiacompra.gov.co",
]
ABSOLUTE_PATH_PATTERN = re.compile(r"(C:\\Users\\|/home/|/Users/|/var/lib/postgresql/data)")

ALLOWLISTED = {
    "docs/controlled-deployment-runbook.md": ["`PLIEGOCHECK_AUTH_SECRET_KEY`"],
    "docs/authentication.md": ["PLIEGOCHECK_AUTH_SECRET_KEY="],
    "docs/security-and-governance.md": ["password_hash"],
    ".env.example": ["OPENAI_API_KEY=", "PLIEGOCHECK_AUTH_SECRET_KEY="],
    ".env.local.example": ["OPENAI_API_KEY=", "PLIEGOCHECK_AUTH_SECRET_KEY="],
    ".env.pilot.example": ["OPENAI_API_KEY=", "PLIEGOCHECK_AUTH_SECRET_KEY="],
}


def _iter_files() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        if root.is_file():
            files.append(root)
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if "__pycache__" in path.parts:
                continue
            if path.suffix.lower() in {".pyc", ".png", ".jpg", ".jpeg", ".zip"}:
                continue
            files.append(path)
    return files


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _is_allowed(rel: str, marker: str, line: str) -> bool:
    if rel == "evals/controlled-deployment/test_controlled_data_scan.py":
        return True
    if rel == "evals/notification-delivery/test_notification_delivery_evals.py":
        return True
    if rel.startswith("evals/") and (
        "not in" in line
        or "assert all" in line
        or "forbidden" in line
        or "secret_marker" in line
        or "SECRET_MARKERS" in line
        or "REAL_DATA_MARKERS" in line
    ):
        return True
    for allowed in ALLOWLISTED.get(rel, []):
        if allowed in marker or allowed in line:
            return True
    if "CHANGEME" in line or "not-real" in line or "placeholder" in line:
        return True
    return rel.startswith("evals/") and ("secret-not-real" in line or "password-12345" in line)


def test_no_real_data_secrets_or_local_paths_in_pilot_artifacts() -> None:
    findings: list[str] = []
    for path in _iter_files():
        rel = _relative(path)
        content = path.read_text(encoding="utf-8", errors="ignore")
        for line_number, line in enumerate(content.splitlines(), start=1):
            for marker in SECRET_MARKERS + REAL_DATA_MARKERS:
                if marker in line and not _is_allowed(rel, marker, line):
                    findings.append(f"{rel}:{line_number}: marker {marker}")
            if (
                ABSOLUTE_PATH_PATTERN.search(line)
                and rel != "evals/controlled-deployment/test_controlled_data_scan.py"
                and not rel.endswith("rollback-plan.md")
            ):
                findings.append(f"{rel}:{line_number}: ruta fisica local")
    assert not findings, "\n".join(findings)
