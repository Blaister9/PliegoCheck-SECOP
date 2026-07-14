"""Motor puro y conservador de alertas explicables."""

import hashlib
import json
from decimal import Decimal

from pliegocheck_schemas import OpportunityAlertRules

from .models import AlertDecision, CandidateChange, CandidateSnapshot

_RANK = {
    "DESCARTAR": 0,
    "POCO_COMPATIBLE": 1,
    "PENDIENTE_INFORMACION": 2,
    "REQUIERE_ALIADO": 3,
    "OPORTUNIDAD_POTENCIAL": 4,
    "REVISAR_PRIMERO": 5,
}


def alert_fingerprint(
    monitor_id: str,
    snapshot: CandidateSnapshot,
    decision: AlertDecision,
    policy_hash: str,
    company_snapshot_id: str,
) -> str:
    payload = [
        monitor_id,
        snapshot.source_system,
        snapshot.source_process_id,
        decision.alert_type,
        decision.material_identity,
        policy_hash,
        company_snapshot_id,
    ]
    return hashlib.sha256(
        json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def initial_alerts(current: CandidateSnapshot, rules: OpportunityAlertRules) -> list[AlertDecision]:
    if current.information_completeness < Decimal(str(rules.minimum_information_completeness)):
        return []
    if current.compatibility_score < Decimal(str(rules.minimum_compatibility_score)):
        return []
    mapping = {
        "REVISAR_PRIMERO": (
            rules.new_review_first,
            "NEW_REVIEW_FIRST",
            "HIGH",
            "Nueva oportunidad prioritaria",
        ),
        "OPORTUNIDAD_POTENCIAL": (
            rules.new_potential,
            "NEW_POTENTIAL_OPPORTUNITY",
            "MEDIUM",
            "Nueva oportunidad potencial",
        ),
        "REQUIERE_ALIADO": (
            rules.partner_needed,
            "NEW_PARTNER_NEEDED",
            "MEDIUM",
            "Nueva oportunidad que requiere aliado",
        ),
    }
    configured = mapping.get(current.outcome)
    if not configured or not configured[0]:
        return []
    return [
        AlertDecision(
            configured[1],
            configured[2],
            configured[3],
            f"El proceso alcanzó {current.outcome} con compatibilidad "
            f"{current.compatibility_score} y completitud {current.information_completeness}.",
            "NEW_RELEVANT_OPPORTUNITY",
            {"outcome": current.outcome, "compatibility_score": str(current.compatibility_score)},
            f"initial:{current.outcome}:{current.assessment_digest}",
        )
    ]


def changed_alerts(
    current: CandidateSnapshot, changes: list[CandidateChange], rules: OpportunityAlertRules
) -> list[AlertDecision]:
    alerts: list[AlertDecision] = []
    changed_kinds = {item.kind for item in changes}
    for change in changes:
        if change.kind == "outcome" and rules.outcome_changes:
            improved = _RANK.get(str(change.new), 0) > _RANK.get(str(change.old), 0)
            kind = "OUTCOME_IMPROVED" if improved else "OUTCOME_WORSENED"
            severity = "MEDIUM" if improved else "HIGH"
            alerts.append(
                AlertDecision(
                    kind,
                    severity,
                    "Cambio de resultado",
                    f"El resultado cambió de {change.old} a {change.new}.",
                    kind,
                    {"previous": change.old, "current": change.new},
                    f"outcome:{change.old}:{change.new}",
                )
            )
        elif change.kind == "compatibility_score" and rules.compatibility_changes:
            delta = Decimal(str(change.new)) - Decimal(str(change.old))
            if abs(delta) >= Decimal(str(rules.compatibility_change_threshold)):
                kind = "COMPATIBILITY_INCREASED" if delta > 0 else "COMPATIBILITY_DECREASED"
                alerts.append(
                    AlertDecision(
                        kind,
                        "MEDIUM",
                        "Cambio material de compatibilidad",
                        f"La compatibilidad cambió de {change.old} a {change.new}.",
                        kind,
                        {"previous": str(change.old), "current": str(change.new)},
                        f"score:{change.old}:{change.new}",
                    )
                )
        elif change.kind == "urgency_status":
            if change.new == "CRITICAL" and rules.critical_deadline:
                alerts.append(
                    AlertDecision(
                        "OPPORTUNITY_NOW_CRITICAL",
                        "CRITICAL",
                        "Cierre crítico",
                        "El proceso requiere atención por proximidad de cierre.",
                        "CRITICAL_DEADLINE",
                        {},
                        f"urgency:{change.new}:{current.closing_date}",
                    )
                )
            elif change.new == "URGENT" and rules.urgent_deadline:
                alerts.append(
                    AlertDecision(
                        "OPPORTUNITY_NOW_URGENT",
                        "HIGH",
                        "Cierre próximo",
                        "El proceso entró en ventana urgente de cierre.",
                        "URGENT_DEADLINE",
                        {},
                        f"urgency:{change.new}:{current.closing_date}",
                    )
                )
        elif change.kind == "closing_date" and rules.closing_date_changes:
            alerts.append(
                AlertDecision(
                    "CLOSING_DATE_CHANGED",
                    "HIGH",
                    "Fecha de cierre modificada",
                    "SECOP publicó una fecha de cierre diferente.",
                    "CLOSING_DATE_CHANGED",
                    {"previous": str(change.old), "current": str(change.new)},
                    f"closing:{change.new}",
                )
            )
        elif (
            change.kind == "source_status"
            and rules.process_closed
            and str(change.new).upper() in {"CLOSED", "CERRADO", "ADJUDICADO"}
        ):
            alerts.append(
                AlertDecision(
                    "PROCESS_CLOSED",
                    "CRITICAL",
                    "Proceso cerrado",
                    "La fuente pública reporta el proceso como cerrado.",
                    "PROCESS_CLOSED",
                    {"status": change.new},
                    f"closed:{change.new}",
                )
            )
        elif change.kind == "document_count" and change.new > change.old and rules.new_documents:
            alerts.append(
                AlertDecision(
                    "NEW_DOCUMENT_DISCOVERED",
                    "HIGH",
                    "Cambio documental",
                    "SECOP publicó una referencia documental nueva o actualizada. "
                    "Requiere revisión humana.",
                    "DOCUMENT_STATE_CHANGED",
                    {},
                    f"documents:{current.document_state_hash}",
                )
            )
        elif (
            change.kind == "document_version_hash"
            and "document_count" not in changed_kinds
            and rules.document_updates
        ):
            alerts.append(
                AlertDecision(
                    "DOCUMENT_UPDATED",
                    "HIGH",
                    "Documento actualizado",
                    "SECOP reportó una versión diferente de un documento existente. "
                    "Requiere revisión humana.",
                    "DOCUMENT_VERSION_CHANGED",
                    {},
                    f"document-version:{change.new}",
                )
            )
        elif (
            change.kind == "addendum_status"
            and rules.addenda
            and change.new
            in {
                "POTENTIAL",
                "CONFIRMED",
                "POTENTIAL_ADDENDUM",
                "CONFIRMED_ADDENDUM",
            }
        ):
            kind = (
                "CONFIRMED_ADDENDUM_DISCOVERED"
                if change.new in {"CONFIRMED", "CONFIRMED_ADDENDUM"}
                else "POTENTIAL_ADDENDUM_DISCOVERED"
            )
            alerts.append(
                AlertDecision(
                    kind,
                    "CRITICAL" if change.new in {"CONFIRMED", "CONFIRMED_ADDENDUM"} else "HIGH",
                    "Novedad de adenda",
                    "La fuente pública reporta una novedad documental que requiere "
                    "revisión humana.",
                    kind,
                    {"status": change.new},
                    f"addendum:{change.new}:{current.document_state_hash}",
                )
            )
    return alerts
