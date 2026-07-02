"""Pruebas del diagnostico del worker."""

import json

import pytest

from pliegocheck_worker.cli import main
from pliegocheck_worker.health import health_status


def test_health_status_reports_skeleton_state() -> None:
    status = health_status()
    assert status == {
        "status": "ok",
        "service": "worker",
        "version": "0.1.0",
        "queue_connected": False,
        "document_processing_enabled": False,
    }


def test_cli_health_prints_json_and_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["health"])
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["status"] == "ok"
    assert payload["service"] == "worker"
    assert payload["queue_connected"] is False
    assert payload["document_processing_enabled"] is False


def test_cli_requires_a_command() -> None:
    with pytest.raises(SystemExit) as excinfo:
        main([])
    assert excinfo.value.code != 0
