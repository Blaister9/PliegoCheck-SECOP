"""Punto de entrada ejecutable del worker.

Uso::

    uv run pliegocheck-worker health

Imprime el diagnostico en JSON por stdout (los logs van a stderr) y termina.
"""

import argparse
import json
import logging
import sys

from pliegocheck_worker import SERVICE_NAME, SERVICE_VERSION
from pliegocheck_worker.health import health_status

logger = logging.getLogger(SERVICE_NAME)


def configure_logging() -> None:
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def run_health() -> int:
    logger.info("ejecutando diagnostico de %s v%s", SERVICE_NAME, SERVICE_VERSION)
    print(json.dumps(health_status(), sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    parser = argparse.ArgumentParser(
        prog="pliegocheck-worker",
        description=(
            "Worker de PliegoCheck-SECOP. Esqueleto de la Microfase 1: todavia no procesa trabajos."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("health", help="Imprime el estado del worker y termina")

    args = parser.parse_args(argv)
    if args.command == "health":
        return run_health()
    parser.error(f"comando no reconocido: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
