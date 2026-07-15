"""Smoke tests de preparacion para despliegue controlado.

No usa OpenAI, no usa datos reales y evita crear backups reales. Verifica que
la configuracion, health checks, auth, worker, storage/reportes y documentacion
esten listos para una demo o piloto controlado.
"""

from __future__ import annotations

import json
import subprocess
import sys
from http import HTTPStatus
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
ENV_EXAMPLE = ROOT / ".env.example"


def _env_example_text() -> str:
    return ENV_EXAMPLE.read_text(encoding="utf-8")


def test_env_examples_cover_controlled_deployment_variables() -> None:
    env = _env_example_text()
    local_env = (ROOT / ".env.local.example").read_text(encoding="utf-8")
    pilot_env = (ROOT / ".env.pilot.example").read_text(encoding="utf-8")
    required = [
        "DATABASE_URL",
        "PLIEGOCHECK_STORAGE_PATH",
        "PLIEGOCHECK_ALLOWED_WEB_ORIGINS",
        "PLIEGOCHECK_CORS_ALLOWED_ORIGINS",
        "PLIEGOCHECK_ENVIRONMENT",
        "PLIEGOCHECK_PILOT_MODE",
        "PLIEGOCHECK_AUTH_ENABLED",
        "PLIEGOCHECK_AUTH_COOKIE_SECURE",
        "PLIEGOCHECK_AUTH_SECRET_KEY",
        "PLIEGOCHECK_REPORT_STORAGE_PATH",
        "PLIEGOCHECK_BACKUP_OUTPUT_DIR",
        "NEXT_PUBLIC_API_BASE_URL",
        "PLIEGOCHECK_AI_ENABLED",
        "OPENAI_API_KEY",
        "PLIEGOCHECK_ALLOW_FAKE_NORMALIZATION_PROVIDER",
    ]
    for name in required:
        assert f"{name}=" in env, f"{name} no esta documentada en .env.example"
    assert "PLIEGOCHECK_CORS_ALLOWED_ORIGINS=*" not in env
    assert "CHANGEME" in env
    assert "PLIEGOCHECK_ENVIRONMENT=development" in local_env
    assert "PLIEGOCHECK_PILOT_MODE=true" in pilot_env
    assert "PLIEGOCHECK_AUTH_COOKIE_SECURE=true" in pilot_env


def test_local_config_is_valid(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from pliegocheck_api.config import Settings

    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@localhost:56543/db")
    monkeypatch.setenv("PLIEGOCHECK_STORAGE_PATH", str(tmp_path / "documents"))
    monkeypatch.setenv("PLIEGOCHECK_ALLOWED_WEB_ORIGINS", "http://localhost:3000")
    monkeypatch.setenv("PLIEGOCHECK_CORS_ALLOWED_ORIGINS", "http://localhost:3000")
    monkeypatch.setenv("PLIEGOCHECK_ENVIRONMENT", "development")
    monkeypatch.setenv("PLIEGOCHECK_PILOT_MODE", "false")
    monkeypatch.setenv("PLIEGOCHECK_AUTH_ENABLED", "true")
    monkeypatch.setenv("PLIEGOCHECK_AUTH_SECRET_KEY", "")
    settings = Settings()  # type: ignore[call-arg]
    assert settings.environment == "development"
    assert settings.effective_cors_origins == ["http://localhost:3000"]


def test_pilot_config_rejects_missing_secret_and_wildcard(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from pliegocheck_api.config import Settings

    base = {
        "DATABASE_URL": "postgresql+psycopg://u:p@localhost:56543/db",
        "PLIEGOCHECK_STORAGE_PATH": str(tmp_path / "documents"),
        "PLIEGOCHECK_ALLOWED_WEB_ORIGINS": "https://pilot.example.test",
        "PLIEGOCHECK_CORS_ALLOWED_ORIGINS": "https://pilot.example.test",
        "PLIEGOCHECK_ENVIRONMENT": "pilot",
        "PLIEGOCHECK_PILOT_MODE": "true",
        "PLIEGOCHECK_AUTH_ENABLED": "true",
        "PLIEGOCHECK_AUTH_COOKIE_SECURE": "true",
        "PLIEGOCHECK_AUTH_SECRET_KEY": "",
    }
    for key, value in base.items():
        monkeypatch.setenv(key, value)
    with pytest.raises(ValueError, match="AUTH_SECRET_KEY"):
        Settings()  # type: ignore[call-arg]

    monkeypatch.setenv("PLIEGOCHECK_AUTH_SECRET_KEY", "pilot-secret-placeholder-not-real")
    monkeypatch.setenv("PLIEGOCHECK_CORS_ALLOWED_ORIGINS", "*")
    with pytest.raises(ValueError, match="no puede usar"):
        Settings()  # type: ignore[call-arg]


def test_health_auth_worker_and_storage_smoke(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLIEGOCHECK_AUTH_ENABLED", "true")
    monkeypatch.setenv("PLIEGOCHECK_ENVIRONMENT", "test")
    monkeypatch.setenv("PLIEGOCHECK_AUTH_SECRET_KEY", "deployment-eval-secret-not-real")
    monkeypatch.setenv("PLIEGOCHECK_ALLOW_FAKE_NORMALIZATION_PROVIDER", "true")
    from pliegocheck_api.auth import create_user
    from pliegocheck_api.config import get_settings
    from pliegocheck_api.db import get_sessionmaker
    from pliegocheck_api.main import app
    from pliegocheck_schemas import AuthRoleName

    get_settings.cache_clear()
    email = f"deployment-admin-{uuid4().hex[:8]}@example.com"
    with get_sessionmaker()() as session:
        create_user(
            session,
            email=email,
            display_name="Deployment Admin",
            password="deployment-password-12345",
            roles=[AuthRoleName.ADMIN],
        )
        session.commit()

    client = TestClient(app)
    live = client.get("/health/live")
    ready = client.get("/health/ready")
    assert live.status_code == HTTPStatus.OK
    assert ready.status_code == HTTPStatus.OK
    assert ready.json()["checks"]["storage"] == "ok"
    assert client.get("/processes").status_code == HTTPStatus.UNAUTHORIZED
    login = client.post(
        "/auth/login",
        json={"email": email, "password": "deployment-password-12345"},
    )
    assert login.status_code == HTTPStatus.OK
    assert client.get("/admin/system-config").status_code == HTTPStatus.OK

    from pliegocheck_worker.health import health_status

    worker = health_status()
    assert worker["status"] == "ok"
    assert worker["report_generation_enabled"] is True
    assert worker["available_specialized_evaluators"] == ["LEGAL", "EXPERIENCE", "TECHNICAL"]


def test_report_storage_and_backup_manifest_are_controlled(tmp_path: Path) -> None:
    storage = tmp_path / "documents"
    storage.mkdir()
    report_artifact = storage / "decision-report-smoke.txt"
    report_artifact.write_text("synthetic report smoke", encoding="utf-8")
    assert report_artifact.read_text(encoding="utf-8") == "synthetic report smoke"

    manifest = {
        "created_at": "2026-07-04T00:00:00Z",
        "database_dump": "database.dump",
        "database_sha256": "a" * 64,
        "storage_archive": "storage.zip",
        "storage_sha256": "b" * 64,
        "excludes": [".env", "secrets", "logs"],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert ".env" in loaded["excludes"]
    assert len(loaded["database_sha256"]) == 64
    assert len(loaded["storage_sha256"]) == 64


def test_no_physical_paths_or_secrets_in_critical_docs_and_artifacts() -> None:
    checked_paths = [
        ROOT / "pilot" / "last-run-summary.example.json",
        ROOT / "docs" / "pilot-feedback-log.md",
        ROOT / "docs" / "pilot-dataset.md",
        ROOT / "docs" / "decision-package.md",
    ]
    forbidden = ["BEGIN RSA", "BEGIN OPENSSH", "AWS_SECRET_ACCESS_KEY", "password_hash"]
    for path in checked_paths:
        content = path.read_text(encoding="utf-8")
        assert "C:\\Users\\" not in content
        for marker in forbidden:
            assert marker not in content


def test_pilot_eval_is_invocable_as_substep() -> None:
    command = ["pnpm.cmd", "pilot:eval"] if sys.platform == "win32" else ["pnpm", "pilot:eval"]
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=180,
    )
    assert result.returncode == 0, result.stdout


def test_documentation_commands_and_files_exist() -> None:
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    scripts = package["scripts"]
    for command in [
        "deployment:eval",
        "deployment:backup-check",
        "pilot:prepare",
        "pilot:run",
        "pilot:eval",
        "ops:backup",
    ]:
        assert command in scripts

    for path in [
        "docs/post-pilot-findings.md",
        "docs/browser-validation-checklist.md",
        "docs/controlled-deployment-runbook.md",
        "docs/pre-deployment-checklist.md",
        "docs/post-deployment-checklist.md",
        "docs/rollback-plan.md",
        "docs/release-candidate.md",
        "docs/observability.md",
    ]:
        assert (ROOT / path).exists(), f"falta {path}"

    roadmap = (ROOT / "docs" / "roadmap.md").read_text(encoding="utf-8")
    assert "Microfase 12: completada" in roadmap
    assert "Microfase 13: completada" in roadmap
    assert "Microfase 14: completada" in roadmap
    assert "Microfase 15:" in roadmap
    assert "Microfase 16: completada" in roadmap
    assert "Microfase 17: completada" in roadmap
    assert "Microfase 18: completada" in roadmap
    assert "Microfase 20: completada" in roadmap
    assert "Microfase 21: siguiente" in roadmap
