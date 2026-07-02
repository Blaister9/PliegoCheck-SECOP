"""Punto de entrada ejecutable del worker.

Uso::

    uv run pliegocheck-worker health
    uv run pliegocheck-worker run-once
    uv run pliegocheck-worker drain --max-jobs 10

Imprime el diagnostico en JSON por stdout (los logs van a stderr) y termina.
"""

import argparse
import json
import logging
import sys

from pliegocheck_worker import SERVICE_NAME, SERVICE_VERSION
from pliegocheck_worker.health import health_status
from pliegocheck_worker.runner import drain, run_once

logger = logging.getLogger(SERVICE_NAME)


def configure_logging() -> None:
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def run_health() -> int:
    logger.info("ejecutando diagnostico de %s v%s", SERVICE_NAME, SERVICE_VERSION)
    status = health_status()
    print(json.dumps(status, sort_keys=True))
    return 0 if status["status"] == "ok" else 1


def run_one(worker_id: str | None) -> int:
    result = run_once(worker_id)
    print(json.dumps(result, sort_keys=True))
    return 0


def run_drain(max_jobs: int, worker_id: str | None) -> int:
    result = drain(max_jobs=max_jobs, worker_id=worker_id)
    print(json.dumps(result, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    parser = argparse.ArgumentParser(
        prog="pliegocheck-worker",
        description=("Worker de PliegoCheck-SECOP para cola PostgreSQL de extraccion documental."),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("health", help="Imprime el estado del worker y termina")
    run_once_parser = subparsers.add_parser("run-once", help="Procesa como maximo un trabajo")
    run_once_parser.add_argument("--worker-id", default=None)
    drain_parser = subparsers.add_parser("drain", help="Procesa trabajos pendientes y termina")
    drain_parser.add_argument("--max-jobs", type=int, default=100)
    drain_parser.add_argument("--worker-id", default=None)

    args = parser.parse_args(argv)
    if args.command == "health":
        return run_health()
    if args.command == "run-once":
        return run_one(args.worker_id)
    if args.command == "drain":
        return run_drain(args.max_jobs, args.worker_id)
    parser.error(f"comando no reconocido: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
