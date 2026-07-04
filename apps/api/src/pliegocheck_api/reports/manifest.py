"""Manifiestos canonicos y hashes para reportes."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def stable_digest(data: Any) -> str:
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


def bytes_digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def artifact_manifest_digest(items: list[dict[str, Any]]) -> str:
    logical = [
        {
            "artifact_type": item["artifact_type"],
            "content_type": item["content_type"],
            "filename": item["filename"],
            "sha256": item["sha256"],
            "size_bytes": item["size_bytes"],
        }
        for item in sorted(items, key=lambda entry: entry["filename"])
    ]
    return stable_digest(logical)
