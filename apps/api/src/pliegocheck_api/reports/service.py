# mypy: ignore-errors
"""Servicio de generacion de paquetes de reporte."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from pliegocheck_api.models import (
    CompanyProfile,
    CompanyProfileSnapshot,
    DecisionActionItemRecord,
    DecisionInputFindingSnapshot,
    DecisionPolicyVersion,
    DecisionReportArtifact,
    DecisionReportPackage,
    DecisionReportSection,
    DecisionReview,
    DecisionRuleEvaluationRecord,
    DecisionRun,
    FinancialEvaluationRun,
    Process,
    Requirement,
    SpecializedEvaluationRun,
)
from pliegocheck_api.reports import REPORT_ENGINE_VERSION, REPORT_TEMPLATE_VERSION
from pliegocheck_api.reports.manifest import artifact_manifest_digest, canonical_json
from pliegocheck_api.reports.package import ReportArtifactStorage, artifact_record, build_zip
from pliegocheck_api.reports.renderer import RenderedArtifact, render_artifacts
from pliegocheck_api.reports.templates import ReportTemplates, load_report_templates
from pliegocheck_schemas import DecisionReportPackageStatus

PACKAGE_VERSION = "1.0.0"


def build_input_manifest(
    session: Session, run: DecisionRun, templates: ReportTemplates | None = None
) -> dict[str, Any]:
    templates = templates or load_report_templates()
    reviews = session.scalars(
        select(DecisionReview)
        .where(DecisionReview.decision_run_id == run.id)
        .order_by(DecisionReview.created_at)
    ).all()
    actions = session.scalars(
        select(DecisionActionItemRecord)
        .where(DecisionActionItemRecord.decision_run_id == run.id)
        .order_by(DecisionActionItemRecord.id)
    ).all()
    findings = session.scalars(
        select(DecisionInputFindingSnapshot)
        .where(DecisionInputFindingSnapshot.decision_run_id == run.id)
        .order_by(DecisionInputFindingSnapshot.id)
    ).all()
    rules = session.scalars(
        select(DecisionRuleEvaluationRecord)
        .where(DecisionRuleEvaluationRecord.decision_run_id == run.id)
        .order_by(DecisionRuleEvaluationRecord.priority, DecisionRuleEvaluationRecord.rule_code)
    ).all()
    specialized_runs = session.scalars(
        select(SpecializedEvaluationRun)
        .where(
            SpecializedEvaluationRun.process_id == run.process_id,
            SpecializedEvaluationRun.normalization_run_id == run.normalization_run_id,
            SpecializedEvaluationRun.company_id == run.company_id,
            SpecializedEvaluationRun.company_profile_snapshot_id == run.company_profile_snapshot_id,
        )
        .order_by(SpecializedEvaluationRun.domain, SpecializedEvaluationRun.created_at)
    ).all()
    policy = session.get(DecisionPolicyVersion, run.policy_version_id)
    snapshot = session.get(CompanyProfileSnapshot, run.company_profile_snapshot_id)
    financial = session.get(FinancialEvaluationRun, run.financial_evaluation_run_id)
    return {
        "process_id": str(run.process_id),
        "decision_run_id": str(run.id),
        "decision_input_digest": run.input_digest,
        "decision_policy_version": policy.semantic_version if policy else None,
        "decision_policy_hash": policy.content_sha256 if policy else None,
        "decision_engine_version": run.engine_version,
        "decision_outcome": run.engine_outcome,
        "effective_outcome": run.effective_outcome,
        "normalization_run_id": str(run.normalization_run_id),
        "company_profile_snapshot_id": str(run.company_profile_snapshot_id),
        "company_snapshot_digest": snapshot.digest if snapshot else None,
        "financial_evaluation_run_id": str(run.financial_evaluation_run_id),
        "financial_evaluation_digest": financial.input_digest if financial else None,
        "specialized_evaluation_run_ids": [str(item.id) for item in specialized_runs],
        "specialized_evaluation_digests": [item.input_digest for item in specialized_runs],
        "requirement_ids": [str(item.requirement_id) for item in findings],
        "decision_finding_ids": [str(item.id) for item in findings],
        "decision_rule_evaluation_ids": [str(item.id) for item in rules],
        "decision_action_item_ids": [f"{item.id}:{item.status}" for item in actions],
        "decision_review_ids": [str(item.id) for item in reviews],
        "template_version": templates.version,
        "template_hash": templates.template_hash,
        "report_engine_version": REPORT_ENGINE_VERSION,
    }


def build_report_snapshot(
    session: Session, run: DecisionRun, input_manifest: dict[str, Any], input_digest: str
) -> dict[str, Any]:
    process = session.get(Process, run.process_id)
    company = session.get(CompanyProfile, run.company_id)
    snapshot = session.get(CompanyProfileSnapshot, run.company_profile_snapshot_id)
    policy = session.get(DecisionPolicyVersion, run.policy_version_id)
    findings = list(
        session.scalars(
            select(DecisionInputFindingSnapshot)
            .where(DecisionInputFindingSnapshot.decision_run_id == run.id)
            .order_by(
                DecisionInputFindingSnapshot.category, DecisionInputFindingSnapshot.requirement_id
            )
        ).all()
    )
    requirements = {
        req.id: req
        for req in session.scalars(
            select(Requirement).where(
                Requirement.id.in_([finding.requirement_id for finding in findings])
            )
        ).all()
    }
    rules = list(
        session.scalars(
            select(DecisionRuleEvaluationRecord)
            .where(DecisionRuleEvaluationRecord.decision_run_id == run.id)
            .order_by(DecisionRuleEvaluationRecord.priority, DecisionRuleEvaluationRecord.rule_code)
        ).all()
    )
    actions = list(
        session.scalars(
            select(DecisionActionItemRecord)
            .where(DecisionActionItemRecord.decision_run_id == run.id)
            .order_by(DecisionActionItemRecord.priority, DecisionActionItemRecord.created_at)
        ).all()
    )
    action_count_by_requirement: dict[str, int] = {}
    for action in actions:
        for requirement_id in action.requirement_ids or []:
            action_count_by_requirement[requirement_id] = (
                action_count_by_requirement.get(requirement_id, 0) + 1
            )
    matrix = []
    evidence_index = []
    for finding in findings:
        requirement = requirements.get(finding.requirement_id)
        evidence_refs = list(finding.evidence_references or [])
        matrix.append(
            {
                "requirement_id": str(finding.requirement_id),
                "stable_key": requirement.stable_key if requirement else "UNKNOWN",
                "category": finding.category,
                "scope": finding.scope,
                "modality": finding.modality,
                "description": _short_text(requirement.description if requirement else "UNKNOWN"),
                "decision_finding_outcome": finding.outcome,
                "source_domain": finding.evaluation_domain,
                "source_run_id": str(finding.source_run_id) if finding.source_run_id else None,
                "source_result_id": str(finding.source_result_id)
                if finding.source_result_id
                else None,
                "requires_human_review": finding.requires_human_review,
                "review_status": finding.review_status,
                "evidence_count": len(evidence_refs),
                "action_count": action_count_by_requirement.get(str(finding.requirement_id), 0),
                "warning_codes": list(finding.warning_codes or []),
            }
        )
        if evidence_refs:
            for ref in evidence_refs:
                evidence_index.append(_evidence_entry(finding.requirement_id, ref))
        else:
            evidence_index.append(
                {
                    "requirement_id": str(finding.requirement_id),
                    "evidence_type": "MISSING",
                    "document_id": None,
                    "segment_id": None,
                    "source_label": "Sin evidencia asociada al hallazgo",
                    "source_location": {},
                    "document_sha256": None,
                    "quoted_text": None,
                    "validation_status": "MISSING",
                }
            )
    action_rows = [
        {
            "id": str(action.id),
            "action_type": action.action_type,
            "priority": action.priority,
            "status": action.status,
            "title_code": action.title_code,
            "description_code": action.description_code,
            "parameters": action.parameters or {},
            "requirement_ids": action.requirement_ids or [],
            "finding_ids": action.finding_ids or [],
            "due_at": action.due_at.isoformat() if action.due_at else None,
        }
        for action in actions
    ]
    rule_rows = [
        {
            "id": str(rule.id),
            "rule_code": rule.rule_code,
            "status": rule.status,
            "suggested_outcome": rule.suggested_outcome,
            "reason_code": rule.reason_code,
            "fact_payload": rule.fact_payload or {},
        }
        for rule in rules
    ]
    decision_manifest = {
        "process": {
            "id": str(process.id),
            "title": process.title,
            "contracting_entity": process.contracting_entity,
        },
        "company": {
            "id": str(company.id),
            "legal_name": company.legal_name if company else "UNKNOWN",
        },
        "decision_run": {
            "id": str(run.id),
            "engine_outcome": run.engine_outcome,
            "effective_outcome": run.effective_outcome,
        },
        "policy": {
            "version": policy.semantic_version if policy else None,
            "hash": policy.content_sha256 if policy else None,
        },
        "coverage": run.coverage_summary or {},
        "actions": {
            "count": len(action_rows),
            "open_count": sum(
                1 for item in action_rows if item["status"] in {"OPEN", "ACKNOWLEDGED"}
            ),
        },
    }
    risk_summary = _risk_summary(matrix, action_rows, run)
    return {
        "created_at": datetime.now(UTC).isoformat(),
        "input_digest": input_digest,
        "process": {
            "id": str(process.id),
            "title": process.title,
            "contracting_entity": process.contracting_entity,
            "internal_reference": process.internal_reference,
            "secop_reference": process.secop_reference,
        },
        "company": {
            "id": str(company.id) if company else None,
            "legal_name": company.legal_name if company else "UNKNOWN",
            "snapshot_id": str(snapshot.id) if snapshot else None,
            "snapshot_digest": snapshot.digest if snapshot else None,
        },
        "decision": {
            "id": str(run.id),
            "engine_outcome": run.engine_outcome,
            "reviewed_outcome": run.reviewed_outcome,
            "effective_outcome": run.effective_outcome,
            "reason_codes": list(run.reason_codes or []),
            "policy_name": policy.policy_name if policy else None,
            "policy_version": policy.semantic_version if policy else None,
            "dominant_rule": next(
                (rule.rule_code for rule in rules if rule.status == "TRIGGERED"), None
            ),
        },
        "coverage": run.coverage_summary or {},
        "findings": [
            {
                "id": str(item.id),
                "requirement_id": str(item.requirement_id),
                "outcome": item.outcome,
                "source_type": item.source_type,
            }
            for item in findings
        ],
        "rules": rule_rows,
        "requirements_matrix": matrix,
        "evidence_index": evidence_index,
        "actions": action_rows,
        "decision_manifest": decision_manifest,
        "evaluation_summaries": _evaluation_summaries(session, run),
        "risk_summary": risk_summary,
        "technical_manifest": {
            "input_manifest": input_manifest,
            "report_engine_version": REPORT_ENGINE_VERSION,
            "template_version": REPORT_TEMPLATE_VERSION,
            "decision_run_id": str(run.id),
        },
    }


def generate_report_package(
    session: Session, package_id: UUID, worker_id: str
) -> DecisionReportPackage:
    package = session.get(DecisionReportPackage, package_id)
    if package is None:
        raise RuntimeError("report package missing")
    run = session.get(DecisionRun, package.decision_run_id)
    if run is None:
        raise RuntimeError("decision run missing")
    templates = load_report_templates(package.template_version)
    snapshot = build_report_snapshot(session, run, package.input_manifest, package.input_digest)
    artifacts = render_artifacts(snapshot, templates)
    manifest_items = [
        artifact_record(a.filename, a.artifact_type, a.content_type, a.content) for a in artifacts
    ]
    package_digest = artifact_manifest_digest(manifest_items)
    package_manifest = {
        "package_id": str(package.id),
        "package_version": PACKAGE_VERSION,
        "input_digest": package.input_digest,
        "package_digest": package_digest,
        "artifacts": manifest_items,
    }
    package_manifest_bytes = (canonical_json(package_manifest) + "\n").encode("utf-8")
    artifacts.append(
        RenderedArtifact(
            "package-manifest.json",
            "PACKAGE_MANIFEST_JSON",
            "application/json",
            package_manifest_bytes,
        )
    )
    zip_bytes = build_zip(artifacts)
    artifacts.append(
        RenderedArtifact("decision-package.zip", "PACKAGE_ZIP", "application/zip", zip_bytes)
    )
    storage = ReportArtifactStorage()
    stored_keys: list[str] = []
    try:
        for artifact in artifacts:
            key = storage.key_for(package.id, artifact.filename)
            storage.save_bytes(artifact.content, key)
            stored_keys.append(key)
            record = artifact_record(
                artifact.filename, artifact.artifact_type, artifact.content_type, artifact.content
            )
            session.add(
                DecisionReportArtifact(
                    id=uuid4(),
                    package_id=package.id,
                    artifact_type=artifact.artifact_type,
                    filename=artifact.filename,
                    content_type=artifact.content_type,
                    storage_key=key,
                    size_bytes=int(record["size_bytes"]),
                    sha256=str(record["sha256"]),
                    template_version=templates.version,
                    source_digest=package.input_digest,
                )
            )
    except Exception:
        for key in stored_keys:
            storage.delete(key)
        raise
    for sequence, (code, title) in enumerate(
        [
            ("executive_summary", "Resumen ejecutivo"),
            ("coverage", "Cobertura"),
            ("evidence", "Evidencias"),
            ("actions", "Acciones y pendientes"),
            ("technical_manifest", "Manifiesto tecnico"),
        ],
        start=1,
    ):
        session.add(
            DecisionReportSection(
                id=uuid4(),
                package_id=package.id,
                section_code=code,
                title=title,
                sequence=sequence,
                summary_payload={"input_digest": package.input_digest},
                warning_codes=list(run.warnings or []),
            )
        )
    now = datetime.now(UTC)
    package.package_digest = package_digest
    package.artifact_count = len(artifacts)
    package.warning_count = run.warning_count
    package.status = (
        DecisionReportPackageStatus.COMPLETED_WITH_WARNINGS.value
        if run.warning_count
        else DecisionReportPackageStatus.COMPLETED.value
    )
    package.published_at = now
    package.created_by = worker_id
    return package


def _evidence_entry(requirement_id: UUID, ref: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": str(requirement_id),
        "evidence_type": str(ref.get("evidence_type") or ref.get("type") or "REFERENCE"),
        "document_id": ref.get("document_id"),
        "segment_id": ref.get("segment_id"),
        "source_label": _short_text(
            str(ref.get("source_label") or ref.get("label") or "Evidencia")
        ),
        "source_location": ref.get("source_location") or {},
        "document_sha256": ref.get("document_sha256") or ref.get("sha256"),
        "quoted_text": _short_text(str(ref.get("quoted_text") or ref.get("quote") or "")) or None,
        "validation_status": ref.get("validation_status"),
    }


def _short_text(value: str, limit: int = 500) -> str:
    clean = " ".join((value or "").split())
    return clean[:limit]


def _evaluation_summaries(session: Session, run: DecisionRun) -> list[str]:
    financial = session.get(FinancialEvaluationRun, run.financial_evaluation_run_id)
    specialized = session.scalars(
        select(SpecializedEvaluationRun)
        .where(
            SpecializedEvaluationRun.process_id == run.process_id,
            SpecializedEvaluationRun.normalization_run_id == run.normalization_run_id,
            SpecializedEvaluationRun.company_id == run.company_id,
            SpecializedEvaluationRun.company_profile_snapshot_id == run.company_profile_snapshot_id,
        )
        .order_by(SpecializedEvaluationRun.domain)
    ).all()
    rows = []
    if financial:
        rows.append(
            f"Financiera: run {financial.id} estado {financial.status}, "
            f"evaluados {financial.evaluated_count}, unknown {financial.unknown_count}, "
            f"conflictos {financial.conflicting_count}."
        )
    else:
        rows.append("Financiera: no ejecutada.")
    domains = {item.domain: item for item in specialized}
    for domain in ["LEGAL", "EXPERIENCE", "TECHNICAL"]:
        item = domains.get(domain)
        if item:
            rows.append(
                f"{domain}: run {item.id} estado {item.status}, "
                f"evaluados {item.evaluated_count}, unknown {item.unknown_count}, "
                f"conflictos {item.conflicting_count}."
            )
        else:
            rows.append(f"{domain}: no ejecutada.")
    return rows


def _risk_summary(
    matrix: list[dict[str, Any]], actions: list[dict[str, Any]], run: DecisionRun
) -> list[str]:
    risks = [
        "La decision es preliminar y requiere revision humana antes de uso externo.",
        "No hay firma digital ni concepto juridico definitivo en esta fase.",
    ]
    if any(row["decision_finding_outcome"] == "UNKNOWN" for row in matrix):
        risks.append("Existen requisitos con resultado UNKNOWN.")
    if any(row["decision_finding_outcome"] == "NOT_EVALUATED" for row in matrix):
        risks.append("Existen requisitos o dimensiones no evaluadas.")
    if any(row["decision_finding_outcome"] == "CONFLICTING_EVIDENCE" for row in matrix):
        risks.append("Existe evidencia conflictiva que requiere revision.")
    if any(row["status"] in {"OPEN", "ACKNOWLEDGED"} for row in actions):
        risks.append("Existen acciones abiertas o reconocidas.")
    if run.requires_human_review:
        risks.append("El motor marco revision humana pendiente.")
    return risks
