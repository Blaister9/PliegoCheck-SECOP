# mypy: ignore-errors
from unittest.mock import MagicMock, patch

from pliegocheck_worker.opportunity_monitoring.orchestrator import monitor_drain


@patch("pliegocheck_worker.opportunity_monitoring.orchestrator.monitor_run_once")
def test_monitor_drain_stops_when_queue_is_empty(run_once: MagicMock):
    run_once.side_effect = [{"processed": 1}, {"processed": 0}]
    assert monitor_drain()["processed"] == 1
