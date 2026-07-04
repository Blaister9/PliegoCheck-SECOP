"""Manifiesto de inputs, digest estable e idempotencia de la decision.

El digest se calcula sobre JSON canonico y excluye ``effective_at``: el reloj
efectivo se persiste y se reutiliza en reintentos, pero no forma parte de la
clave de idempotencia (no se usa tiempo actual arbitrario dentro del digest).
"""

from __future__ import annotations

import json
from hashlib import sha256
from typing import Any

DIGEST_EXCLUDED_KEYS = {"effective_at"}


def stable_decision_digest(manifest: dict[str, Any]) -> str:
    filtered = {key: value for key, value in manifest.items() if key not in DIGEST_EXCLUDED_KEYS}
    canonical = json.dumps(filtered, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(canonical.encode("utf-8")).hexdigest()


def build_decision_manifest(
    *,
    process: Any,
    normalization_run: Any,
    snapshot: Any,
    financial_run: Any,
    requirements: list[Any],
    policy_name: str,
    policy_version: str,
    policy_hash: str,
    engine_version: str,
    effective_at: str,
) -> dict[str, Any]:
    return {
        "process_id": str(process.id),
        "process_updated_at": process.updated_at.isoformat() if process.updated_at else None,
        "normalization_run_id": str(normalization_run.id),
        "normalization_input_digest": getattr(normalization_run, "input_digest", None),
        "company_id": str(snapshot.company_id),
        "company_profile_snapshot_id": str(snapshot.id),
        "company_snapshot_digest": snapshot.digest,
        "financial_evaluation_run_id": str(financial_run.id),
        "financial_evaluation_input_digest": financial_run.input_digest,
        "requirement_ids": sorted(str(requirement.id) for requirement in requirements),
        "finding_source_ids": [str(financial_run.id)],
        "policy_name": policy_name,
        "policy_version": policy_version,
        "policy_hash": policy_hash,
        "engine_version": engine_version,
        "effective_at": effective_at,
    }
