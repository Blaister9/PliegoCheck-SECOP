"""Punto de entrada ejecutable del worker.

Uso::

    uv run pliegocheck-worker health
    uv run pliegocheck-worker run-once
    uv run pliegocheck-worker drain --max-jobs 10
    uv run pliegocheck-worker financial-run-once
    uv run pliegocheck-worker financial-drain --max-jobs 10

Imprime el diagnostico en JSON por stdout (los logs van a stderr) y termina.
"""

import argparse
import json
import logging
import sys

from pliegocheck_worker import SERVICE_NAME, SERVICE_VERSION
from pliegocheck_worker.decision.orchestrator import (
    decision_drain,
    decision_run_once,
)
from pliegocheck_worker.external_documents.orchestrator import (
    external_download_drain,
    external_download_run_once,
    external_sync_drain,
    external_sync_run_once,
)
from pliegocheck_worker.financial.orchestrator import (
    financial_drain,
    financial_run_once,
)
from pliegocheck_worker.health import health_status
from pliegocheck_worker.normalization.orchestrator import (
    normalization_drain,
    normalization_run_once,
)
from pliegocheck_worker.normalization.providers import (
    NormalizationBatchRequest,
    OpenAIResponsesNormalizationProvider,
)
from pliegocheck_worker.opportunities.orchestrator import (
    opportunity_drain,
    opportunity_run_once,
)
from pliegocheck_worker.opportunity_monitoring.orchestrator import (
    monitor_drain,
    monitor_run_once,
    monitor_scheduler_run_once,
)
from pliegocheck_worker.reports.orchestrator import report_drain, report_run_once
from pliegocheck_worker.runner import drain, run_once
from pliegocheck_worker.specialized.orchestrator import (
    specialized_drain,
    specialized_run_once,
)

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


def run_normalization_once(worker_id: str | None, provider: str | None) -> int:
    _validate_provider(provider)
    result = normalization_run_once(worker_id=worker_id, provider_name=provider)
    print(json.dumps(result, sort_keys=True))
    return 0


def run_normalization_drain(max_jobs: int, worker_id: str | None, provider: str | None) -> int:
    _validate_provider(provider)
    result = normalization_drain(max_jobs=max_jobs, worker_id=worker_id, provider_name=provider)
    print(json.dumps(result, sort_keys=True))
    return 0


def run_financial_once(worker_id: str | None) -> int:
    result = financial_run_once(worker_id=worker_id)
    print(json.dumps(result, sort_keys=True))
    return 0


def run_financial_drain(max_jobs: int, worker_id: str | None) -> int:
    result = financial_drain(max_jobs=max_jobs, worker_id=worker_id)
    print(json.dumps(result, sort_keys=True))
    return 0


def run_decision_once(worker_id: str | None) -> int:
    result = decision_run_once(worker_id=worker_id)
    print(json.dumps(result, sort_keys=True))
    return 0


def run_decision_drain(max_jobs: int, worker_id: str | None) -> int:
    result = decision_drain(max_jobs=max_jobs, worker_id=worker_id)
    print(json.dumps(result, sort_keys=True))
    return 0


def run_report_once(worker_id: str | None) -> int:
    result = report_run_once(worker_id=worker_id)
    print(json.dumps(result, sort_keys=True))
    return 0


def run_report_drain(max_jobs: int, worker_id: str | None) -> int:
    result = report_drain(max_jobs=max_jobs, worker_id=worker_id)
    print(json.dumps(result, sort_keys=True))
    return 0


def run_specialized_once(worker_id: str | None) -> int:
    result = specialized_run_once(worker_id=worker_id)
    print(json.dumps(result, sort_keys=True))
    return 0


def run_specialized_drain(max_jobs: int, worker_id: str | None) -> int:
    result = specialized_drain(max_jobs=max_jobs, worker_id=worker_id)
    print(json.dumps(result, sort_keys=True))
    return 0


def run_pilot_prepare(password: str | None) -> int:
    from pliegocheck_worker.pilot.orchestrator import DEFAULT_DEMO_PASSWORD, prepare_pilot

    result = prepare_pilot(password=password or DEFAULT_DEMO_PASSWORD)
    print(json.dumps(result, sort_keys=True))
    return 0


def run_pilot_run(password: str | None) -> int:
    from pliegocheck_worker.pilot.orchestrator import DEFAULT_DEMO_PASSWORD, run_pilot

    summary = run_pilot(password=password or DEFAULT_DEMO_PASSWORD)
    print(json.dumps(summary.model_dump(mode="json"), sort_keys=True))
    return 0


def run_pilot_reset(confirm: bool) -> int:
    from pliegocheck_worker.pilot.orchestrator import reset_pilot

    if not confirm:
        print(
            json.dumps(
                {
                    "status": "aborted",
                    "reason": "reset requiere --confirm para eliminar datos de piloto",
                },
                sort_keys=True,
            )
        )
        return 1
    result = reset_pilot(confirm=True)
    print(json.dumps(result, sort_keys=True))
    return 0


def run_pilot_readiness() -> int:
    from pliegocheck_worker.pilot.orchestrator import pilot_readiness

    readiness = pilot_readiness()
    print(json.dumps(readiness.model_dump(mode="json"), sort_keys=True))
    return 0


def run_normalization_smoke() -> int:
    from uuid import UUID

    from pliegocheck_api.config import get_settings

    settings = get_settings()
    if not settings.ai_enabled or not settings.openai_api_key:
        print(
            json.dumps(
                {
                    "status": "skipped",
                    "reason": "OPENAI_API_KEY no disponible o IA deshabilitada.",
                },
                sort_keys=True,
            )
        )
        return 0
    provider = OpenAIResponsesNormalizationProvider(settings)
    fake_segment_id = UUID("00000000-0000-0000-0000-000000000001")
    result = provider.normalize_batch(
        NormalizationBatchRequest(
            process_id=UUID("00000000-0000-0000-0000-000000000010"),
            batch_index=0,
            prompt_version="smoke",
            system_prompt=(
                "Devuelve solo JSON valido del esquema. Extrae requisitos con evidencia."
            ),
            user_template="{{segments_json}}",
            segments=[
                {
                    "segment_id": str(fake_segment_id),
                    "text": "El proponente debe acreditar indice de liquidez minimo de 1.2.",
                    "source_location": {"page_number": 1},
                    "page_number": 1,
                }
            ],
        )
    )
    print(
        json.dumps(
            {
                "status": "ok",
                "response_id": result.response_id,
                "usage": result.usage.__dict__,
                "candidate_count": len(result.output.candidates)
                if hasattr(result.output, "candidates")
                else 0,
            },
            sort_keys=True,
        )
    )
    return 0


def _validate_provider(provider: str | None) -> None:
    if provider == "fake":
        from pliegocheck_api.config import get_settings

        if not get_settings().allow_fake_normalization_provider:
            raise SystemExit(
                "El proveedor fake requiere PLIEGOCHECK_ALLOW_FAKE_NORMALIZATION_PROVIDER=true"
            )


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
    normalization_once = subparsers.add_parser(
        "normalization-run-once",
        help="Procesa como maximo una normalizacion de requisitos",
    )
    normalization_once.add_argument("--worker-id", default=None)
    normalization_once.add_argument("--provider", choices=["openai", "fake"], default=None)
    normalization_drain_parser = subparsers.add_parser(
        "normalization-drain",
        help="Procesa normalizaciones pendientes y termina",
    )
    normalization_drain_parser.add_argument("--max-jobs", type=int, default=100)
    normalization_drain_parser.add_argument("--worker-id", default=None)
    normalization_drain_parser.add_argument("--provider", choices=["openai", "fake"], default=None)
    financial_once = subparsers.add_parser(
        "financial-run-once",
        help="Procesa como maximo una evaluacion financiera",
    )
    financial_once.add_argument("--worker-id", default=None)
    financial_drain_parser = subparsers.add_parser(
        "financial-drain",
        help="Procesa evaluaciones financieras pendientes y termina",
    )
    financial_drain_parser.add_argument("--max-jobs", type=int, default=100)
    financial_drain_parser.add_argument("--worker-id", default=None)
    decision_once = subparsers.add_parser(
        "decision-run-once",
        help="Procesa como maximo una decision preliminar",
    )
    decision_once.add_argument("--worker-id", default=None)
    decision_drain_parser = subparsers.add_parser(
        "decision-drain",
        help="Procesa decisiones pendientes y termina",
    )
    decision_drain_parser.add_argument("--max-jobs", type=int, default=100)
    decision_drain_parser.add_argument("--worker-id", default=None)
    report_once = subparsers.add_parser(
        "report-run-once",
        help="Procesa como maximo un paquete de reporte de decision",
    )
    report_once.add_argument("--worker-id", default=None)
    report_drain_parser = subparsers.add_parser(
        "report-drain",
        help="Procesa paquetes de reporte pendientes y termina",
    )
    report_drain_parser.add_argument("--max-jobs", type=int, default=100)
    report_drain_parser.add_argument("--worker-id", default=None)
    specialized_once = subparsers.add_parser(
        "specialized-run-once",
        help="Procesa como maximo una evaluacion especializada",
    )
    specialized_once.add_argument("--worker-id", default=None)
    specialized_drain_parser = subparsers.add_parser(
        "specialized-drain",
        help="Procesa evaluaciones especializadas pendientes y termina",
    )
    specialized_drain_parser.add_argument("--max-jobs", type=int, default=100)
    specialized_drain_parser.add_argument("--worker-id", default=None)
    for name, help_text in (
        ("secop-sync-run-once", "Procesa una sincronizacion SECOP"),
        ("secop-download-run-once", "Procesa una descarga SECOP"),
        ("external-sync-run-once", "Procesa una sincronizacion SECOP"),
        ("external-document-download-run-once", "Procesa una descarga SECOP"),
    ):
        item = subparsers.add_parser(name, help=help_text)
        item.add_argument("--worker-id", default=None)
    for name in (
        "opportunity-discovery-run-once",
        "opportunity-assessment-run-once",
    ):
        item = subparsers.add_parser(name, help="Procesa una ejecucion de oportunidades")
        item.add_argument("--worker-id", default=None)
    for name in (
        "opportunity-discovery-drain",
        "opportunity-assessment-drain",
    ):
        item = subparsers.add_parser(name, help="Drena ejecuciones de oportunidades")
        item.add_argument("--max-jobs", type=int, default=100)
        item.add_argument("--worker-id", default=None)
    subparsers.add_parser(
        "opportunity-monitor-scheduler-run-once", help="Reclama monitores vencidos"
    )
    monitor_once = subparsers.add_parser(
        "opportunity-monitor-run-once", help="Procesa una ejecución de monitor"
    )
    monitor_once.add_argument("--worker-id", default=None)
    monitor_drain_parser = subparsers.add_parser(
        "opportunity-monitor-drain", help="Drena ejecuciones de monitores"
    )
    monitor_drain_parser.add_argument("--max-jobs", type=int, default=100)
    monitor_drain_parser.add_argument("--worker-id", default=None)
    for name, help_text in (
        ("secop-sync-drain", "Drena sincronizaciones SECOP"),
        ("secop-download-drain", "Drena descargas SECOP"),
        ("external-sync-drain", "Drena sincronizaciones SECOP"),
        ("external-document-download-drain", "Drena descargas SECOP"),
    ):
        item = subparsers.add_parser(name, help=help_text)
        item.add_argument("--max-jobs", type=int, default=100)
        item.add_argument("--worker-id", default=None)
    subparsers.add_parser(
        "normalization-smoke",
        help="Prueba manual opcional contra OpenAI con fixture sintetico",
    )
    pilot_prepare = subparsers.add_parser(
        "pilot-prepare",
        help="Siembra el dataset sintetico de piloto (usuarios, proceso, empresa)",
    )
    pilot_prepare.add_argument("--password", default=None)
    pilot_run = subparsers.add_parser(
        "pilot-run",
        help="Ejecuta el flujo end-to-end del piloto y devuelve un resumen JSON",
    )
    pilot_run.add_argument("--password", default=None)
    pilot_reset = subparsers.add_parser(
        "pilot-reset",
        help="Elimina unicamente datos de piloto (requiere --confirm)",
    )
    pilot_reset.add_argument("--confirm", action="store_true")
    subparsers.add_parser("pilot-readiness", help="Diagnostico de preparacion del piloto")

    args = parser.parse_args(argv)
    if args.command == "health":
        return run_health()
    if args.command == "run-once":
        return run_one(args.worker_id)
    if args.command == "drain":
        return run_drain(args.max_jobs, args.worker_id)
    if args.command == "normalization-run-once":
        return run_normalization_once(args.worker_id, args.provider)
    if args.command == "normalization-drain":
        return run_normalization_drain(args.max_jobs, args.worker_id, args.provider)
    if args.command == "financial-run-once":
        return run_financial_once(args.worker_id)
    if args.command == "financial-drain":
        return run_financial_drain(args.max_jobs, args.worker_id)
    if args.command == "decision-run-once":
        return run_decision_once(args.worker_id)
    if args.command == "decision-drain":
        return run_decision_drain(args.max_jobs, args.worker_id)
    if args.command == "report-run-once":
        return run_report_once(args.worker_id)
    if args.command == "report-drain":
        return run_report_drain(args.max_jobs, args.worker_id)
    if args.command == "specialized-run-once":
        return run_specialized_once(args.worker_id)
    if args.command == "specialized-drain":
        return run_specialized_drain(args.max_jobs, args.worker_id)
    if args.command in {"secop-sync-run-once", "external-sync-run-once"}:
        print(json.dumps(external_sync_run_once(args.worker_id), sort_keys=True))
        return 0
    if args.command in {"secop-sync-drain", "external-sync-drain"}:
        print(json.dumps(external_sync_drain(args.max_jobs, args.worker_id), sort_keys=True))
        return 0
    if args.command in {
        "secop-download-run-once",
        "external-document-download-run-once",
    }:
        print(json.dumps(external_download_run_once(args.worker_id), sort_keys=True))
        return 0
    if args.command in {"secop-download-drain", "external-document-download-drain"}:
        print(json.dumps(external_download_drain(args.max_jobs, args.worker_id), sort_keys=True))
        return 0
    if args.command in {
        "opportunity-discovery-run-once",
        "opportunity-assessment-run-once",
    }:
        print(json.dumps(opportunity_run_once(args.worker_id), sort_keys=True))
        return 0
    if args.command in {
        "opportunity-discovery-drain",
        "opportunity-assessment-drain",
    }:
        print(json.dumps(opportunity_drain(args.max_jobs, args.worker_id), sort_keys=True))
        return 0
    if args.command == "opportunity-monitor-scheduler-run-once":
        print(json.dumps(monitor_scheduler_run_once(), sort_keys=True))
        return 0
    if args.command == "opportunity-monitor-run-once":
        print(json.dumps(monitor_run_once(args.worker_id), sort_keys=True))
        return 0
    if args.command == "opportunity-monitor-drain":
        print(json.dumps(monitor_drain(args.max_jobs, args.worker_id), sort_keys=True))
        return 0
    if args.command == "normalization-smoke":
        return run_normalization_smoke()
    if args.command == "pilot-prepare":
        return run_pilot_prepare(args.password)
    if args.command == "pilot-run":
        return run_pilot_run(args.password)
    if args.command == "pilot-reset":
        return run_pilot_reset(args.confirm)
    if args.command == "pilot-readiness":
        return run_pilot_readiness()
    parser.error(f"comando no reconocido: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
