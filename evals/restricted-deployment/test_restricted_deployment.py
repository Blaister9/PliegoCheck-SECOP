from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from pliegocheck_api.main import app

ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "deploy" / "restricted"


def controller_module():
    spec = importlib.util.spec_from_file_location("restricted_controller", DEPLOY / "controller.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def secure_environment(tmp_path: Path) -> dict[str, str]:
    external = tmp_path / "external"
    external.mkdir()
    values = {
        "session": "s" * 48,
        "db-password": "d" * 48,
        "db-url": f"postgresql+psycopg://pliegocheck:{'d' * 48}@postgres:5432/pliegocheck",
        "bootstrap": "B" * 24 + "9!",
    }
    for name, value in values.items():
        (external / name).write_text(value, encoding="utf-8")
    return {
        "PLIEGOCHECK_DEPLOYMENT_MODE": "restricted",
        "PLIEGOCHECK_PUBLIC_BASE_URL": "https://localhost:8443",
        "PLIEGOCHECK_ALLOWED_ORIGINS": "https://localhost:8443",
        "PLIEGOCHECK_TRUSTED_HOSTS": "localhost",
        "PLIEGOCHECK_TRUSTED_PROXY_CIDRS": "172.16.0.0/12",
        "PLIEGOCHECK_SECURE_COOKIES": "true",
        "PLIEGOCHECK_SESSION_SECRET_FILE": str(external / "session"),
        "PLIEGOCHECK_SESSION_TTL_MINUTES": "480",
        "PLIEGOCHECK_DATABASE_PASSWORD_FILE": str(external / "db-password"),
        "PLIEGOCHECK_DATABASE_URL_FILE": str(external / "db-url"),
        "PLIEGOCHECK_BOOTSTRAP_ADMIN_ENABLED": "false",
        "PLIEGOCHECK_STORAGE_PATH": str(external / "storage"),
        "PLIEGOCHECK_BACKUP_PATH": str(external / "backups"),
        "PLIEGOCHECK_TLS_CERT_FILE": str(external / "tls.crt"),
        "PLIEGOCHECK_TLS_KEY_FILE": str(external / "tls.key"),
        "PLIEGOCHECK_SECOP_ENABLED": "false",
        "PLIEGOCHECK_MONITORING_ENABLED": "false",
        "PLIEGOCHECK_EXTERNAL_DELIVERY_ENABLED": "false",
        "PLIEGOCHECK_NOTIFICATION_DRY_RUN": "true",
    }


def test_secure_configuration_contract(tmp_path: Path) -> None:
    controller = controller_module()
    errors, warnings = controller.validate_configuration(secure_environment(tmp_path))
    assert errors == []
    assert warnings == []


@pytest.mark.parametrize(
    ("key", "value", "expected"),
    [
        ("PLIEGOCHECK_ALLOWED_ORIGINS", "*", "allowed_origins_must_be_explicit_https"),
        ("PLIEGOCHECK_SECURE_COOKIES", "false", "secure_cookies_required"),
        (
            "PLIEGOCHECK_TRUSTED_HOSTS",
            "*",
            "trusted_hosts_must_include_public_host_without_wildcard",
        ),
    ],
)
def test_preflight_rejects_insecure_configuration(
    tmp_path: Path, key: str, value: str, expected: str
) -> None:
    controller = controller_module()
    environment = secure_environment(tmp_path)
    environment[key] = value
    errors, _warnings = controller.validate_configuration(environment)
    assert expected in errors


def test_bootstrap_and_confirmation_guards(tmp_path: Path) -> None:
    controller = controller_module()
    environment = secure_environment(tmp_path)
    environment["PLIEGOCHECK_BOOTSTRAP_ADMIN_ENABLED"] = "true"
    errors, _ = controller.validate_configuration(environment)
    assert "bootstrap_email_required" in errors
    assert "bootstrap_password_file_required" in errors
    with pytest.raises(controller.RestrictedError, match="rollback requires"):
        controller.rollback(Path("missing.env"), None, False)


def test_compose_has_only_proxy_ports_and_hardened_services() -> None:
    text = (DEPLOY / "compose.restricted.yaml").read_text(encoding="utf-8")
    for service in ("reverse-proxy:", "web:", "api:", "worker:", "scheduler:", "postgres:"):
        assert service in text
    assert text.count("ports:") == 1
    assert "no-new-privileges:true" in text
    assert "postgres:17.5-bookworm" in text
    assert 'profiles: ["scheduler"]' in text
    assert "./:/" not in text
    assert "--reload" not in text


def test_env_schema_and_all_wrappers_exist() -> None:
    schema = json.loads((DEPLOY / "env.schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["PLIEGOCHECK_DEPLOYMENT_MODE"]["const"] == "restricted"
    for command in (
        "preflight",
        "deploy",
        "validate",
        "status",
        "backup",
        "restore-verify",
        "rollback",
        "stop",
    ):
        assert (DEPLOY / f"{command}.ps1").is_file()
        assert (DEPLOY / f"{command}.sh").is_file()


def test_api_rejects_untrusted_host_and_cors_wildcard() -> None:
    client = TestClient(app)
    assert client.get("/health/live").status_code == 200
    assert client.get("/health/live", headers={"Host": "denied.example.invalid"}).status_code == 400
    response = client.get("/health/live", headers={"Origin": "https://denied.example.invalid"})
    assert "access-control-allow-origin" not in response.headers


def test_backup_manifest_hash_verification(tmp_path: Path) -> None:
    controller = controller_module()
    (tmp_path / "database.dump").write_bytes(b"synthetic database")
    (tmp_path / "storage.zip").write_bytes(b"synthetic storage")
    files = {
        name: {"sha256": controller.sha256(tmp_path / name)}
        for name in ("database.dump", "storage.zip")
    }
    (tmp_path / "manifest.json").write_text(json.dumps({"files": files}), encoding="utf-8")
    assert controller.verify_manifest(tmp_path)["files"] == files
    (tmp_path / "storage.zip").write_bytes(b"tampered")
    with pytest.raises(controller.RestrictedError, match="hash mismatch"):
        controller.verify_manifest(tmp_path)
