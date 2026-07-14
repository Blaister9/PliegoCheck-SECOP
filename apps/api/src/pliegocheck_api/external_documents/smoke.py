"""Smoke live opt-in: solo disponibilidad y esquema, nunca guarda payloads ni documentos."""

from __future__ import annotations

import json

import httpx

from pliegocheck_api.config import get_settings


def main() -> int:
    settings = get_settings()
    if not settings.secop_document_allow_live_tests:
        print(
            json.dumps(
                {
                    "status": "skipped",
                    "reason": "PLIEGOCHECK_SECOP_DOCUMENT_ALLOW_LIVE_TESTS=false",
                },
                sort_keys=True,
            )
        )
        return 0
    results: list[dict[str, object]] = []
    with httpx.Client(
        base_url=settings.secop_base_url,
        timeout=settings.secop_timeout_seconds,
        headers={"Accept": "application/json", "User-Agent": "PliegoCheck-SECOP/0.17 smoke"},
    ) as client:
        for source, dataset in (("SECOP_II", "dmgg-8hin"), ("SECOP_I", "ps88-5e3v")):
            response = client.get(f"/resource/{dataset}.json", params={"$limit": "1"})
            payload = response.json() if response.is_success else []
            results.append(
                {
                    "source": source,
                    "dataset": dataset,
                    "http_status": response.status_code,
                    "schema_available": bool(payload and isinstance(payload[0], dict)),
                    "download_attempted": False,
                }
            )
    print(json.dumps({"status": "ok", "results": results, "persisted": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
