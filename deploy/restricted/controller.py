"""Controlador multiplataforma del paquete RESTRICTED_SINGLE_HOST."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import socket
import ssl
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEPLOY = Path(__file__).resolve().parent
COMPOSE = DEPLOY / "compose.restricted.yaml"
SCHEMA = DEPLOY / "env.schema.json"
PLACEHOLDERS = ("changeme", "replace_me", "replace-me", "example.invalid", "placeholder")
SECURITY_HEADERS = (
    "strict-transport-security",
    "x-content-type-options",
    "referrer-policy",
    "permissions-policy",
    "content-security-policy",
    "x-frame-options",
)


class RestrictedError(RuntimeError):
    """Fallo controlado sin valores sensibles."""


def log(event: str, status: str = "INFO", **fields: Any) -> None:
    payload = {"timestamp": datetime.now(UTC).isoformat(), "event": event, "status": status}
    payload.update(fields)
    print(json.dumps(payload, sort_keys=True))


def read_env(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise RestrictedError(f"configuration file not found: {path}")
    values: dict[str, str] = {}
    for number, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise RestrictedError(f"invalid configuration line: {number}")
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def as_bool(value: str | None) -> bool:
    return (value or "").lower() == "true"


def path_value(env: dict[str, str], key: str) -> Path:
    value = env.get(key, "")
    if not value:
        raise RestrictedError(f"missing configuration: {key}")
    return Path(value).expanduser().resolve()


def run(
    command: list[str],
    *,
    check: bool = True,
    capture: bool = False,
    env: dict[str, str] | None = None,
    output: Path | None = None,
) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
    kwargs: dict[str, Any] = {"cwd": ROOT, "check": check, "env": env}
    if capture:
        kwargs.update({"capture_output": True, "text": True})
    if output is not None:
        with output.open("wb") as handle:
            return subprocess.run(command, stdout=handle, stderr=subprocess.PIPE, **kwargs)
    return subprocess.run(command, **kwargs)


def compose_command(env_file: Path, *arguments: str, profile: bool = False) -> list[str]:
    command = [
        "docker",
        "compose",
        "--env-file",
        str(env_file),
        "-f",
        str(COMPOSE),
    ]
    if profile:
        command.extend(["--profile", "scheduler"])
    return [*command, *arguments]


def validate_schema(env: dict[str, str]) -> list[str]:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors: list[str] = []
    for key in schema["required"]:
        if not env.get(key):
            errors.append(f"missing:{key}")
    for key, rules in schema["properties"].items():
        value = env.get(key)
        if value is None or value == "":
            continue
        if "const" in rules and value != rules["const"]:
            errors.append(f"invalid:{key}")
        if "enum" in rules and value not in rules["enum"]:
            errors.append(f"invalid:{key}")
        if rules.get("type") == "integer":
            try:
                integer = int(value)
                if integer < rules.get("minimum", integer) or integer > rules.get(
                    "maximum", integer
                ):
                    errors.append(f"range:{key}")
            except ValueError:
                errors.append(f"type:{key}")
    return errors


def validate_secret(path: Path, name: str, *, minimum: int = 16) -> str:
    if not path.is_file():
        return f"missing_secret:{name}"
    value = path.read_text(encoding="utf-8").strip()
    if len(value) < minimum or any(marker in value.lower() for marker in PLACEHOLDERS):
        return f"weak_or_placeholder_secret:{name}"
    return ""


def openssl_executable() -> str | None:
    available = shutil.which("openssl")
    if available:
        return available
    if os.name == "nt":
        base = Path(os.environ.get("PROGRAMFILES", "C:/Program Files"))
        candidate = base / "Git/usr/bin/openssl.exe"
        if candidate.is_file():
            return str(candidate)
    return None


def openssl(*args: str, input_data: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    executable = openssl_executable()
    if executable is None:
        raise RestrictedError("OpenSSL is not available")
    return subprocess.run([executable, *args], input=input_data, capture_output=True, check=False)


def validate_certificate(env: dict[str, str]) -> list[str]:
    errors: list[str] = []
    cert = path_value(env, "PLIEGOCHECK_TLS_CERT_FILE")
    key = path_value(env, "PLIEGOCHECK_TLS_KEY_FILE")
    if not cert.is_file() or not key.is_file():
        return ["tls_files_missing"]
    parsed = openssl("x509", "-in", str(cert), "-noout", "-checkend", "0")
    if parsed.returncode:
        errors.append("certificate_invalid_or_expired")
    min_days = int(env.get("PLIEGOCHECK_TLS_MIN_DAYS", "15"))
    if openssl("x509", "-in", str(cert), "-noout", "-checkend", str(min_days * 86400)).returncode:
        errors.append("certificate_expires_soon")
    hostname = urllib.parse.urlsplit(env.get("PLIEGOCHECK_PUBLIC_BASE_URL", "")).hostname
    if hostname and openssl("x509", "-in", str(cert), "-noout", "-checkhost", hostname).returncode:
        errors.append("certificate_hostname_mismatch")
    cert_pub = openssl("x509", "-in", str(cert), "-pubkey", "-noout")
    key_pub = openssl("pkey", "-in", str(key), "-pubout")
    if cert_pub.returncode or key_pub.returncode or cert_pub.stdout != key_pub.stdout:
        errors.append("certificate_private_key_mismatch")
    return errors


def validate_configuration(env: dict[str, str]) -> tuple[list[str], list[str]]:
    errors = validate_schema(env)
    warnings: list[str] = []
    base = urllib.parse.urlsplit(env.get("PLIEGOCHECK_PUBLIC_BASE_URL", ""))
    if base.scheme != "https" or not base.hostname or base.path not in {"", "/"}:
        errors.append("public_base_url_must_be_https_origin")
    origins = [item.strip() for item in env.get("PLIEGOCHECK_ALLOWED_ORIGINS", "").split(",")]
    if "*" in origins or any(urllib.parse.urlsplit(item).scheme != "https" for item in origins):
        errors.append("allowed_origins_must_be_explicit_https")
    hosts = [item.strip().lower() for item in env.get("PLIEGOCHECK_TRUSTED_HOSTS", "").split(",")]
    if "*" in hosts or not base.hostname or base.hostname.lower() not in hosts:
        errors.append("trusted_hosts_must_include_public_host_without_wildcard")
    if any(
        marker in env.get(key, "").lower()
        for key in (
            "PLIEGOCHECK_PUBLIC_BASE_URL",
            "PLIEGOCHECK_ALLOWED_ORIGINS",
            "PLIEGOCHECK_TRUSTED_HOSTS",
        )
        for marker in PLACEHOLDERS
    ):
        errors.append("public_configuration_contains_placeholder")
    if (
        not env.get("PLIEGOCHECK_TRUSTED_PROXY_CIDRS")
        or env.get("PLIEGOCHECK_TRUSTED_PROXY_CIDRS") == "*"
    ):
        errors.append("trusted_proxy_must_be_explicit")
    if not as_bool(env.get("PLIEGOCHECK_SECURE_COOKIES")):
        errors.append("secure_cookies_required")
    if as_bool(env.get("PLIEGOCHECK_EXTERNAL_DELIVERY_ENABLED")) and as_bool(
        env.get("PLIEGOCHECK_NOTIFICATION_DRY_RUN")
    ):
        warnings.append("external_delivery_enabled_but_dry_run_remains_active")
    for key in ("PLIEGOCHECK_SESSION_SECRET_FILE", "PLIEGOCHECK_DATABASE_PASSWORD_FILE"):
        problem = validate_secret(path_value(env, key), key, minimum=32)
        if problem:
            errors.append(problem)
    database_url_path = path_value(env, "PLIEGOCHECK_DATABASE_URL_FILE")
    problem = validate_secret(database_url_path, "PLIEGOCHECK_DATABASE_URL_FILE", minimum=32)
    if problem:
        errors.append(problem)
    elif "@postgres:" not in database_url_path.read_text(encoding="utf-8"):
        errors.append("database_url_must_use_internal_postgres_host")
    storage = path_value(env, "PLIEGOCHECK_STORAGE_PATH")
    backup = path_value(env, "PLIEGOCHECK_BACKUP_PATH")
    checkout = ROOT.resolve()
    for path, name in ((storage, "storage"), (backup, "backup")):
        if path == checkout or checkout in path.parents:
            errors.append(f"{name}_must_be_outside_checkout")
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".restricted-write-probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
        except OSError:
            errors.append(f"{name}_not_writable")
    if as_bool(env.get("PLIEGOCHECK_BOOTSTRAP_ADMIN_ENABLED")):
        if not env.get("PLIEGOCHECK_BOOTSTRAP_ADMIN_EMAIL"):
            errors.append("bootstrap_email_required")
        password_ref = env.get("PLIEGOCHECK_BOOTSTRAP_ADMIN_PASSWORD_FILE")
        if not password_ref:
            errors.append("bootstrap_password_file_required")
        else:
            problem = validate_secret(
                Path(password_ref).expanduser().resolve(), "bootstrap", minimum=16
            )
            if problem:
                errors.append(problem)
    return errors, warnings


def host_checks(env_file: Path, env: dict[str, str]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for executable in ("docker",):
        if shutil.which(executable) is None:
            errors.append(f"missing_executable:{executable}")
    if openssl_executable() is None:
        errors.append("missing_executable:openssl")
    if errors:
        return errors, warnings
    if run(["docker", "info"], check=False, capture=True).returncode:
        errors.append("docker_daemon_unavailable")
    if run(["docker", "compose", "version"], check=False, capture=True).returncode:
        errors.append("docker_compose_unavailable")
    else:
        version = run(["docker", "compose", "version", "--short"], capture=True)
        match = re.match(r"v?(\d+)\.(\d+)", str(version.stdout).strip())
        if not match or tuple(map(int, match.groups())) < (2, 20):
            errors.append("docker_compose_version_below_2_20")
    total, _used, free = shutil.disk_usage(path_value(env, "PLIEGOCHECK_STORAGE_PATH"))
    if free < int(env.get("PLIEGOCHECK_MIN_FREE_GB", "5")) * 1024**3:
        errors.append("insufficient_disk")
    if total < 10 * 1024**3:
        warnings.append("small_storage_filesystem")
    if (os.cpu_count() or 0) < 2:
        warnings.append("fewer_than_two_cpus")
    if os.name == "nt":
        memory = run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory",
            ],
            check=False,
            capture=True,
        )
        try:
            if int(str(memory.stdout).strip()) < 4 * 1024**3:
                warnings.append("less_than_4gb_memory")
        except ValueError:
            warnings.append("memory_not_verified")
    hostname = urllib.parse.urlsplit(env["PLIEGOCHECK_PUBLIC_BASE_URL"]).hostname
    try:
        if hostname:
            socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        errors.append("public_hostname_dns_unresolved")
    bind = env.get("PLIEGOCHECK_BIND_ADDRESS", "127.0.0.1")
    current_proxy = run(
        compose_command(env_file, "ps", "-q", "reverse-proxy"), check=False, capture=True
    )
    proxy_running = bool(str(current_proxy.stdout).strip())
    for key, default in (("PLIEGOCHECK_HTTP_PORT", "8080"), ("PLIEGOCHECK_HTTPS_PORT", "8443")):
        port = int(env.get(key, default))
        if proxy_running:
            warnings.append(f"port_owned_by_current_deployment:{port}")
            continue
        with socket.socket() as sock:
            try:
                sock.bind((bind, port))
            except OSError:
                errors.append(f"port_unavailable:{port}")
    result = run(compose_command(env_file, "config", "--quiet"), check=False, capture=True)
    if result.returncode:
        errors.append("compose_config_invalid")
    warnings.append(f"host:{platform.system().lower()}")
    warnings.append(f"timezone:{datetime.now().astimezone().tzname() or 'unknown'}")
    warnings.append("firewall_and_vpn_require_human_verification")
    return errors, warnings


def preflight(env_file: Path) -> int:
    env = read_env(env_file)
    errors, warnings = validate_configuration(env)
    if openssl_executable():
        errors.extend(validate_certificate(env))
    else:
        errors.append("missing_executable:openssl")
    host_errors, host_warnings = host_checks(env_file, env)
    errors.extend(host_errors)
    warnings.extend(host_warnings)
    status = "FAIL" if errors else ("PASS_WITH_WARNINGS" if warnings else "PASS")
    log("restricted.preflight", status, errors=sorted(set(errors)), warnings=sorted(set(warnings)))
    return 1 if errors else 0


def compose_env(env: dict[str, str]) -> dict[str, str]:
    process_env = os.environ.copy()
    process_env.update(env)
    process_env["PLIEGOCHECK_COMMIT"] = git_value("rev-parse", "--short", "HEAD")
    return process_env


def git_value(*arguments: str) -> str:
    result = run(["git", *arguments], capture=True)
    assert isinstance(result.stdout, str)
    return result.stdout.strip()


def deploy(env_file: Path) -> int:
    if preflight(env_file):
        return 1
    env = read_env(env_file)
    process_env = compose_env(env)
    scheduler = as_bool(env.get("PLIEGOCHECK_SCHEDULER_ENABLED"))
    log("restricted.deploy.start", mode="RESTRICTED_SINGLE_HOST")
    run(compose_command(env_file, "build", "api", "web"), env=process_env)
    run(compose_command(env_file, "up", "-d", "postgres"), env=process_env)
    run(
        compose_command(
            env_file,
            "run",
            "--rm",
            "api",
            "alembic",
            "-c",
            "apps/api/alembic.ini",
            "upgrade",
            "head",
        ),
        env=process_env,
    )
    services = ["api", "worker", "web", "reverse-proxy"]
    command = compose_command(env_file, "up", "-d", *services, profile=scheduler)
    if scheduler:
        command.append("scheduler")
    run(command, env=process_env)
    if as_bool(env.get("PLIEGOCHECK_BOOTSTRAP_ADMIN_ENABLED")):
        bootstrap = path_value(env, "PLIEGOCHECK_BOOTSTRAP_ADMIN_PASSWORD_FILE")
        command = compose_command(
            env_file,
            "run",
            "--rm",
            "-T",
            "api",
            "pliegocheck-api",
            "users",
            "bootstrap-admin",
            "--email",
            env["PLIEGOCHECK_BOOTSTRAP_ADMIN_EMAIL"],
            "--display-name",
            env.get("PLIEGOCHECK_BOOTSTRAP_ADMIN_DISPLAY_NAME", "Initial administrator"),
            "--password-stdin",
        )
        with bootstrap.open("rb") as handle:
            subprocess.run(command, cwd=ROOT, env=process_env, stdin=handle, check=True)
        log("restricted.bootstrap", "PASS", action="disable_bootstrap_flag_after_first_deploy")
    return validate(env_file)


def request(
    url: str,
    cert: Path,
    *,
    origin: str | None = None,
    host: str | None = None,
) -> tuple[int, dict[str, str]]:
    context = ssl.create_default_context(cafile=str(cert))
    headers = {"User-Agent": "PliegoCheck-Restricted-Validator/1.0"}
    if origin:
        headers["Origin"] = origin
    if host:
        headers["Host"] = host
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, headers=headers), context=context, timeout=10
        ) as response:
            return response.status, {key.lower(): value for key, value in response.headers.items()}
    except urllib.error.HTTPError as exc:
        return exc.code, {key.lower(): value for key, value in exc.headers.items()}


def validate(env_file: Path) -> int:
    env = read_env(env_file)
    base = env["PLIEGOCHECK_PUBLIC_BASE_URL"].rstrip("/")
    cert = path_value(env, "PLIEGOCHECK_TLS_CERT_FILE")
    errors: list[str] = []
    live_status, headers = request(f"{base}/api/health/live", cert)
    if live_status != 200:
        errors.append("https_liveness_failed")
    for header in SECURITY_HEADERS:
        if header not in headers:
            errors.append(f"missing_header:{header}")
    ready_status, _ = request(f"{base}/api/health/ready", cert)
    if ready_status != 200:
        errors.append("readiness_failed")
    unauthorized, _ = request(f"{base}/api/auth/me", cert)
    if unauthorized != 401:
        errors.append("auth_401_failed")
    allowed = env["PLIEGOCHECK_ALLOWED_ORIGINS"].split(",")[0].strip()
    _status, allowed_headers = request(f"{base}/api/health/live", cert, origin=allowed)
    if allowed_headers.get("access-control-allow-origin") != allowed:
        errors.append("cors_allowed_origin_failed")
    _status, denied_headers = request(
        f"{base}/api/health/live", cert, origin="https://denied.example.invalid"
    )
    if "access-control-allow-origin" in denied_headers:
        errors.append("cors_denied_origin_failed")
    denied_host_status, _ = request(f"{base}/api/health/live", cert, host="denied.example.invalid")
    if denied_host_status != 400:
        errors.append("trusted_host_rejection_failed")

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args: Any, **kwargs: Any) -> None:
            return None

    hostname = urllib.parse.urlsplit(base).hostname or "localhost"
    http_port = int(env.get("PLIEGOCHECK_HTTP_PORT", "8080"))
    try:
        urllib.request.build_opener(NoRedirect).open(
            f"http://{hostname}:{http_port}/api/health/live", timeout=10
        )
        errors.append("http_redirect_missing")
    except urllib.error.HTTPError as exc:
        location = exc.headers.get("Location", "")
        if exc.code != 308 or not location.startswith("https://"):
            errors.append("http_redirect_invalid")
    rendered = run(
        compose_command(env_file, "config", "--format", "json", profile=True), capture=True
    )
    assert isinstance(rendered.stdout, str)
    config = json.loads(rendered.stdout)
    for service in ("api", "web", "postgres", "worker", "scheduler"):
        if config["services"][service].get("ports"):
            errors.append(f"internal_port_published:{service}")
    status = "PASS" if not errors else "FAIL"
    log("restricted.validate", status, errors=errors, read_only=True)
    return 1 if errors else 0


def status(env_file: Path) -> int:
    env = read_env(env_file)
    result = run(compose_command(env_file, "ps", "--format", "json"), check=False, capture=True)
    assert isinstance(result.stdout, str)
    services = []
    for line in result.stdout.splitlines():
        try:
            item = json.loads(line)
            services.append(
                {
                    "service": item.get("Service"),
                    "state": item.get("State"),
                    "health": item.get("Health"),
                }
            )
        except json.JSONDecodeError:
            continue
    backups = sorted(path_value(env, "PLIEGOCHECK_BACKUP_PATH").glob("restricted-*"))
    restore_reports = sorted(
        path_value(env, "PLIEGOCHECK_BACKUP_PATH").glob("restore-verification-*.json")
    )
    cert = path_value(env, "PLIEGOCHECK_TLS_CERT_FILE")
    cert_state = "valid" if not validate_certificate(env) else "warning"
    log(
        "restricted.status",
        "PASS",
        version=env.get("PLIEGOCHECK_VERSION", "0.1.0"),
        commit=git_value("rev-parse", "--short", "HEAD"),
        services=services,
        scheduler="enabled" if as_bool(env.get("PLIEGOCHECK_SCHEDULER_ENABLED")) else "disabled",
        secop="enabled" if as_bool(env.get("PLIEGOCHECK_SECOP_ENABLED")) else "disabled",
        notifications="dry_run"
        if as_bool(env.get("PLIEGOCHECK_NOTIFICATION_DRY_RUN"))
        else "configured",
        last_backup=backups[-1].name if backups else None,
        last_restore_verification=restore_reports[-1].name if restore_reports else None,
        retention={
            "backup_days": int(env.get("PLIEGOCHECK_BACKUP_RETENTION_DAYS", "30")),
            "confirmation_required": True,
        },
        storage_free_bytes=shutil.disk_usage(path_value(env, "PLIEGOCHECK_STORAGE_PATH")).free,
        certificate=cert_state if cert.exists() else "missing",
    )
    return 0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def backup(env_file: Path) -> int:
    env = read_env(env_file)
    root = path_value(env, "PLIEGOCHECK_BACKUP_PATH")
    lock = root / ".backup.lock"
    try:
        lock.touch(exist_ok=False)
    except FileExistsError as exc:
        raise RestrictedError("backup already running") from exc
    target = root / f"restricted-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    temporary = root / f".{target.name}.tmp"
    try:
        temporary.mkdir(mode=0o700)
        database = temporary / "database.dump"
        run(
            compose_command(
                env_file,
                "exec",
                "-T",
                "postgres",
                "pg_dump",
                "-U",
                "pliegocheck",
                "-Fc",
                "pliegocheck",
            ),
            output=database,
        )
        storage_archive = temporary / "storage.zip"
        storage = path_value(env, "PLIEGOCHECK_STORAGE_PATH")
        with zipfile.ZipFile(storage_archive, "w", zipfile.ZIP_DEFLATED) as archive:
            for file in storage.rglob("*"):
                if file.is_file() and not file.is_symlink():
                    archive.write(file, file.relative_to(storage))
        manifest = {
            "format_version": 1,
            "created_at": datetime.now(UTC).isoformat(),
            "application_version": env.get("PLIEGOCHECK_VERSION", "0.1.0"),
            "commit": git_value("rev-parse", "HEAD"),
            "schema": "alembic-head",
            "files": {
                database.name: {"sha256": sha256(database), "bytes": database.stat().st_size},
                storage_archive.name: {
                    "sha256": sha256(storage_archive),
                    "bytes": storage_archive.stat().st_size,
                },
            },
            "excludes": ["secrets", "private_keys", "environment", "logs", "temporary_files"],
        }
        (temporary / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        if os.name != "nt":
            for path in temporary.iterdir():
                path.chmod(0o600)
        temporary.rename(target)
        log("restricted.backup", "PASS", backup=target.name, files=len(manifest["files"]))
        return 0
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
        lock.unlink(missing_ok=True)


def verify_manifest(directory: Path) -> dict[str, Any]:
    manifest_path = directory / "manifest.json"
    if not manifest_path.is_file():
        raise RestrictedError("backup manifest missing")
    manifest: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, metadata in manifest.get("files", {}).items():
        path = directory / name
        if not path.is_file() or sha256(path) != metadata.get("sha256"):
            raise RestrictedError(f"backup hash mismatch: {name}")
    return manifest


def backup_verify(env_file: Path, directory: Path | None) -> int:
    env = read_env(env_file)
    candidates = sorted(path_value(env, "PLIEGOCHECK_BACKUP_PATH").glob("restricted-*"))
    selected = directory or (candidates[-1] if candidates else None)
    if selected is None:
        raise RestrictedError("no backup available")
    manifest = verify_manifest(selected.resolve())
    log("restricted.backup.verify", "PASS", backup=selected.name, files=len(manifest["files"]))
    return 0


def restore_verify(env_file: Path, directory: Path | None) -> int:
    env = read_env(env_file)
    candidates = sorted(path_value(env, "PLIEGOCHECK_BACKUP_PATH").glob("restricted-*"))
    selected = directory or (candidates[-1] if candidates else None)
    if selected is None:
        raise RestrictedError("no backup available")
    selected = selected.resolve()
    verify_manifest(selected)
    verify_db = f"pliegocheck_verify_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
    temporary = Path(tempfile.mkdtemp(prefix="pliegocheck-restore-verify-"))
    try:
        run(
            compose_command(
                env_file, "exec", "-T", "postgres", "createdb", "-U", "pliegocheck", verify_db
            )
        )
        database = selected / "database.dump"
        command = compose_command(
            env_file,
            "exec",
            "-T",
            "postgres",
            "pg_restore",
            "-U",
            "pliegocheck",
            "-d",
            verify_db,
            "--no-owner",
        )
        with database.open("rb") as handle:
            subprocess.run(command, cwd=ROOT, stdin=handle, check=True)
        storage_dir = temporary / "storage"
        storage_dir.mkdir()
        with zipfile.ZipFile(selected / "storage.zip") as archive:
            archive.extractall(storage_dir)
        file_count = sum(1 for path in storage_dir.rglob("*") if path.is_file())
        result = run(
            compose_command(
                env_file,
                "exec",
                "-T",
                "postgres",
                "psql",
                "-U",
                "pliegocheck",
                "-d",
                verify_db,
                "-Atc",
                "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'",
            ),
            capture=True,
        )
        assert isinstance(result.stdout, str)
        counts_result = run(
            compose_command(
                env_file,
                "exec",
                "-T",
                "postgres",
                "psql",
                "-U",
                "pliegocheck",
                "-d",
                verify_db,
                "-Atc",
                "SELECT json_build_object('processes',(SELECT count(*) FROM processes),"
                "'documents',(SELECT count(*) FROM process_documents),"
                "'monitors',(SELECT count(*) FROM opportunity_monitors),"
                "'alerts',(SELECT count(*) FROM opportunity_alerts),"
                "'outbox',(SELECT count(*) FROM notification_outbox_messages))",
            ),
            capture=True,
        )
        assert isinstance(counts_result.stdout, str)
        report = {
            "status": "PASS",
            "created_at": datetime.now(UTC).isoformat(),
            "backup": selected.name,
            "isolated_database": True,
            "table_count": int(result.stdout.strip()),
            "storage_file_count": file_count,
            "entity_counts": json.loads(counts_result.stdout.strip()),
            "active_environment_overwritten": False,
        }
        report_path = path_value(env, "PLIEGOCHECK_BACKUP_PATH") / (
            f"restore-verification-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.json"
        )
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        if os.name != "nt":
            report_path.chmod(0o600)
        log("restricted.restore.verify", "PASS", **report)
        return 0
    finally:
        run(
            compose_command(
                env_file,
                "exec",
                "-T",
                "postgres",
                "dropdb",
                "-U",
                "pliegocheck",
                "--if-exists",
                verify_db,
            ),
            check=False,
        )
        shutil.rmtree(temporary, ignore_errors=True)


def retention(env_file: Path, confirm: bool) -> int:
    env = read_env(env_file)
    cutoff = datetime.now(UTC) - timedelta(
        days=int(env.get("PLIEGOCHECK_BACKUP_RETENTION_DAYS", "30"))
    )
    expired = [
        path
        for path in path_value(env, "PLIEGOCHECK_BACKUP_PATH").glob("restricted-*")
        if datetime.fromtimestamp(path.stat().st_mtime, UTC) < cutoff
    ]
    if confirm:
        for path in expired:
            shutil.rmtree(path)
    log(
        "restricted.retention",
        "PASS",
        dry_run=not confirm,
        candidates=len(expired),
        deleted=len(expired) if confirm else 0,
        audit_preserved=True,
    )
    return 0


def rollback(env_file: Path, target: str | None, confirmed: bool) -> int:
    if not target or not confirmed:
        raise RestrictedError("rollback requires --target-version and --confirm-rollback")
    backup_verify(env_file, None)
    images = run(
        [
            "docker",
            "image",
            "inspect",
            f"pliegocheck-backend:{target}",
            f"pliegocheck-web:{target}",
        ],
        check=False,
        capture=True,
    )
    if images.returncode:
        raise RestrictedError("target images are not available locally")
    process_env = compose_env(read_env(env_file))
    process_env["PLIEGOCHECK_IMAGE_TAG"] = target
    run(compose_command(env_file, "stop", "worker", "scheduler"), check=False, env=process_env)
    run(
        compose_command(env_file, "up", "-d", "api", "worker", "web", "reverse-proxy"),
        env=process_env,
    )
    log("restricted.rollback", "PASS", target_version=target, database_downgrade=False)
    return validate(env_file)


def stop(env_file: Path) -> int:
    run(compose_command(env_file, "down", "--remove-orphans"), check=False)
    log(
        "restricted.stop",
        "PASS",
        volumes_preserved=True,
        backups_preserved=True,
        storage_preserved=True,
    )
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    root.add_argument("--env-file", type=Path)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("preflight", "deploy", "validate", "status", "backup", "stop"):
        commands.add_parser(name)
    verify = commands.add_parser("backup-verify")
    verify.add_argument("--backup-dir", type=Path)
    restore = commands.add_parser("restore-verify")
    restore.add_argument("--backup-dir", type=Path)
    retention_parser = commands.add_parser("retention")
    retention_parser.add_argument("--confirm-retention", action="store_true")
    rollback_parser = commands.add_parser("rollback")
    rollback_parser.add_argument("--target-version")
    rollback_parser.add_argument("--confirm-rollback", action="store_true")
    return root


def main() -> int:
    args = parser().parse_args()
    configured = args.env_file or os.environ.get("PLIEGOCHECK_RESTRICTED_ENV_FILE")
    if not configured:
        log("restricted.configuration", "FAIL", error="PLIEGOCHECK_RESTRICTED_ENV_FILE_REQUIRED")
        return 1
    env_file = Path(configured).expanduser().resolve()
    handlers = {
        "preflight": lambda: preflight(env_file),
        "deploy": lambda: deploy(env_file),
        "validate": lambda: validate(env_file),
        "status": lambda: status(env_file),
        "backup": lambda: backup(env_file),
        "backup-verify": lambda: backup_verify(env_file, args.backup_dir),
        "restore-verify": lambda: restore_verify(env_file, args.backup_dir),
        "retention": lambda: retention(env_file, args.confirm_retention),
        "rollback": lambda: rollback(env_file, args.target_version, args.confirm_rollback),
        "stop": lambda: stop(env_file),
    }
    try:
        return handlers[args.command]()
    except (RestrictedError, OSError, subprocess.CalledProcessError, ValueError) as exc:
        log(f"restricted.{args.command}", "FAIL", error=type(exc).__name__, message=str(exc)[:300])
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
