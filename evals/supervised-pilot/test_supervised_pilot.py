import json
from pathlib import Path

ROOT = Path(__file__).parents[2]
MANIFEST = json.loads((ROOT / "config/pilot/supervised-pilot-v1.json").read_text())
PACKAGE = json.loads((ROOT / "package.json").read_text())
SCRIPT = (ROOT / "scripts/supervised-pilot.ps1").read_text()
CONTROLLED_DEPLOY = (ROOT / "scripts/deploy-controlled.ps1").read_text()


def test_manifest_mode():
    assert MANIFEST["mode"] == "SUPERVISED_TECHNICAL_PILOT"


def test_timezone():
    assert MANIFEST["timezone"] == "America/Bogota"


def test_sources():
    assert set(MANIFEST["allowed_sources"]) <= {"SECOP_I", "SECOP_II"}


def test_search_limit():
    assert MANIFEST["max_search_results"] <= 100


def test_page_limit():
    assert MANIFEST["max_pages"] <= 2


def test_import_limit():
    assert MANIFEST["max_imported_processes"] <= 3


def test_download_limit():
    assert MANIFEST["max_document_downloads"] <= 2


def test_monitor_limit():
    assert MANIFEST["max_monitors"] <= 2


def test_alert_limit():
    assert MANIFEST["max_alerts"] <= 20


def test_dry_run_default():
    assert MANIFEST["dry_run"] is True


def test_local_delivery_only():
    assert MANIFEST["external_delivery_mode"] == "LOCAL_OR_DRY_RUN"


def test_snapshot_required():
    assert "PUBLISHED_SNAPSHOT_REQUIRED" in MANIFEST["start_conditions"]


def test_kill_switch_condition():
    assert "EXTERNAL_DELIVERY_KILL_SWITCH_OFF" in MANIFEST["start_conditions"]


def test_stop_on_secret():
    assert "SECRET_EXPOSURE" in MANIFEST["stop_conditions"]


def test_stop_on_data_loss():
    assert "DATA_LOSS" in MANIFEST["stop_conditions"]


def test_reset_confirmation():
    assert "if (-not $Confirm)" in SCRIPT


def test_stop_reuses_controlled_stop():
    assert "stop-controlled.ps1" in SCRIPT


def test_deploy_reuses_controlled_deploy():
    assert "deploy-controlled.ps1" in SCRIPT


def test_report_is_local():
    assert "var/pilot-reports" in SCRIPT


def test_human_status_conservative():
    assert "USER_VALIDATION_PENDING" in SCRIPT


def test_no_production_approval():
    assert "production_approval = $false" in SCRIPT


def test_root_commands_exist():
    expected = {
        f"pilot:supervised:{name}"
        for name in (
            "deploy",
            "validate",
            "status",
            "stop",
            "reset",
            "report",
            "opportunity-worker-once",
            "test",
            "eval",
            "data-scan",
        )
    }
    assert expected <= PACKAGE["scripts"].keys()


def test_windows_web_launcher_resolves_pnpm_cmd():
    assert "Get-Command pnpm.cmd" in CONTROLLED_DEPLOY
    assert '"dev", "--", "--hostname"' not in CONTROLLED_DEPLOY


def test_opportunity_worker_has_explicit_safe_pilot_environment():
    assert '"opportunity-worker-once"' in SCRIPT
    assert '$env:PLIEGOCHECK_SECOP_ENABLED = "true"' in SCRIPT
    for name in (
        "PLIEGOCHECK_SECOP_DOCUMENT_DOWNLOAD_ENABLED",
        "PLIEGOCHECK_EXTERNAL_DELIVERY_ENABLED",
        "PLIEGOCHECK_EMAIL_ENABLED",
        "PLIEGOCHECK_WEBHOOK_ENABLED",
    ):
        assert f'$env:{name} = "false"' in SCRIPT
    assert '$env:PLIEGOCHECK_NOTIFICATION_DRY_RUN = "true"' in SCRIPT
    assert "Get-PnpmExecutable" in SCRIPT
