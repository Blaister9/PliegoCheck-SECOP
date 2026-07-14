"""Carga y validacion estricta de la politica versionada."""

import json
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

from pliegocheck_schemas import OpportunityComponent, OpportunityOutcome

ROOT = Path(__file__).resolve().parents[5]
POLICY_PATH = ROOT / "config" / "opportunity-policies" / "v1" / "policy.json"
TERMS_PATH = ROOT / "config" / "opportunity-policies" / "v1" / "terms.json"


@dataclass(frozen=True)
class OpportunityPolicy:
    version: str
    policy_hash: str
    raw: dict[str, Any]
    terms: dict[str, Any]

    @property
    def weights(self) -> dict[str, Decimal]:
        return {key: Decimal(str(value)) for key, value in self.raw["weights"].items()}


def canonical_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(canonical.encode()).hexdigest()


def load_policy(path: Path = POLICY_PATH, terms_path: Path = TERMS_PATH) -> OpportunityPolicy:
    raw = json.loads(path.read_text(encoding="utf-8"))
    terms = json.loads(terms_path.read_text(encoding="utf-8"))
    _validate(raw)
    return OpportunityPolicy(
        version=str(raw["version"]),
        policy_hash=canonical_hash(raw),
        raw=raw,
        terms=terms,
    )


def _validate(raw: dict[str, Any]) -> None:
    required = {
        "version",
        "effective_date",
        "components",
        "weights",
        "thresholds",
        "hard_rules",
        "urgency_rules",
        "information_rules",
        "partner_rules",
        "outcome_precedence",
        "reason_codes",
    }
    if set(raw) != required:
        raise ValueError("invalid opportunity policy keys")
    known_components = {item.value for item in OpportunityComponent}
    components = set(raw["components"])
    if components != known_components or set(raw["weights"]) != known_components:
        raise ValueError("unknown or missing opportunity component")
    total = sum(Decimal(str(value)) for value in raw["weights"].values())
    if total != Decimal("1"):
        raise ValueError("opportunity weights must sum exactly to 1")
    outcomes = {item.value for item in OpportunityOutcome}
    if set(raw["outcome_precedence"]) != outcomes:
        raise ValueError("invalid opportunity outcome precedence")
    thresholds = raw["thresholds"]
    if not (0 <= thresholds["low"] <= thresholds["potential"] <= thresholds["review_first"] <= 100):
        raise ValueError("invalid opportunity thresholds")
    if not raw["reason_codes"] or len(raw["reason_codes"]) != len(set(raw["reason_codes"])):
        raise ValueError("invalid opportunity reason codes")
