"""Evals de despliegue controlado para validacion con usuarios piloto.

Usan TestClient y scripts versionados para CI. El levantamiento completo con
procesos reales vive en `pnpm controlled:deploy` y `pnpm controlled:validate`.
"""

from __future__ import annotations

import json
import re
from http import HTTPStatus
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]


def _package_scripts() -> dict[str, str]:
    return json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["scripts"]


def test_controlled_scripts_and_compose_profile_exist() -> None:
    scripts = _package_scripts()
    for command in [
        "controlled:deploy",
        "controlled:validate",
        "controlled:stop",
        "controlled:reset",
        "controlled:eval",
        "controlled:data-scan",
        "controlled:backup-check",
    ]:
        assert command in scripts

    compose = (ROOT / "compose.pilot.yaml").read_text(encoding="utf-8")
    assert "pliegocheck-controlled-postgres" in compose
    assert "controlled-postgres-data" in compose
    assert "./var/documents" in compose
    assert "healthcheck" in compose

    for script in [
        "scripts/deploy-controlled.ps1",
        "scripts/validate-controlled.ps1",
        "scripts/stop-controlled.ps1",
        "scripts/reset-controlled.ps1",
    ]:
        content = (ROOT / script).read_text(encoding="utf-8")
        assert "git reset --hard" not in content
        assert "push --force" not in content
        assert "Write-Output $env:" not in content


def test_pilot_env_profile_is_controlled(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from pliegocheck_api.config import Settings

    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@localhost:56543/db")
    monkeypatch.setenv("PLIEGOCHECK_STORAGE_PATH", str(tmp_path / "documents"))
    monkeypatch.setenv("PLIEGOCHECK_ALLOWED_WEB_ORIGINS", "https://pilot.example.test")
    monkeypatch.setenv("PLIEGOCHECK_CORS_ALLOWED_ORIGINS", "https://pilot.example.test")
    monkeypatch.setenv("PLIEGOCHECK_ENVIRONMENT", "pilot")
    monkeypatch.setenv("PLIEGOCHECK_PILOT_MODE", "true")
    monkeypatch.setenv("PLIEGOCHECK_AUTH_ENABLED", "true")
    monkeypatch.setenv("PLIEGOCHECK_AUTH_COOKIE_SECURE", "true")
    monkeypatch.setenv("PLIEGOCHECK_AUTH_SECRET_KEY", "controlled-secret-not-real")
    monkeypatch.setenv("PLIEGOCHECK_AI_ENABLED", "false")
    monkeypatch.setenv("PLIEGOCHECK_ALLOW_FAKE_NORMALIZATION_PROVIDER", "false")

    settings = Settings()  # type: ignore[call-arg]
    assert settings.environment == "pilot"
    assert settings.pilot_mode is True
    assert settings.auth_enabled is True
    assert settings.auth_cookie_secure is True
    assert settings.ai_enabled is False
    assert settings.effective_cors_origins == ["https://pilot.example.test"]


def test_controlled_smoke_health_auth_worker_db_and_storage(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("PLIEGOCHECK_AUTH_ENABLED", "true")
    monkeypatch.setenv("PLIEGOCHECK_ENVIRONMENT", "test")
    monkeypatch.setenv("PLIEGOCHECK_AUTH_SECRET_KEY", "controlled-eval-secret-not-real")
    monkeypatch.setenv("PLIEGOCHECK_STORAGE_PATH", str(tmp_path / "documents"))
    monkeypatch.setenv("PLIEGOCHECK_ALLOW_FAKE_NORMALIZATION_PROVIDER", "true")

    from pliegocheck_api.auth import create_user
    from pliegocheck_api.config import get_settings
    from pliegocheck_api.db import get_engine, get_sessionmaker
    from pliegocheck_api.main import app
    from pliegocheck_schemas import AuthRoleName
    from pliegocheck_worker.health import health_status

    get_settings.cache_clear()
    email = f"controlled-admin-{uuid4().hex[:8]}@example.test"
    with get_sessionmaker()() as session:
        create_user(
            session,
            email=email,
            display_name="Controlled Admin",
            password="controlled-password-12345",
            roles=[AuthRoleName.ADMIN],
        )
        session.commit()

    with get_engine().connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1

    client = TestClient(app)
    assert client.get("/health/live").status_code == HTTPStatus.OK
    ready = client.get("/health/ready")
    assert ready.status_code == HTTPStatus.OK
    assert ready.json()["checks"]["storage"] == "ok"
    assert client.get("/processes").status_code == HTTPStatus.UNAUTHORIZED
    assert (
        client.post(
            "/auth/login",
            json={"email": email, "password": "controlled-password-12345"},
        ).status_code
        == HTTPStatus.OK
    )
    assert client.get("/admin/system-config").status_code == HTTPStatus.OK

    worker = health_status()
    assert worker["status"] == "ok"
    assert worker["auth_enabled"] is True
    assert worker["report_generation_enabled"] is True
    assert set(worker["available_specialized_evaluators"]) == {"LEGAL", "EXPERIENCE", "TECHNICAL"}


def test_controlled_pilot_run_report_zip_audit_and_backup(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("PLIEGOCHECK_AUTH_ENABLED", "true")
    monkeypatch.setenv("PLIEGOCHECK_ENVIRONMENT", "test")
    monkeypatch.setenv("PLIEGOCHECK_AUTH_SECRET_KEY", "controlled-pilot-secret-not-real")
    monkeypatch.setenv("PLIEGOCHECK_STORAGE_PATH", str(tmp_path / "documents"))
    monkeypatch.setenv("PLIEGOCHECK_ALLOW_FAKE_NORMALIZATION_PROVIDER", "true")

    from pliegocheck_api.config import get_settings
    from pliegocheck_api.main import app
    from pliegocheck_worker.pilot import PILOT_DOMAIN
    from pliegocheck_worker.pilot.orchestrator import (
        DEFAULT_DEMO_PASSWORD,
        execute_pilot,
        reset_pilot,
    )

    get_settings.cache_clear()
    reset_pilot(confirm=True)
    summary = execute_pilot(password=DEFAULT_DEMO_PASSWORD)
    assert summary.steps_failed == 0
    assert summary.decision_outcome == "PENDIENTE_INFORMACION"
    assert summary.artifact_count >= 9
    assert summary.audit_event_count > 0

    client = TestClient(app)
    assert (
        client.post(
            "/auth/login",
            json={
                "email": f"reviewer@{PILOT_DOMAIN}",
                "password": DEFAULT_DEMO_PASSWORD,
            },
        ).status_code
        == HTTPStatus.OK
    )
    zip_response = client.get(
        f"/processes/{summary.process_id}/decision-reports/{summary.report_package_id}/download"
    )
    assert zip_response.status_code == HTTPStatus.OK
    zip_path = tmp_path / "decision-package.zip"
    zip_path.write_bytes(zip_response.content)
    with ZipFile(zip_path) as archive:
        names = archive.namelist()
        assert any(name.endswith("manifest.json") for name in names)
        assert all(not name.startswith("/") and ".." not in name for name in names)
        payload = b"".join(archive.read(name) for name in names)
        assert b"BEGIN RSA" not in payload
        assert b"C:\\Users\\" not in payload

    backup = (ROOT / "scripts" / "backup-local.ps1").read_text(encoding="utf-8")
    assert "manifest.json" in backup
    assert "database_sha256" in backup
    assert "storage_sha256" in backup
    assert '".env"' in backup


def test_user_validation_kit_and_docs_are_complete() -> None:
    required_paths = [
        "docs/ADR-013-controlled-deployment-user-validation.md",
        "docs/user-pilot-readiness-checklist.md",
        "docs/user-pilot-findings.md",
        "docs/pilot-validation-minutes.md",
        "docs/pilot-observation-guide.md",
        "pilot/user-validation/README.md",
        "pilot/user-validation/session-plan.md",
        "pilot/user-validation/tasks-admin.md",
        "pilot/user-validation/tasks-analyst.md",
        "pilot/user-validation/tasks-reviewer.md",
        "pilot/user-validation/tasks-viewer.md",
        "pilot/user-validation/feedback-form.md",
        "pilot/user-validation/feedback-form.csv",
        "pilot/user-validation/findings-matrix.csv",
        "pilot/user-validation/validation-minutes-template.md",
        "pilot/user-validation/consent-and-scope-note.md",
    ]
    for path in required_paths:
        assert (ROOT / path).exists(), f"falta {path}"

    feedback_csv = (ROOT / "pilot/user-validation/feedback-form.csv").read_text(encoding="utf-8")
    for column in [
        "escenario",
        "rol",
        "tarea",
        "resultado_esperado",
        "resultado_observado",
        "severidad",
        "evidencia",
        "decision",
        "fase_destino",
        "estado",
    ]:
        assert column in feedback_csv

    findings = (ROOT / "docs/user-pilot-findings.md").read_text(encoding="utf-8")
    for severity in ["BLOCKER", "HIGH", "MEDIUM", "LOW", "OBSERVATION"]:
        assert severity in findings
    assert "Validacion real con usuarios aun pendiente" in findings

    roadmap = (ROOT / "docs/roadmap.md").read_text(encoding="utf-8")
    assert "Microfase 13: completada" in roadmap
    assert "Microfase 14: siguiente" in roadmap

    release = (ROOT / "docs/release-candidate.md").read_text(encoding="utf-8")
    assert "0.13.0-rc.1" in release
    assert re.search(r"Commit base:\*\* `?[0-9a-f]{7,40}`?", release)
