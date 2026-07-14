"""Motor puro, deterministico y no probabilistico de screening."""
# mypy: disable-error-code="no-untyped-def,no-untyped-call"

import json
import re
import unicodedata
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
from zoneinfo import ZoneInfo

from pliegocheck_schemas import (
    OpportunityComponent,
    OpportunityComponentStatus,
    OpportunityOutcome,
    OpportunityUrgencyStatus,
)

from .models import AssessmentResult, CompanySnapshotInput, ComponentResult, ProcessInput
from .policy import OpportunityPolicy

BOGOTA = ZoneInfo("America/Bogota")
POSITIVE = {
    OpportunityComponentStatus.STRONG_MATCH: Decimal("100"),
    OpportunityComponentStatus.MATCH: Decimal("80"),
    OpportunityComponentStatus.PARTIAL_MATCH: Decimal("50"),
    OpportunityComponentStatus.MISMATCH: Decimal("0"),
    OpportunityComponentStatus.UNKNOWN: Decimal("0"),
    OpportunityComponentStatus.NOT_APPLICABLE: Decimal("0"),
    OpportunityComponentStatus.CONFLICTING: Decimal("0"),
}


def assess(
    snapshot: CompanySnapshotInput,
    process: ProcessInput,
    policy: OpportunityPolicy,
    effective_at: datetime,
) -> AssessmentResult:
    effective = effective_at.astimezone(BOGOTA)
    company = snapshot.payload.get("company", {})
    components: list[ComponentResult] = []
    relevance = _relevance(snapshot.payload, process, policy)
    components.append(
        _component(OpportunityComponent.RELEVANCE, relevance[0], relevance[1], relevance[2], policy)
    )
    unspsc = _unspsc(snapshot.payload, process)
    components.append(
        _component(OpportunityComponent.UNSPSC_MATCH, unspsc[0], unspsc[1], unspsc[2], policy)
    )
    experience = _experience(snapshot.payload, process, policy)
    components.append(
        _component(
            OpportunityComponent.EXPERIENCE_MATCH,
            experience[0],
            experience[1],
            experience[2],
            policy,
        )
    )
    value = _value(snapshot.payload, process)
    components.append(
        _component(OpportunityComponent.VALUE_FIT, value[0], value[1], value[2], policy)
    )
    financial = _financial(snapshot.payload)
    components.append(
        _component(
            OpportunityComponent.FINANCIAL_FIT,
            financial[0],
            financial[1],
            financial[2],
            policy,
        )
    )
    technical = _presence(
        snapshot.payload.get("capabilities", []),
        "TECHNICAL_DATA_AVAILABLE",
        "TECHNICAL_DATA_MISSING",
    )
    components.append(
        _component(
            OpportunityComponent.TECHNICAL_FIT,
            technical[0],
            technical[1],
            technical[2],
            policy,
        )
    )
    legal = _presence(
        snapshot.payload.get("legal_registrations", []),
        "LEGAL_DATA_AVAILABLE",
        "LEGAL_DATA_MISSING",
    )
    components.append(
        _component(
            OpportunityComponent.LEGAL_READINESS,
            legal[0],
            legal[1],
            legal[2],
            policy,
        )
    )
    geography = _geography(company, snapshot.payload, process)
    components.append(
        _component(
            OpportunityComponent.GEOGRAPHIC_FIT,
            geography[0],
            geography[1],
            geography[2],
            policy,
        )
    )
    urgency_status, days_remaining, urgency_score, urgency_reason = _urgency(
        process, effective, policy
    )
    components.append(
        _component(
            OpportunityComponent.DEADLINE_URGENCY,
            OpportunityComponentStatus.NOT_APPLICABLE,
            urgency_reason,
            {},
            policy,
        )
    )
    document_status = (
        OpportunityComponentStatus.MATCH
        if process.document_status
        not in {
            "UNKNOWN",
            "NOT_AVAILABLE",
            "MISSING",
            "METADATA_ONLY",
            "DOCUMENTS_NOT_AVAILABLE",
            "DOCUMENT_DOWNLOAD_UNSUPPORTED",
            "DOCUMENT_DOWNLOAD_FAILED",
        }
        else OpportunityComponentStatus.UNKNOWN
    )
    document_reason = (
        "DOCUMENTS_AVAILABLE"
        if document_status == OpportunityComponentStatus.MATCH
        else "DOCUMENTS_UNAVAILABLE"
    )
    components.append(
        _component(
            OpportunityComponent.DOCUMENT_READINESS, document_status, document_reason, {}, policy
        )
    )
    missing = _missing(snapshot.payload, process)
    completeness = _completeness(missing)
    info_status = (
        OpportunityComponentStatus.MATCH
        if completeness >= 75
        else OpportunityComponentStatus.PARTIAL_MATCH
        if completeness >= 45
        else OpportunityComponentStatus.UNKNOWN
    )
    info_reason = (
        "INFORMATION_COMPLETE"
        if completeness >= 75
        else "INFORMATION_PARTIAL"
        if completeness >= 45
        else "INFORMATION_INSUFFICIENT"
    )
    components.append(
        _component(
            OpportunityComponent.INFORMATION_COMPLETENESS,
            info_status,
            info_reason,
            {},
            policy,
            score=completeness,
        )
    )
    partner_reasons = _partner_reasons(components, snapshot.payload, policy)
    partner_status = (
        OpportunityComponentStatus.PARTIAL_MATCH
        if partner_reasons
        else OpportunityComponentStatus.NOT_APPLICABLE
    )
    components.append(
        _component(
            OpportunityComponent.PARTNER_NEED,
            partner_status,
            "POTENTIAL_PARTNER_NEED" if partner_reasons else "NO_PARTNER_NEED_IDENTIFIED",
            {},
            policy,
        )
    )
    compatibility = sum((item.weighted_score for item in components), start=Decimal("0")).quantize(
        Decimal("0.01")
    )
    outcome = _outcome(
        process, urgency_status, relevance[0], compatibility, completeness, partner_reasons, policy
    )
    digest_payload = {
        "snapshot_id": snapshot.snapshot_id,
        "snapshot_digest": snapshot.digest,
        "policy_hash": policy.policy_hash,
        "process_identity": process.identity,
        "payload_hash": process.payload_hash,
        "effective_at": effective.isoformat(),
        "components": [
            (item.component.value, item.status.value, str(item.score)) for item in components
        ],
    }
    digest = sha256(
        json.dumps(digest_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return AssessmentResult(
        outcome=outcome.value,
        compatibility_score=compatibility,
        urgency_score=urgency_score,
        information_completeness=completeness,
        urgency_status=urgency_status.value,
        days_remaining=days_remaining,
        components=tuple(components),
        missing_information=missing,
        partner_reasons=tuple(partner_reasons),
        summary=_summary(outcome, compatibility, urgency_status),
        warnings=tuple(["Requiere revision humana."] if missing["missing_fields"] else []),
        input_digest=digest,
    )


def _component(component, status, reason, parameters, policy, score=None):
    return ComponentResult(
        component,
        status,
        score if score is not None else POSITIVE[status],
        policy.weights[component.value],
        reason,
        parameters,
    )


def _tokens(value: str, policy: OpportunityPolicy) -> set[str]:
    normalized = unicodedata.normalize("NFKD", value.lower()).encode("ascii", "ignore").decode()
    words = set(re.findall(r"[a-z0-9]{3,}", normalized)) - set(policy.terms["stopwords"])
    for canonical, synonyms in policy.terms["synonyms"].items():
        if canonical in words or any(term in normalized for term in synonyms):
            words.add(canonical)
    return words


def _relevance(payload, process, policy):
    process_tokens = _tokens(" ".join(filter(None, [process.title, process.description])), policy)
    company_data = payload.get("company", {})
    text_parts = list(company_data.get("economic_activity_codes", []))
    for row in payload.get("experience_records", []):
        text_parts.extend([row.get("contract_title", ""), row.get("description", "")])
        text_parts.extend(row.get("activities", []))
    for row in payload.get("capabilities", []):
        text_parts.extend([row.get("name", ""), row.get("description", "")])
    company_tokens = _tokens(" ".join(str(item) for item in text_parts), policy)
    if not process_tokens or not company_tokens:
        return OpportunityComponentStatus.UNKNOWN, "TEXT_INFORMATION_MISSING", {}
    ratio = Decimal(len(process_tokens & company_tokens)) / Decimal(max(1, len(process_tokens)))
    if ratio >= Decimal("0.25"):
        return OpportunityComponentStatus.STRONG_MATCH, "TEXT_STRONG_MATCH", {"ratio": str(ratio)}
    if ratio > 0:
        return OpportunityComponentStatus.PARTIAL_MATCH, "TEXT_PARTIAL_MATCH", {"ratio": str(ratio)}
    return OpportunityComponentStatus.MISMATCH, "TEXT_MISMATCH", {}


def _codes(payload):
    values = [str(row.get("code", "")) for row in payload.get("unspsc_codes", [])]
    for row in payload.get("experience_records", []):
        values.extend(str(code) for code in row.get("unspsc_codes", []))
    return {re.sub(r"\D", "", value)[:8] for value in values if len(re.sub(r"\D", "", value)) >= 2}


def _unspsc(payload, process):
    company_codes, process_codes = (
        _codes(payload),
        {re.sub(r"\D", "", code)[:8] for code in process.unspsc_codes},
    )
    if not company_codes or not process_codes:
        return OpportunityComponentStatus.UNKNOWN, "UNSPSC_UNKNOWN", {}
    levels = [
        (8, OpportunityComponentStatus.STRONG_MATCH, "UNSPSC_PRODUCT_MATCH"),
        (6, OpportunityComponentStatus.MATCH, "UNSPSC_CLASS_MATCH"),
        (4, OpportunityComponentStatus.PARTIAL_MATCH, "UNSPSC_FAMILY_MATCH"),
        (2, OpportunityComponentStatus.PARTIAL_MATCH, "UNSPSC_SEGMENT_MATCH"),
    ]
    for size, status, reason in levels:
        for left in company_codes:
            for right in process_codes:
                if left[:size] == right[:size]:
                    return status, reason, {"code": right[:size]}
    return OpportunityComponentStatus.MISMATCH, "UNSPSC_GAP", {}


def _experience(payload, process, policy):
    rows = payload.get("experience_records", [])
    if not rows:
        return OpportunityComponentStatus.UNKNOWN, "EXPERIENCE_UNKNOWN", {}
    target = _tokens(" ".join(filter(None, [process.title, process.description])), policy)
    for row in rows:
        candidate = _tokens(
            " ".join([row.get("contract_title", ""), row.get("description", "")]), policy
        )
        if target & candidate:
            return OpportunityComponentStatus.MATCH, "EXPERIENCE_EVIDENCE_AVAILABLE", {}
    return OpportunityComponentStatus.MISMATCH, "EXPERIENCE_NOT_FOUND", {}


def _value(payload, process):
    if process.estimated_value is None:
        return OpportunityComponentStatus.UNKNOWN, "FINANCIAL_DATA_MISSING", {}
    values = [
        Decimal(str(row.get("company_attributable_value") or row.get("total_contract_value")))
        for row in payload.get("experience_records", [])
        if row.get("company_attributable_value") or row.get("total_contract_value")
    ]
    capacities = [
        Decimal(str(row.get("financial_capacity")))
        for row in payload.get("rup_snapshots", [])
        if row.get("financial_capacity")
    ]
    documented = max(values + capacities, default=None)
    if documented is None:
        return OpportunityComponentStatus.UNKNOWN, "FINANCIAL_DATA_MISSING", {}
    if process.estimated_value <= documented:
        return (
            OpportunityComponentStatus.MATCH,
            "PRELIMINARY_VALUE_FIT",
            {"documented_value": str(documented)},
        )
    return (
        OpportunityComponentStatus.MISMATCH,
        "PRELIMINARY_VALUE_MISMATCH",
        {"documented_value": str(documented)},
    )


def _financial(payload):
    return _presence(
        payload.get("financial_periods", []),
        "DEEP_FINANCIAL_REVIEW_REQUIRED",
        "FINANCIAL_DATA_MISSING",
    )


def _presence(rows, available_reason, missing_reason):
    if rows:
        return OpportunityComponentStatus.PARTIAL_MATCH, available_reason, {}
    return OpportunityComponentStatus.UNKNOWN, missing_reason, {}


def _geography(company, payload, process):
    target = {str(process.department or "").lower(), str(process.municipality or "").lower()} - {""}
    scopes = {
        str(company.get("department") or "").lower(),
        str(company.get("city") or "").lower(),
    } - {""}
    scopes |= {
        str(row.get("territorial_scope") or "").lower() for row in payload.get("capabilities", [])
    } - {""}
    if not target or not scopes:
        return OpportunityComponentStatus.UNKNOWN, "GEOGRAPHIC_UNKNOWN", {}
    if target & scopes or "nacional" in scopes:
        return OpportunityComponentStatus.MATCH, "GEOGRAPHIC_MATCH", {}
    return OpportunityComponentStatus.MISMATCH, "GEOGRAPHIC_GAP", {}


def _urgency(process, effective, policy):
    closed_words = {"cerrado", "adjudicado", "cancelado", "terminado", "closed"}
    if process.status and process.status.strip().lower() in closed_words:
        return OpportunityUrgencyStatus.CLOSED, Decimal("0"), Decimal("100"), "DEADLINE_CLOSED"
    if process.closing_date is None:
        return OpportunityUrgencyStatus.UNKNOWN, None, Decimal("0"), "DEADLINE_UNKNOWN"
    closing = process.closing_date.astimezone(BOGOTA)
    hours = Decimal(str((closing - effective).total_seconds() / 3600)).quantize(Decimal("0.01"))
    days = (hours / Decimal("24")).quantize(Decimal("0.01"))
    if hours < 0:
        return OpportunityUrgencyStatus.EXPIRED, days, Decimal("100"), "DEADLINE_CLOSED"
    rules = policy.raw["urgency_rules"]
    if hours < Decimal(str(rules["critical_hours"])):
        return OpportunityUrgencyStatus.CRITICAL, days, Decimal("100"), "DEADLINE_CRITICAL"
    if days <= Decimal(str(rules["urgent_days"])):
        return OpportunityUrgencyStatus.URGENT, days, Decimal("80"), "DEADLINE_URGENT"
    if days <= Decimal(str(rules["normal_days"])):
        return OpportunityUrgencyStatus.NORMAL, days, Decimal("50"), "DEADLINE_NORMAL"
    return OpportunityUrgencyStatus.LONG_HORIZON, days, Decimal("20"), "DEADLINE_LONG"


def _missing(payload, process):
    fields = [
        name
        for name, value in {
            "title": process.title,
            "entity_name": process.entity_name,
            "closing_date": process.closing_date,
            "estimated_value": process.estimated_value,
            "unspsc_codes": process.unspsc_codes,
        }.items()
        if not value
    ]
    company = [
        name
        for name, value in {
            "experience_records": payload.get("experience_records"),
            "financial_periods": payload.get("financial_periods"),
            "legal_registrations": payload.get("legal_registrations"),
            "capabilities": payload.get("capabilities"),
        }.items()
        if not value
    ]
    documents = (
        []
        if process.document_status
        not in {
            "UNKNOWN",
            "NOT_AVAILABLE",
            "MISSING",
            "METADATA_ONLY",
            "DOCUMENTS_NOT_AVAILABLE",
            "DOCUMENT_DOWNLOAD_UNSUPPORTED",
            "DOCUMENT_DOWNLOAD_FAILED",
        }
        else ["process_documents"]
    )
    return {
        "missing_fields": fields,
        "missing_documents": documents,
        "missing_evaluations": [],
        "missing_company_data": company,
        "unsupported_source_fields": [],
    }


def _completeness(missing):
    missing_count = sum(len(values) for values in missing.values())
    return max(Decimal("0"), Decimal("100") - Decimal(min(missing_count, 10) * 10))


def _partner_reasons(components, payload, policy):
    mapping = {
        OpportunityComponent.UNSPSC_MATCH: "UNSPSC_GAP",
        OpportunityComponent.EXPERIENCE_MATCH: "INSUFFICIENT_EXPERIENCE_VALUE",
        OpportunityComponent.GEOGRAPHIC_FIT: "GEOGRAPHIC_GAP",
        OpportunityComponent.VALUE_FIT: "FINANCIAL_CAPACITY_GAP",
    }
    allowed = set(policy.raw["partner_rules"]["resolvable_reason_codes"])
    return [
        {"reason_code": mapping[item.component], "partner_resolvable": "unknown"}
        for item in components
        if item.status == OpportunityComponentStatus.MISMATCH
        and item.component in mapping
        and mapping[item.component] in allowed
    ]


def _outcome(process, urgency, relevance, score, completeness, partner_reasons, policy):
    if (
        urgency in {OpportunityUrgencyStatus.CLOSED, OpportunityUrgencyStatus.EXPIRED}
        or relevance == OpportunityComponentStatus.MISMATCH
    ):
        return OpportunityOutcome.DESCARTAR
    if completeness < Decimal(str(policy.raw["thresholds"]["minimum_information"])):
        return OpportunityOutcome.INFORMACION_INSUFICIENTE
    if partner_reasons:
        return OpportunityOutcome.REQUIERE_ALIADO
    thresholds = policy.raw["thresholds"]
    if score < Decimal(str(thresholds["low"])):
        return OpportunityOutcome.POCO_COMPATIBLE
    if score >= Decimal(str(thresholds["review_first"])) and urgency not in {
        OpportunityUrgencyStatus.CRITICAL,
        OpportunityUrgencyStatus.UNKNOWN,
    }:
        return OpportunityOutcome.REVISAR_PRIMERO
    return OpportunityOutcome.OPORTUNIDAD_POTENCIAL


def _summary(outcome, score, urgency):
    return (
        f"{outcome.value}: compatibilidad preliminar {score}/100; "
        f"urgencia {urgency.value}. Requiere revision humana."
    )
