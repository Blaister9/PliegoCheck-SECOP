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
