from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCANNED = [ROOT / "deploy" / "restricted", ROOT / "docs"]


def test_no_runtime_secrets_certificates_backups_or_physical_user_paths() -> None:
    forbidden_suffixes = {".env", ".pem", ".key", ".crt", ".p12", ".dump", ".zip"}
    forbidden_markers = (
        "-----BEGIN " + "PRIVATE " + "KEY-----",
        "-----BEGIN " + "RSA " + "PRIVATE " + "KEY-----",
        "-----BEGIN " + "OPENSSH " + "PRIVATE " + "KEY-----",
        "C:" + "\\Users\\" + "santi",
        "/" + "home/" + "santi/",
    )
    violations: list[str] = []
    for directory in SCANNED:
        for path in directory.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() in forbidden_suffixes:
                violations.append(str(path.relative_to(ROOT)))
                continue
            if path.suffix.lower() not in {
                ".md",
                ".json",
                ".yaml",
                ".py",
                ".ps1",
                ".sh",
                ".conf",
                "",
            }:
                continue
            content = path.read_text(encoding="utf-8", errors="ignore")
            if any(marker in content for marker in forbidden_markers):
                violations.append(str(path.relative_to(ROOT)))
    assert violations == []


def test_example_contains_references_only() -> None:
    example = (ROOT / "deploy" / "restricted" / "restricted.env.example").read_text(
        encoding="utf-8"
    )
    assert "PLIEGOCHECK_SESSION_SECRET=" not in example
    assert "PLIEGOCHECK_DATABASE_PASSWORD=" not in example
    assert "PLIEGOCHECK_SESSION_SECRET_FILE=" in example
    assert "PLIEGOCHECK_DATABASE_PASSWORD_FILE=" in example
