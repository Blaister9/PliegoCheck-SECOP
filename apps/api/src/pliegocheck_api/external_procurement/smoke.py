"""Smoke live manual y no transaccional del dataset SECOP II."""

import json
from time import perf_counter

from pliegocheck_api.config import get_settings
from pliegocheck_api.external_procurement.datos_abiertos import DatosAbiertosClient
from pliegocheck_api.external_procurement.providers import get_source_definition
from pliegocheck_api.external_procurement.secop_mapper import map_secop_process
from pliegocheck_schemas import (
    ExternalProcurementSearchRequest,
    ExternalProcurementSourceSystem,
)


def main() -> int:
    settings = get_settings()
    if not settings.secop_allow_live_tests:
        print(
            json.dumps(
                {
                    "status": "SKIPPED",
                    "reason": "PLIEGOCHECK_SECOP_ALLOW_LIVE_TESTS debe ser true",
                }
            )
        )
        return 2
    if not settings.secop_enabled:
        print(
            json.dumps({"status": "SKIPPED", "reason": "PLIEGOCHECK_SECOP_ENABLED debe ser true"})
        )
        return 2
    definition = get_source_definition(ExternalProcurementSourceSystem.SECOP_II)
    client = DatosAbiertosClient(settings)
    started = perf_counter()
    try:
        rows, unsupported = client.search(
            definition,
            ExternalProcurementSearchRequest(source_system=definition.source_system, limit=1),
        )
        normalized = map_secop_process(rows[0], definition)[0] if rows else None
        print(
            json.dumps(
                {
                    "status": "OK",
                    "source": definition.name,
                    "dataset_id": definition.dataset_id,
                    "latency_ms": round((perf_counter() - started) * 1000, 2),
                    "result_count": len(rows),
                    "normalized": normalized.model_dump(mode="json") if normalized else None,
                    "warnings": (
                        [item.model_dump(mode="json") for item in normalized.warnings]
                        if normalized
                        else []
                    ),
                    "unsupported_filters": unsupported,
                    "import_executed": False,
                },
                ensure_ascii=False,
            )
        )
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
