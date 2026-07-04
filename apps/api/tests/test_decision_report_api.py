# mypy: ignore-errors
"""Pruebas API del paquete de reporte de decision."""

from zipfile import ZipFile

from fastapi.testclient import TestClient

from pliegocheck_worker.decision.orchestrator import decision_run_once
from pliegocheck_worker.reports.orchestrator import report_run_once

from .test_decision_api import _full_pipeline


def _completed_decision(client: TestClient) -> tuple[str, str]:
    setup = _full_pipeline(client)
    process_id = setup["process"]["id"]
    response = client.post(
        f"/processes/{process_id}/decisions",
        json={
            "normalization_run_id": setup["normalization_run_id"],
            "company_id": setup["company"]["id"],
            "company_profile_snapshot_id": setup["snapshot"]["id"],
            "financial_evaluation_run_id": setup["financial_run_id"],
            "force": False,
        },
    )
    assert response.status_code == 202, response.text
    worker = decision_run_once(worker_id="report-test-decision")
    assert worker["processed"] == 1, worker
    assert worker["run_status"] in {"COMPLETED", "COMPLETED_WITH_WARNINGS"}
    return process_id, worker["run_id"]


def test_decision_report_full_flow_and_idempotency(client: TestClient) -> None:
    process_id, run_id = _completed_decision(client)
    response = client.post(
        f"/processes/{process_id}/decision-reports",
        json={"decision_run_id": run_id, "force": False},
    )
    assert response.status_code == 202, response.text
    package_id = response.json()["package"]["id"]
    worker = report_run_once(worker_id="report-test")
    assert worker["processed"] == 1, worker
    assert worker["package_status"] in {"COMPLETED", "COMPLETED_WITH_WARNINGS"}

    detail = client.get(f"/processes/{process_id}/decision-reports/{package_id}")
    assert detail.status_code == 200, detail.text
    payload = detail.json()
    assert payload["artifact_count"] == 9
    assert payload["package_digest"]
    filenames = {artifact["filename"] for artifact in payload["artifacts"]}
    assert "executive-report.html" in filenames
    assert "decision-package.zip" in filenames

    second = client.post(
        f"/processes/{process_id}/decision-reports",
        json={"decision_run_id": run_id, "force": False},
    )
    assert second.status_code == 202, second.text
    assert second.json()["reused_existing_package"] is True
    assert second.json()["package"]["id"] == package_id

    forced = client.post(
        f"/processes/{process_id}/decision-reports",
        json={"decision_run_id": run_id, "force": True},
    )
    assert forced.status_code == 202, forced.text
    assert forced.json()["package"]["id"] != package_id


def test_decision_report_preview_downloads_and_zip_are_safe(client: TestClient, tmp_path) -> None:
    process_id, run_id = _completed_decision(client)
    response = client.post(
        f"/processes/{process_id}/decision-reports",
        json={"decision_run_id": run_id, "force": False},
    )
    package_id = response.json()["package"]["id"]
    report_run_once(worker_id="report-download")

    preview = client.get(f"/processes/{process_id}/decision-reports/{package_id}/preview")
    assert preview.status_code == 200, preview.text
    assert "No constituye concepto juridico" in preview.json()["text"]

    zip_response = client.get(f"/processes/{process_id}/decision-reports/{package_id}/download")
    assert zip_response.status_code == 200, zip_response.text
    zip_path = tmp_path / "decision-package.zip"
    zip_path.write_bytes(zip_response.content)
    with ZipFile(zip_path) as archive:
        names = archive.namelist()
    assert "executive-report.html" in names
    assert ".env" not in names
    assert all("/" not in name and "\\" not in name and ".." not in name for name in names)


def test_decision_report_rejects_incomplete_decision(client: TestClient) -> None:
    setup = _full_pipeline(client)
    response = client.post(
        f"/processes/{setup['process']['id']}/decision-reports",
        json={"decision_run_id": "00000000-0000-0000-0000-000000000001"},
    )
    assert response.status_code == 404
