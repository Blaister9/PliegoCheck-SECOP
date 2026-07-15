# mypy: ignore-errors
from unittest.mock import patch

from pliegocheck_worker.notification_delivery.orchestrator import notification_drain


@patch("pliegocheck_worker.notification_delivery.orchestrator.notification_run_once")
def test_notification_drain_stops_when_empty(run_once):
    run_once.side_effect = [{"processed": 1}, {"processed": 0}]
    assert notification_drain()["processed"] == 1
