"""Carga y validacion de la politica de decision versionada.

La politica es un archivo JSON de parametros validados con Pydantic. Las
reglas viven tipadas en ``rules.py``; aqui no hay ``eval``, ``exec`` ni
expresiones dinamicas.
"""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from pliegocheck_schemas import DecisionOutcome

POLICY_ROOT = Path(__file__).resolve().parents[5] / "config" / "decision-policies"
ACTIVE_POLICY_DIR = "v1"


class PolicyReviewRequirements(BaseModel):
    model_config = ConfigDict(extra="forbid")

    block_positive_outcomes_on_pending_critical_review: bool = True


class PolicyGoRequirements(BaseModel):
    model_config = ConfigDict(extra="forbid")

    require_full_mandatory_coverage: bool = True
    require_all_mandatory_comply: bool = True
    forbid_pending_human_review: bool = True
    forbid_conflicts: bool = True


class PolicyGoConditionedRequirements(BaseModel):
    model_config = ConfigDict(extra="forbid")

    require_full_mandatory_coverage: bool = True
    require_explicit_condition_codes: bool = True
    require_action_per_gap: bool = True


class PolicyPartnerRequirements(BaseModel):
    model_config = ConfigDict(extra="forbid")

    require_explicit_partner_solvable: bool = True
    forbid_unresolved_critical_conflicts: bool = True


class PolicyNoGoRequirements(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criticalities: list[str] = Field(min_length=1)
    require_mandatory_applicable: bool = True
    exclude_remediable_with_condition: bool = True
    exclude_partner_solvable: bool = True


class PolicyNoCargarRequirements(BaseModel):
    model_config = ConfigDict(extra="forbid")

    require_explicit_submission_blocker: bool = True


class DecisionPolicy(BaseModel):
    """Parametros validados de la politica de decision."""

    model_config = ConfigDict(extra="forbid")

    policy_name: str = Field(min_length=1, max_length=128)
    semantic_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    required_categories_mode: str = Field(min_length=1)
    required_outcomes: list[str] = Field(min_length=1)
    precedence: list[DecisionOutcome] = Field(min_length=6, max_length=6)
    blocking_criticalities: list[str] = Field(min_length=1)
    positive_review_requirements: PolicyReviewRequirements
    unknown_behavior: DecisionOutcome
    conflict_behavior: DecisionOutcome
    partial_behavior: DecisionOutcome
    optional_requirement_behavior: str
    not_applicable_behavior: str
    go_requirements: PolicyGoRequirements
    go_conditioned_requirements: PolicyGoConditionedRequirements
    partner_requirements: PolicyPartnerRequirements
    no_go_requirements: PolicyNoGoRequirements
    no_cargar_requirements: PolicyNoCargarRequirements

    @field_validator("precedence")
    @classmethod
    def precedence_is_total(cls, value: list[DecisionOutcome]) -> list[DecisionOutcome]:
        if set(value) != set(DecisionOutcome):
            raise ValueError("la precedencia debe incluir los seis resultados exactamente una vez")
        return value

    @field_validator("unknown_behavior", "conflict_behavior", "partial_behavior")
    @classmethod
    def uncertainty_never_positive(cls, value: DecisionOutcome) -> DecisionOutcome:
        if value in {
            DecisionOutcome.GO,
            DecisionOutcome.GO_CONDICIONADO,
            DecisionOutcome.BUSCAR_ALIADO,
        }:
            raise ValueError(
                "la ausencia de informacion nunca puede producir un resultado positivo"
            )
        return value

    def outcome_rank(self, outcome: DecisionOutcome) -> int:
        return self.precedence.index(outcome)


class PolicyLoadError(Exception):
    """La politica no existe o no es valida."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def policy_content_sha256(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(canonical.encode("utf-8")).hexdigest()


def load_active_policy(
    policy_dir: str = ACTIVE_POLICY_DIR,
) -> tuple[DecisionPolicy, dict[str, Any], str]:
    """Carga la politica activa: (politica validada, payload crudo, hash)."""
    path = POLICY_ROOT / policy_dir / "policy.json"
    if not path.is_file():
        raise PolicyLoadError(
            "DECISION_POLICY_NOT_FOUND",
            f"No existe la politica de decision en {policy_dir}/policy.json.",
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PolicyLoadError(
            "DECISION_POLICY_INVALID",
            "La politica de decision no es JSON valido.",
        ) from exc
    try:
        policy = DecisionPolicy.model_validate(payload)
    except ValidationError as exc:
        raise PolicyLoadError(
            "DECISION_POLICY_INVALID",
            "La politica de decision no cumple el esquema de parametros.",
        ) from exc
    return policy, payload, policy_content_sha256(payload)
