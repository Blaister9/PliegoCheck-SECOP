"""Pruebas del diagnostico del worker."""

import json

import pytest

from pliegocheck_worker.cli import main
from pliegocheck_worker.health import health_status


def test_health_status_reports_queue_state() -> None:
    status = health_status()
    assert status == {
        "status": "ok",
        "service": "worker",
        "version": "0.1.0",
        "queue_connected": True,
        "document_processing_enabled": True,
        "company_evidence_extraction_enabled": True,
        "financial_evaluation_enabled": True,
        "requirement_normalization_enabled": True,
        "normalization_provider": "fake",
        "normalization_model": "gpt-5.5-pro",
        "decision_engine_enabled": True,
        "decision_policy_version": "1.0.0",
        "available_decision_adapters": ["FINANCIAL"],
    }


def test_cli_health_prints_json_and_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["health"])
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["status"] == "ok"
    assert payload["service"] == "worker"
    assert payload["queue_connected"] is True
    assert payload["document_processing_enabled"] is True
    assert payload["company_evidence_extraction_enabled"] is True
    assert payload["financial_evaluation_enabled"] is True
    assert payload["requirement_normalization_enabled"] is True


def test_cli_requires_a_command() -> None:
    with pytest.raises(SystemExit) as excinfo:
        main([])
    assert excinfo.value.code != 0
