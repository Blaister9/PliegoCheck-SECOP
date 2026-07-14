from pliegocheck_worker.opportunities.orchestrator import opportunity_drain, opportunity_run_once


def test_opportunity_worker_is_idle_without_jobs() -> None:
    assert opportunity_run_once("fixture-worker") == {
        "status": "idle",
        "processed": 0,
        "worker_id": "fixture-worker",
    }
    result = opportunity_drain(worker_id="fixture-worker")
    assert result["status"] == "ok"
    assert result["processed"] == 0
