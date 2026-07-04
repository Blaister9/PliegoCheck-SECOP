"""Pruebas de scripts operativos."""

from pathlib import Path


def test_backup_and_restore_scripts_exist_and_do_not_embed_env() -> None:
    backup = Path("scripts/backup-local.ps1").read_text(encoding="utf-8")
    restore = Path("scripts/restore-local.ps1").read_text(encoding="utf-8")
    assert "pg_dump" in backup
    assert "pg_restore" in restore
    assert ".env" in backup
    assert "OPENAI_API_KEY=" not in backup
    assert "PASSWORD=" not in restore


def test_backup_manifest_declares_hashes_and_excludes_secrets() -> None:
    """El backup local produce manifest con hashes y excluye .env/secretos.

    Validacion estatica multiplataforma: la ejecucion real de pg_dump requiere
    binarios de PostgreSQL y se documenta en el checklist de demo del piloto.
    """
    backup = Path("scripts/backup-local.ps1").read_text(encoding="utf-8")
    assert "manifest.json" in backup
    assert "database_sha256" in backup
    assert "storage_sha256" in backup
    assert "SHA256" in backup
    # No debe incrustar .env ni secretos en el paquete de backup.
    assert '".env"' in backup  # aparece unicamente como exclusion declarada
    for marker in (
        "OPENAI_API_KEY=",
        "AUTH_SECRET_KEY=",
        "AWS_SECRET_ACCESS_KEY=",
        "password_hash",
    ):
        assert marker not in backup


def test_pilot_documents_are_synthetic_and_secret_free() -> None:
    """Los documentos del dataset de piloto son sinteticos y no contienen secretos."""
    forbidden = (
        "OPENAI_API_KEY",
        "AWS_SECRET_ACCESS_KEY",
        "BEGIN RSA",
        "BEGIN OPENSSH",
        "password_hash",
    )
    for path in Path("pilot").rglob("*"):
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        for marker in forbidden:
            assert marker not in content, f"{path} contiene {marker}"
