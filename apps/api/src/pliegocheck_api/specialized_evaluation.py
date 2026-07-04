# mypy: ignore-errors
"""Evaluadores especializados deterministas contra snapshots de empresa.

No llama modelos de IA ni interpreta equivalencias libres. Cuando el requisito
o el dato no es comparable de forma explicita, devuelve UNKNOWN.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from typing import Any
from uuid import UUID

from pliegocheck_schemas import (
    CompanyEvidenceReviewStatus,
    CompanyEvidenceRole,
    CompanyRecordStatus,
    ExperienceExecutionStatus,
    RequirementCategory,
    SpecializedDataUsability,
    SpecializedEvaluationDomain,
    SpecializedEvaluationResultStatus,
    SpecializedExplanationCode,
    SpecializedOperator,
    SpecializedRuleMappingStatus,
    SpecializedRuleSourceBasis,
    SpecializedRuleType,
)

RULE_MAPPING_VERSION = "specialized-rule-mapper:1.0.0"

DOMAIN_CATEGORIES: dict[str, set[str]] = {
    SpecializedEvaluationDomain.LEGAL.value: {
        RequirementCategory.LEGAL.value,
        RequirementCategory.RISK_AND_INELIGIBILITY.value,
        RequirementCategory.DOCUMENTARY.value,
        RequirementCategory.GUARANTEE.value,
    },
    SpecializedEvaluationDomain.EXPERIENCE.value: {RequirementCategory.EXPERIENCE.value},
    SpecializedEvaluationDomain.TECHNICAL.value: {
        RequirementCategory.TECHNICAL.value,
        RequirementCategory.OPERATIONAL.value,
        RequirementCategory.WORKFORCE.value,
        RequirementCategory.ORGANIZATIONAL.value,
    },
}


@dataclass(frozen=True)
class ResolvedRecord:
    record: dict[str, Any] | None
    source_record_type: str | None
    usability: str
    evidence_links: list[dict[str, Any]] = field(default_factory=list)
    actual_value: str | None = None
    warning: str | None = None


def stable_digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(canonical.encode("utf-8")).hexdigest()


def supported_domains() -> list[str]:
    return [
        SpecializedEvaluationDomain.LEGAL.value,
        SpecializedEvaluationDomain.EXPERIENCE.value,
        SpecializedEvaluationDomain.TECHNICAL.value,
    ]


def categories_for_domain(domain: str) -> set[str]:
    return set(DOMAIN_CATEGORIES.get(domain, set()))


def build_input_manifest(
    *,
    process: Any,
    normalization_run: Any,
    snapshot: Any,
    requirements: list[Any],
    domain: str,
) -> dict[str, Any]:
    payload = snapshot.payload if isinstance(snapshot.payload, dict) else {}
    source_record_ids: list[str] = []
    for key in (
        "legal_registrations",
        "rup_snapshots",
        "experience_records",
        "people",
        "certifications",
        "capabilities",
        "unspsc_codes",
    ):
        for item in payload.get(key, []):
            if isinstance(item, dict) and item.get("id"):
                source_record_ids.append(str(item["id"]))
    evidence_ids = [
        str(link["id"])
        for link in payload.get("evidence_links", [])
        if isinstance(link, dict) and link.get("id")
    ]
    return {
        "process_id": str(process.id),
        "normalization_run_id": str(normalization_run.id),
        "company_id": str(snapshot.company_id),
        "company_profile_snapshot_id": str(snapshot.id),
        "domain": domain,
        "company_snapshot_digest": snapshot.digest,
        "requirement_ids": [str(requirement.id) for requirement in requirements],
        "requirement_stable_keys": [requirement.stable_key for requirement in requirements],
        "source_record_ids": sorted(set(source_record_ids)),
        "evidence_ids": sorted(set(evidence_ids)),
        "effective_at": _effective_date(process, snapshot),
        "rule_mapping_version": RULE_MAPPING_VERSION,
    }


def _effective_date(process: Any, snapshot: Any) -> str | None:
    for value in (
        getattr(process, "closing_at", None),
        getattr(snapshot, "published_at", None),
        getattr(snapshot, "created_at", None),
    ):
        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, date):
            return value.isoformat()
    return None


def map_specialized_requirement(requirement: Any, domain: str) -> dict[str, Any]:
    if requirement.category not in categories_for_domain(domain):
        return _rule_payload(
            requirement,
            domain=domain,
            rule_type=SpecializedRuleType.UNSUPPORTED.value,
            subject=None,
            operator=None,
            source_basis=SpecializedRuleSourceBasis.UNKNOWN.value,
            mapping_status=SpecializedRuleMappingStatus.UNSUPPORTED.value,
            mapping_warnings=["DOMAIN_NOT_APPLICABLE"],
            requires_human_review=True,
        )
    text = _requirement_text(requirement)
    normalized = _normalize(text)
    expected = requirement.expected_value or {}
    expected_value = _expected_text(expected, normalized)
    expected_number = _expected_number(expected, normalized)

    rule_type, subject, operator = _detect_rule(domain, requirement.category, normalized)
    warnings: list[str] = []
    mapping_status = SpecializedRuleMappingStatus.MAPPED.value
    if rule_type == SpecializedRuleType.UNSUPPORTED.value:
        warnings.append("RULE_NOT_SUPPORTED")
        mapping_status = SpecializedRuleMappingStatus.UNSUPPORTED.value
    if operator is None:
        warnings.append("OPERATOR_NOT_DETECTED")
        mapping_status = SpecializedRuleMappingStatus.AMBIGUOUS.value
    if _requires_expected(rule_type) and expected_value is None and expected_number is None:
        warnings.append("EXPECTED_VALUE_NOT_DETECTED")
        mapping_status = SpecializedRuleMappingStatus.AMBIGUOUS.value
    source_basis = (
        SpecializedRuleSourceBasis.EXPLICIT_EXPECTED_VALUE.value
        if expected
        else SpecializedRuleSourceBasis.EXPLICIT_DESCRIPTION.value
    )
    if mapping_status != SpecializedRuleMappingStatus.MAPPED.value:
        source_basis = SpecializedRuleSourceBasis.UNKNOWN.value
    return _rule_payload(
        requirement,
        domain=domain,
        rule_type=rule_type,
        subject=subject,
        operator=operator,
        expected_value=expected_value,
        expected_min_value=expected_number,
        unit=_unit_for(rule_type),
        currency=_currency_for(normalized),
        source_basis=source_basis,
        mapping_status=mapping_status,
        mapping_warnings=warnings,
        requires_human_review=mapping_status != SpecializedRuleMappingStatus.MAPPED.value,
    )


def evaluate_specialized_requirement(
    *,
    requirement: Any,
    rule: Any,
    snapshot_payload: dict[str, Any],
    effective_at: datetime,
) -> dict[str, Any]:
    if _get(rule, "mapping_status") != SpecializedRuleMappingStatus.MAPPED.value:
        return _result_payload(
            rule=rule,
            status=SpecializedEvaluationResultStatus.UNKNOWN.value,
            explanation_code=(
                SpecializedExplanationCode.RULE_UNSUPPORTED.value
                if _get(rule, "mapping_status") == SpecializedRuleMappingStatus.UNSUPPORTED.value
                else SpecializedExplanationCode.RULE_AMBIGUOUS.value
            ),
            explanation_parameters={"warnings": _get(rule, "mapping_warnings") or []},
            requires_human_review=True,
        )
    domain = _get(rule, "domain")
    if domain == SpecializedEvaluationDomain.LEGAL.value:
        resolution = _resolve_legal(rule, snapshot_payload, effective_at.date())
    elif domain == SpecializedEvaluationDomain.EXPERIENCE.value:
        resolution = _resolve_experience(rule, snapshot_payload)
    elif domain == SpecializedEvaluationDomain.TECHNICAL.value:
        resolution = _resolve_technical(rule, snapshot_payload, effective_at.date())
    else:
        resolution = ResolvedRecord(None, None, SpecializedDataUsability.MISSING.value)
    return _result_from_resolution(rule, resolution)


def _detect_rule(domain: str, category: str, text: str) -> tuple[str, str | None, str | None]:
    if domain == SpecializedEvaluationDomain.LEGAL.value:
        if "rup" in text:
            return (
                SpecializedRuleType.REGISTRATION_VALID.value
                if _mentions_validity(text)
                else SpecializedRuleType.REGISTRATION_EXISTS.value,
                "RUP",
                SpecializedOperator.EXISTS.value,
            )
        if "rut" in text or "tribut" in text:
            return (
                SpecializedRuleType.REGISTRATION_EXISTS.value,
                "RUT",
                SpecializedOperator.EXISTS.value,
            )
        if "camara" in text or "comercio" in text:
            return (
                SpecializedRuleType.REGISTRATION_VALID.value
                if _mentions_validity(text)
                else SpecializedRuleType.REGISTRATION_EXISTS.value,
                "CHAMBER_OF_COMMERCE",
                SpecializedOperator.EXISTS.value,
            )
        if "representante" in text or "representacion legal" in text:
            return (
                SpecializedRuleType.DOCUMENT_EXISTS.value,
                "LEGAL_REPRESENTATION",
                SpecializedOperator.EXISTS.value,
            )
        if category == RequirementCategory.GUARANTEE.value or "garantia" in text:
            return (
                SpecializedRuleType.DOCUMENT_EXISTS.value,
                "GUARANTEE",
                SpecializedOperator.EXISTS.value,
            )
        if "inhabilidad" in text or "incompatibilidad" in text or "riesgo" in text:
            return (
                SpecializedRuleType.DOCUMENT_EXISTS.value,
                "RISK_DECLARATION",
                SpecializedOperator.EXISTS.value,
            )
        return (
            SpecializedRuleType.DOCUMENT_EXISTS.value,
            "DOCUMENT",
            SpecializedOperator.EXISTS.value,
        )
    if domain == SpecializedEvaluationDomain.EXPERIENCE.value:
        if "unspsc" in text:
            return (
                SpecializedRuleType.EXPERIENCE_UNSPSC.value,
                "UNSPSC",
                SpecializedOperator.CONTAINS.value,
            )
        if "actividad" in text or "objeto" in text:
            return (
                SpecializedRuleType.EXPERIENCE_ACTIVITY.value,
                "ACTIVITY",
                SpecializedOperator.CONTAINS.value,
            )
        if "contrato" in text and ("minimo" in text or "al menos" in text):
            return (
                SpecializedRuleType.EXPERIENCE_COUNT.value,
                "CONTRACT_COUNT",
                SpecializedOperator.GREATER_THAN_OR_EQUAL.value,
            )
        if "valor" in text or "$" in text or "smmlv" in text:
            return (
                SpecializedRuleType.EXPERIENCE_VALUE.value,
                "CONTRACT_VALUE",
                SpecializedOperator.GREATER_THAN_OR_EQUAL.value,
            )
        return (
            SpecializedRuleType.EXPERIENCE_EXISTS.value,
            "EXPERIENCE",
            SpecializedOperator.EXISTS.value,
        )
    if "certificacion" in text or "certificado" in text:
        return (
            SpecializedRuleType.CERTIFICATION_VALID.value
            if _mentions_validity(text)
            else SpecializedRuleType.CERTIFICATION_EXISTS.value,
            "CERTIFICATION",
            SpecializedOperator.EXISTS.value,
        )
    if "persona" in text or "profesional" in text or "equipo" in text:
        return (
            SpecializedRuleType.PERSON_ROLE_EXISTS.value,
            "PERSON_ROLE",
            SpecializedOperator.EXISTS.value,
        )
    if "cobertura" in text or "territorial" in text:
        return (
            SpecializedRuleType.COVERAGE_EXISTS.value,
            "GEOGRAPHIC_COVERAGE",
            SpecializedOperator.CONTAINS.value,
        )
    if "capacidad" in text or "plataforma" in text or "infraestructura" in text:
        return (
            SpecializedRuleType.CAPABILITY_EXISTS.value,
            "CAPABILITY",
            SpecializedOperator.CONTAINS.value,
        )
    return (SpecializedRuleType.UNSUPPORTED.value, None, None)


def _resolve_legal(rule: Any, payload: dict[str, Any], today: date) -> ResolvedRecord:
    subject = _get(rule, "subject")
    if subject == "RUP":
        records = payload.get("rup_snapshots", [])
        return _first_usable(records, payload, "RUP_SNAPSHOT", "RUP", today)
    if subject in {"RUT", "CHAMBER_OF_COMMERCE", "LEGAL_REPRESENTATION"}:
        records = [
            item
            for item in payload.get("legal_registrations", [])
            if item.get("registration_type") == subject
        ]
        return _first_usable(records, payload, "LEGAL_REGISTRATION", subject, today)
    if subject == "GUARANTEE":
        docs = [
            item
            for item in payload.get("evidence_documents", [])
            if "guarantee" in _normalize(item.get("evidence_type", ""))
            or "garantia" in _normalize(item.get("title", ""))
        ]
        return _first_usable(docs, payload, "EVIDENCE_DOCUMENT", subject, today)
    if subject == "RISK_DECLARATION":
        docs = [
            item
            for item in payload.get("evidence_documents", [])
            if "inhabilidad" in _normalize(item.get("title", ""))
            or "declaracion" in _normalize(item.get("title", ""))
        ]
        return _first_usable(docs, payload, "EVIDENCE_DOCUMENT", subject, today)
    return _first_usable(
        payload.get("evidence_documents", []), payload, "EVIDENCE_DOCUMENT", subject, today
    )


def _resolve_experience(rule: Any, payload: dict[str, Any]) -> ResolvedRecord:
    records = [
        item
        for item in payload.get("experience_records", [])
        if item.get("status") != CompanyRecordStatus.REJECTED.value
    ]
    rule_type = _get(rule, "rule_type")
    if not records:
        return ResolvedRecord(None, "EXPERIENCE_RECORD", SpecializedDataUsability.MISSING.value)
    if rule_type == SpecializedRuleType.EXPERIENCE_COUNT.value:
        completed = [item for item in records if item.get("execution_status") == "COMPLETED"]
        threshold = _to_decimal(_get(rule, "expected_min_value")) or Decimal("1")
        if len(completed) >= threshold:
            return _experience_resolution(completed[0], payload, str(len(completed)))
        return ResolvedRecord(
            completed[0] if completed else records[0],
            "EXPERIENCE_RECORD",
            _record_usability(
                completed[0] if completed else records[0],
                _links(payload, completed[0].get("id") if completed else records[0].get("id")),
            ),
            _links(payload, completed[0].get("id") if completed else records[0].get("id")),
            actual_value=str(len(completed)),
            warning="COUNT_BELOW_REQUIRED",
        )
    if rule_type == SpecializedRuleType.EXPERIENCE_VALUE.value:
        return _resolve_experience_value(rule, records, payload)
    if rule_type == SpecializedRuleType.EXPERIENCE_UNSPSC.value:
        expected = _get(rule, "expected_value")
        if not expected:
            return ResolvedRecord(
                records[0], "EXPERIENCE_RECORD", SpecializedDataUsability.MISSING.value
            )
        for item in records:
            if expected in {str(code) for code in item.get("unspsc_codes", [])}:
                return _experience_resolution(item, payload, expected)
        return ResolvedRecord(
            records[0],
            "EXPERIENCE_RECORD",
            SpecializedDataUsability.MISSING.value,
            warning="UNSPSC_NOT_COMPARABLE",
        )
    if rule_type == SpecializedRuleType.EXPERIENCE_ACTIVITY.value:
        expected = _get(rule, "expected_value")
        if not expected:
            return ResolvedRecord(
                records[0], "EXPERIENCE_RECORD", SpecializedDataUsability.MISSING.value
            )
        for item in records:
            if _normalize(expected) in {
                _normalize(activity) for activity in item.get("activities", [])
            }:
                return _experience_resolution(item, payload, expected)
        return ResolvedRecord(
            records[0],
            "EXPERIENCE_RECORD",
            SpecializedDataUsability.MISSING.value,
            warning="ACTIVITY_NOT_COMPARABLE",
        )
    return _experience_resolution(records[0], payload, records[0].get("contract_title"))


def _resolve_experience_value(
    rule: Any, records: list[dict[str, Any]], payload: dict[str, Any]
) -> ResolvedRecord:
    required = _to_decimal(_get(rule, "expected_min_value")) or _to_decimal(
        _get(rule, "expected_value")
    )
    if required is None:
        return ResolvedRecord(
            records[0], "EXPERIENCE_RECORD", SpecializedDataUsability.MISSING.value
        )
    currency = _get(rule, "currency")
    for item in records:
        if item.get("execution_status") != ExperienceExecutionStatus.COMPLETED.value:
            continue
        if currency and item.get("currency") and currency != item.get("currency"):
            return ResolvedRecord(
                item,
                "EXPERIENCE_RECORD",
                SpecializedDataUsability.MISSING.value,
                warning="CURRENCY_MISMATCH",
            )
        value = _attributable_value(item)
        if value is None:
            return ResolvedRecord(
                item,
                "EXPERIENCE_RECORD",
                SpecializedDataUsability.MISSING.value,
                warning="CONSORTIUM_PERCENTAGE_MISSING",
            )
        if value >= required:
            return _experience_resolution(item, payload, str(value))
    return _experience_resolution(
        records[0],
        payload,
        str(_attributable_value(records[0]) or "0"),
        warning="VALUE_BELOW_REQUIRED",
    )


def _resolve_technical(rule: Any, payload: dict[str, Any], today: date) -> ResolvedRecord:
    rule_type = _get(rule, "rule_type")
    expected = _get(rule, "expected_value")
    if rule_type in {
        SpecializedRuleType.CERTIFICATION_EXISTS.value,
        SpecializedRuleType.CERTIFICATION_VALID.value,
    }:
        certs = payload.get("certifications", [])
        if expected:
            certs = [
                item for item in certs if _normalize(expected) in _normalize(item.get("name", ""))
            ]
        return _first_usable(certs, payload, "CERTIFICATION", expected, today)
    if rule_type == SpecializedRuleType.PERSON_ROLE_EXISTS.value:
        people = payload.get("people", [])
        if expected:
            people = [
                item
                for item in people
                if _normalize(expected)
                in _normalize(item.get("relationship_type", "") + " " + item.get("full_name", ""))
            ]
        return _first_usable(people, payload, "PERSON", expected, today)
    if rule_type in {
        SpecializedRuleType.CAPABILITY_EXISTS.value,
        SpecializedRuleType.COVERAGE_EXISTS.value,
    }:
        capabilities = payload.get("capabilities", [])
        if expected:
            capabilities = [
                item
                for item in capabilities
                if _normalize(expected)
                in _normalize(
                    " ".join(
                        [
                            str(item.get("name", "")),
                            str(item.get("description", "")),
                            str(item.get("territorial_scope", "")),
                        ]
                    )
                )
            ]
        return _first_usable(capabilities, payload, "CAPABILITY", expected, today)
    return ResolvedRecord(None, None, SpecializedDataUsability.MISSING.value)


def _first_usable(
    records: list[dict[str, Any]],
    payload: dict[str, Any],
    record_type: str,
    actual_value: str | None,
    today: date,
) -> ResolvedRecord:
    if not records:
        return ResolvedRecord(None, record_type, SpecializedDataUsability.MISSING.value)
    record = records[0]
    links = _links(payload, record.get("id"))
    usability = _record_usability(record, links)
    expires = record.get("expires_at") or record.get("valid_until")
    if expires and _parse_date(expires) < today:
        usability = SpecializedDataUsability.EXPIRED.value
    return ResolvedRecord(record, record_type, usability, links, actual_value=actual_value)


def _experience_resolution(
    item: dict[str, Any], payload: dict[str, Any], actual: str | None, warning: str | None = None
) -> ResolvedRecord:
    links = _links(payload, item.get("id"))
    usability = _record_usability(item, links)
    if item.get("execution_status") not in {ExperienceExecutionStatus.COMPLETED.value, "COMPLETED"}:
        usability = SpecializedDataUsability.MISSING.value
        warning = warning or "RECORD_NOT_COMPLETED"
    return ResolvedRecord(
        item, "EXPERIENCE_RECORD", usability, links, actual_value=actual, warning=warning
    )


def _result_from_resolution(rule: Any, resolution: ResolvedRecord) -> dict[str, Any]:
    if resolution.usability == SpecializedDataUsability.CONFLICTING.value:
        status = SpecializedEvaluationResultStatus.CONFLICTING_EVIDENCE.value
        code = SpecializedExplanationCode.EVIDENCE_CONFLICT.value
    elif resolution.usability in {
        SpecializedDataUsability.MISSING.value,
        SpecializedDataUsability.DECLARED_ONLY.value,
    }:
        status = SpecializedEvaluationResultStatus.UNKNOWN.value
        code = (
            SpecializedExplanationCode.DECLARED_ONLY_NOT_ACCEPTED.value
            if resolution.usability == SpecializedDataUsability.DECLARED_ONLY.value
            else SpecializedExplanationCode.DATA_MISSING.value
        )
    elif resolution.usability == SpecializedDataUsability.EXPIRED.value:
        status = SpecializedEvaluationResultStatus.DOES_NOT_COMPLY.value
        code = SpecializedExplanationCode.EVIDENCE_EXPIRED.value
    elif resolution.usability == SpecializedDataUsability.REJECTED.value:
        status = SpecializedEvaluationResultStatus.UNKNOWN.value
        code = SpecializedExplanationCode.EVIDENCE_REJECTED.value
    elif resolution.warning in {
        "VALUE_BELOW_REQUIRED",
        "COUNT_BELOW_REQUIRED",
    }:
        status = SpecializedEvaluationResultStatus.DOES_NOT_COMPLY.value
        code = SpecializedExplanationCode.REQUIREMENT_NOT_MET.value
    elif resolution.warning == "RECORD_NOT_COMPLETED":
        status = SpecializedEvaluationResultStatus.UNKNOWN.value
        code = SpecializedExplanationCode.RECORD_NOT_COMPLETED.value
    elif resolution.warning == "CURRENCY_MISMATCH":
        status = SpecializedEvaluationResultStatus.UNKNOWN.value
        code = SpecializedExplanationCode.CURRENCY_MISMATCH.value
    elif resolution.warning == "CONSORTIUM_PERCENTAGE_MISSING":
        status = SpecializedEvaluationResultStatus.UNKNOWN.value
        code = SpecializedExplanationCode.CONSORTIUM_PERCENTAGE_MISSING.value
    elif resolution.warning == "UNSPSC_NOT_COMPARABLE":
        status = SpecializedEvaluationResultStatus.UNKNOWN.value
        code = SpecializedExplanationCode.UNSPSC_NOT_COMPARABLE.value
    elif resolution.warning == "ACTIVITY_NOT_COMPARABLE":
        status = SpecializedEvaluationResultStatus.UNKNOWN.value
        code = SpecializedExplanationCode.ACTIVITY_NOT_COMPARABLE.value
    else:
        status = SpecializedEvaluationResultStatus.COMPLIES.value
        code = SpecializedExplanationCode.REQUIREMENT_COMPLIES.value
    return _result_payload(
        rule=rule,
        status=status,
        source_record_type=resolution.source_record_type,
        source_record_id=_uuid_or_none(resolution.record.get("id") if resolution.record else None),
        actual_value=resolution.actual_value,
        evidence_refs={"links": [_link_ref(link) for link in resolution.evidence_links]},
        explanation_code=code,
        explanation_parameters={"usability": resolution.usability, "warning": resolution.warning},
        requires_human_review=status
        in {
            SpecializedEvaluationResultStatus.UNKNOWN.value,
            SpecializedEvaluationResultStatus.CONFLICTING_EVIDENCE.value,
        }
        or resolution.usability != SpecializedDataUsability.VERIFIED.value,
    )


def _record_usability(record: dict[str, Any], links: list[dict[str, Any]]) -> str:
    if any(link.get("evidence_role") == CompanyEvidenceRole.CONFLICTING.value for link in links):
        return SpecializedDataUsability.CONFLICTING.value
    status = record.get("status")
    if status == CompanyRecordStatus.REJECTED.value:
        return SpecializedDataUsability.REJECTED.value
    if status == CompanyRecordStatus.EXPIRED.value:
        return SpecializedDataUsability.EXPIRED.value
    if status == CompanyRecordStatus.VERIFIED.value or any(
        link.get("review_status") == CompanyEvidenceReviewStatus.VERIFIED.value for link in links
    ):
        return SpecializedDataUsability.VERIFIED.value
    if status == CompanyRecordStatus.SUPPORTED.value or any(
        link.get("review_status") == CompanyEvidenceReviewStatus.SUPPORTED.value for link in links
    ):
        return SpecializedDataUsability.SUPPORTED.value
    return SpecializedDataUsability.DECLARED_ONLY.value


def _links(payload: dict[str, Any], subject_id: Any) -> list[dict[str, Any]]:
    if not subject_id:
        return []
    return [
        link
        for link in payload.get("evidence_links", [])
        if isinstance(link, dict) and str(link.get("subject_id")) == str(subject_id)
    ]


def _attributable_value(item: dict[str, Any]) -> Decimal | None:
    direct = _to_decimal(item.get("company_attributable_value"))
    if direct is not None:
        return direct
    total = _to_decimal(item.get("total_contract_value"))
    if total is None:
        return None
    if item.get("consortium_name") or item.get("consortium_members"):
        percentage = _to_decimal(item.get("company_participation_percentage"))
        if percentage is None:
            return None
        return total * percentage / Decimal("100")
    return total


def _requires_expected(rule_type: str) -> bool:
    return rule_type in {
        SpecializedRuleType.EXPERIENCE_COUNT.value,
        SpecializedRuleType.EXPERIENCE_VALUE.value,
        SpecializedRuleType.EXPERIENCE_UNSPSC.value,
        SpecializedRuleType.EXPERIENCE_ACTIVITY.value,
        SpecializedRuleType.CAPABILITY_EXISTS.value,
        SpecializedRuleType.COVERAGE_EXISTS.value,
        SpecializedRuleType.PERSON_ROLE_EXISTS.value,
        SpecializedRuleType.CERTIFICATION_EXISTS.value,
        SpecializedRuleType.CERTIFICATION_VALID.value,
    }


def _rule_payload(requirement: Any, **values: Any) -> dict[str, Any]:
    return {
        "requirement_id": requirement.id,
        "normalization_run_id": requirement.normalization_run_id,
        "domain": values["domain"],
        "rule_type": values["rule_type"],
        "subject": values.get("subject"),
        "operator": values.get("operator"),
        "expected_value": values.get("expected_value"),
        "expected_min_value": values.get("expected_min_value"),
        "expected_max_value": values.get("expected_max_value"),
        "unit": values.get("unit"),
        "currency": values.get("currency"),
        "period_policy": values.get("period_policy"),
        "condition_group": values.get("condition_group") or {},
        "source_basis": values["source_basis"],
        "mapping_status": values["mapping_status"],
        "mapping_warnings": values["mapping_warnings"],
        "requires_human_review": values["requires_human_review"],
        "manual_override_payload": values.get("manual_override_payload") or {},
        "version": 1,
        "is_manual_override": False,
    }


def _result_payload(
    *,
    rule: Any,
    status: str,
    source_record_type: str | None = None,
    source_record_id: UUID | None = None,
    actual_value: str | None = None,
    evidence_refs: dict[str, Any] | None = None,
    explanation_code: str,
    explanation_parameters: dict[str, Any] | None = None,
    requires_human_review: bool = False,
) -> dict[str, Any]:
    return {
        "status": status,
        "domain": _get(rule, "domain"),
        "rule_type": _get(rule, "rule_type"),
        "subject": _get(rule, "subject"),
        "operator": _get(rule, "operator"),
        "expected_value": _get(rule, "expected_value"),
        "actual_value": actual_value,
        "unit": _get(rule, "unit"),
        "source_record_type": source_record_type,
        "source_record_id": source_record_id,
        "explanation_code": explanation_code,
        "explanation_parameters": explanation_parameters or {},
        "evidence_refs": evidence_refs or {"links": []},
        "requires_human_review": requires_human_review,
    }


def _requirement_text(requirement: Any) -> str:
    expected = requirement.expected_value or {}
    pieces = [
        requirement.description or "",
        requirement.condition_text or "",
        str(expected.get("raw_text") or ""),
        str(expected.get("value") or ""),
        str(expected.get("unit") or ""),
    ]
    return " ".join(piece for piece in pieces if piece)


def _expected_text(expected: dict[str, Any], text: str) -> str | None:
    for key in ("value", "raw_text", "code", "name"):
        if expected.get(key):
            return str(expected[key]).strip()
    unspsc = re.search(r"\b\d{8}\b", text)
    if unspsc:
        return unspsc.group(0)
    quoted = re.search(r"'([^']{3,120})'|\"([^\"]{3,120})\"", text)
    if quoted:
        return quoted.group(1) or quoted.group(2)
    return None


def _expected_number(expected: dict[str, Any], text: str) -> Decimal | None:
    for key in ("numeric_value", "value", "min_value"):
        parsed = _to_decimal(expected.get(key))
        if parsed is not None:
            return parsed
    numbers = [_to_decimal(item) for item in re.findall(r"\d+(?:[.,]\d+)?", text)]
    numbers = [item for item in numbers if item is not None]
    return numbers[-1] if numbers else None


def _unit_for(rule_type: str) -> str | None:
    if rule_type == SpecializedRuleType.EXPERIENCE_COUNT.value:
        return "contracts"
    if rule_type == SpecializedRuleType.EXPERIENCE_VALUE.value:
        return "money"
    return None


def _currency_for(text: str) -> str | None:
    if "$" in text or "cop" in text or "pesos" in text:
        return "COP"
    return None


def _mentions_validity(text: str) -> bool:
    return "vigente" in text or "vigencia" in text or "valido" in text or "valid" in text


def _normalize(value: Any) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or "").lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _to_decimal(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        text = str(value).strip().replace("$", "").replace("COP", "").replace("cop", "")
        text = text.replace("%", "").strip()
        if "," in text and "." in text:
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", ".")
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return None


def _parse_date(value: Any) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return date.fromisoformat(str(value))


def _uuid_or_none(value: Any) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def _link_ref(link: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": link.get("id"),
        "document_id": link.get("document_id"),
        "subject_id": link.get("subject_id"),
        "evidence_role": link.get("evidence_role"),
        "review_status": link.get("review_status"),
        "validation_status": link.get("validation_status"),
        "quoted_text": link.get("quoted_text"),
        "source_location": link.get("source_location") or {},
    }


def _get(obj: Any, name: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name)
