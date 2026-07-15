"""Loops conservadores para worker y scheduler del host restringido."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

HEARTBEAT = Path("/tmp/pliegocheck-heartbeat")


def run(command: list[str]) -> None:
    subprocess.run(command, check=False, timeout=300)
    HEARTBEAT.touch()


def worker() -> None:
    commands = [
        ["pliegocheck-worker", "run-once"],
        ["pliegocheck-worker", "opportunity-discovery-run-once"],
        ["pliegocheck-worker", "opportunity-assessment-run-once"],
        ["pliegocheck-worker", "external-sync-run-once"],
        ["pliegocheck-worker", "external-document-download-run-once"],
        ["pliegocheck-worker", "opportunity-monitor-run-once"],
        ["pliegocheck-worker", "notification-delivery-run-once"],
        ["pliegocheck-worker", "notification-digest-run-once"],
    ]
    while True:
        for command in commands:
            run(command)
        time.sleep(10)


def scheduler() -> None:
    if os.environ.get("PLIEGOCHECK_SCHEDULER_ENABLED", "false").lower() != "true":
        raise SystemExit("scheduler requiere opt-in explicito")
    while True:
        run(["pliegocheck-worker", "opportunity-monitor-scheduler-run-once"])
        time.sleep(int(os.environ.get("PLIEGOCHECK_MONITOR_SCHEDULER_INTERVAL_SECONDS", "60")))


if len(sys.argv) != 2 or sys.argv[1] not in {"worker", "scheduler"}:
    raise SystemExit("uso: restricted-runtime.py worker|scheduler")
worker() if sys.argv[1] == "worker" else scheduler()
