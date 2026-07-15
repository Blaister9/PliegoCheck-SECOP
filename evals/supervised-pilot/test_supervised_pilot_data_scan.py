import re
from pathlib import Path

ROOT = Path(__file__).parents[2]
SCANNED = [
    ROOT / "config/pilot",
    ROOT / "pilot/supervised-delivery",
    ROOT / "pilot/user-validation",
]
SCANNED_FILES = [
    ROOT / "docs/pilot-readiness-assessment.md",
    ROOT / "docs/supervised-pilot-findings.md",
    ROOT / "docs/pilot-incident-log.md",
    ROOT / "docs/supervised-pilot-scorecard.md",
    ROOT / "docs/pilot-go-no-go.md",
]
SECRET_ASSIGNMENT = re.compile(
    r"(?i)(?:password|secret|token|api[_-]?key)\s*[:=]\s*['\"]?(?!NOT_PROVIDED|PENDING|CHANGEME|false|true|$)[A-Za-z0-9_./+-]{12,}"
)


def files():
    return [
        path for base in SCANNED if base.exists() for path in base.rglob("*") if path.is_file()
    ] + SCANNED_FILES


def test_no_secret_assignments():
    hits = [
        str(path.relative_to(ROOT))
        for path in files()
        if SECRET_ASSIGNMENT.search(path.read_text(encoding="utf-8", errors="ignore"))
    ]
    assert hits == []


def test_no_live_payload_files():
    assert not list((ROOT / "pilot").rglob("*payload*live*"))


def test_no_live_documents():
    assert not (ROOT / "pilot/supervised-delivery/documents").exists()


def test_no_generated_reports():
    assert (
        not (ROOT / "var/pilot-reports").is_relative_to(ROOT)
        or "var/" in (ROOT / ".gitignore").read_text()
    )


def test_no_email_in_manifest():
    assert "@" not in (ROOT / "config/pilot/supervised-pilot-v1.json").read_text()


def test_no_windows_user_paths():
    hits = [
        str(path.relative_to(ROOT))
        for path in files()
        if "C:\\Users\\" in path.read_text(encoding="utf-8", errors="ignore")
    ]
    assert hits == []


def test_participant_not_invented():
    assert (
        "participant: NOT_PROVIDED"
        in (ROOT / "pilot/user-validation/pilot-session-minutes.md").read_text()
    )


def test_feedback_pending():
    assert (
        "USER_VALIDATION_PENDING" in (ROOT / "pilot/user-validation/feedback-form.md").read_text()
    )
