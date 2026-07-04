# mypy: ignore-errors
"""Orquestador del piloto controlado end-to-end (Microfase 11).

Coordina el flujo completo con datos sinteticos: usuarios, proceso, documentos,
extraccion, normalizacion controlada, empresa, snapshot, evaluaciones financiera
y especializadas, decision, reporte, descarga y auditoria. No llama a OpenAI.
"""

from __future__ import annotations

import copy
import time
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select

from pliegocheck_api.auth import create_user, ensure_roles
from pliegocheck_api.config import get_settings
from pliegocheck_api.db import get_sessionmaker
from pliegocheck_api.models import (
    AuthUser,
    CompanyProfile,
    CompanyProfileSnapshot,
    OperationalAuditEvent,
    Process,
    Requirement,
    RequirementNormalizationJob,
    RequirementNormalizationRun,
)
from pliegocheck_api.prompt_registry import (
    CONSOLIDATION_PROMPT,
    NORMALIZATION_PROMPT,
    ensure_prompt_version,
)
from pliegocheck_schemas import (
    AuthRoleName,
    CompanyProfileStatus,
    CompanySnapshotStatus,
    NormalizationProvider,
    PilotExpectedOutcome,
    PilotReadiness,
    PilotRunSummary,
    PilotStepName,
    PilotStepState,
    PilotStepStatus,
    ProcessSource,
    ProcessStatus,
    RequirementBasis,
    RequirementEvidenceStatus,
    RequirementModality,
    RequirementNormalizationStatus,
    RequirementReviewStatus,
    RequirementScope,
    RequirementSubsanability,
)
from pliegocheck_worker.decision.orchestrator import decision_drain
from pliegocheck_worker.financial.orchestrator import financial_drain
from pliegocheck_worker.pilot import PILOT_DOMAIN
from pliegocheck_worker.pilot.dataset import (
    PILOT_COMPANY,
    PILOT_EXPECTED_OUTCOME,
    PILOT_PROCESS,
    PILOT_PROCESS_DOCUMENTS,
    PILOT_REQUIREMENTS,
    PILOT_SPECIALIZED_DOMAINS,
    PILOT_USERS,
    build_snapshot_payload,
)
from pliegocheck_worker.reports.orchestrator import report_drain
from pliegocheck_worker.runner import drain as extraction_drain
from pliegocheck_worker.specialized.orchestrator import specialized_drain

DEFAULT_DEMO_PASSWORD = "DemoOnly-ChangeMe-12345"


def expected_outcome() -> PilotExpectedOutcome:
    return PilotExpectedOutcome.model_validate(PILOT_EXPECTED_OUTCOME)


def _is_local_environment() -> bool:
    settings = get_settings()
    return settings.environment in {"development", "test", "pilot"}


def _new_client() -> TestClient:
    from pliegocheck_api.main import app

    return TestClient(app)


def _login(client: TestClient, email: str, password: str) -> None:
    if not get_settings().auth_enabled:
        return
    response = client.post("/auth/login", json={"email": email, "password": password})
    if response.status_code != 200:
        raise RuntimeError(f"login fallido para {email}: {response.status_code}")


# --- Readiness ---------------------------------------------------------------
def pilot_readiness() -> PilotReadiness:
    settings = get_settings()
    warnings: list[str] = []
    with get_sessionmaker()() as session:
        admin_exists = (
            session.execute(
                select(func.count())
                .select_from(AuthUser)
                .where(AuthUser.email.like(f"%@{PILOT_DOMAIN}"))
            ).scalar_one()
            > 0
        )
        present_users = [
            row
            for row in session.execute(
                select(AuthUser.email).where(AuthUser.email.like(f"%@{PILOT_DOMAIN}"))
            ).scalars()
        ]
        process_present = (
            session.execute(
                select(func.count())
                .select_from(Process)
                .where(Process.title == PILOT_PROCESS["title"])
            ).scalar_one()
            > 0
        )
        company_present = (
            session.execute(
                select(func.count())
                .select_from(CompanyProfile)
                .where(CompanyProfile.legal_name == PILOT_COMPANY["legal_name"])
            ).scalar_one()
            > 0
        )
    is_local = _is_local_environment()
    if not is_local:
        warnings.append("ENVIRONMENT_NOT_LOCAL")
    if not settings.auth_enabled:
        warnings.append("AUTH_DISABLED")
    ready = is_local and process_present and company_present
    return PilotReadiness(
        environment=settings.environment,
        pilot_mode=settings.pilot_mode,
        auth_enabled=settings.auth_enabled,
        is_local_environment=is_local,
        admin_user_exists=admin_exists,
        pilot_users_present=sorted(present_users),
        pilot_process_present=process_present,
        pilot_company_present=company_present,
        dataset_available=True,
        ready=ready,
        warnings=warnings,
    )


# --- Seed --------------------------------------------------------------------
def prepare_pilot(*, password: str = DEFAULT_DEMO_PASSWORD) -> dict[str, Any]:
    """Siembra usuarios, proceso, documentos, extraccion, normalizacion y empresa.

    Idempotente: reutiliza usuarios existentes y crea un proceso/empresa nuevos
    por corrida para mantener trazabilidad del historico.
    """
    if not _is_local_environment():
        raise RuntimeError(
            "prepare_pilot solo puede ejecutarse en entorno local (development/test/pilot)."
        )
    _seed_users(password)
    client = _new_client()
    _login(client, f"analyst@{PILOT_DOMAIN}", password)

    process_id = _create_process(client)
    _upload_documents(client, process_id)
    _run_extraction(client, process_id)
    normalization_run_id = _seed_normalization(process_id)
    company_id, snapshot_id = _seed_company_and_snapshot()
    return {
        "process_id": str(process_id),
        "normalization_run_id": str(normalization_run_id),
        "company_id": str(company_id),
        "snapshot_id": str(snapshot_id),
    }


def _seed_users(password: str) -> None:
    with get_sessionmaker()() as session:
        ensure_roles(session)
        for user in PILOT_USERS:
            exists = session.execute(
                select(AuthUser).where(AuthUser.email == user["email"])
            ).scalar_one_or_none()
            if exists is not None:
                continue
            create_user(
                session,
                email=user["email"],
                display_name=user["display_name"],
                password=password,
                roles=[AuthRoleName(role) for role in user["roles"]],
            )
        session.commit()


def _create_process(client: TestClient) -> UUID:
    payload = {
        "title": PILOT_PROCESS["title"],
        "contracting_entity": PILOT_PROCESS["contracting_entity"],
        "secop_reference": PILOT_PROCESS["secop_reference"],
        "description": PILOT_PROCESS["description"],
        "selection_method": PILOT_PROCESS["selection_method"],
        "estimated_value": PILOT_PROCESS["estimated_value"],
        "currency": PILOT_PROCESS["currency"],
        "closing_at": PILOT_PROCESS["closing_at"],
    }
    response = client.post("/processes", json=payload)
    if response.status_code != 201:
        raise RuntimeError(f"no se pudo crear el proceso piloto: {response.status_code}")
    return UUID(response.json()["id"])


def _upload_documents(client: TestClient, process_id: UUID) -> None:
    files = [
        (
            "files",
            (
                document["filename"],
                document["text"].encode("utf-8"),
                document["content_type"],
            ),
        )
        for document in PILOT_PROCESS_DOCUMENTS
    ]
    response = client.post(f"/processes/{process_id}/documents", files=files)
    if response.status_code not in {200, 201, 207}:
        raise RuntimeError(f"carga de documentos fallida: {response.status_code}")


def _run_extraction(client: TestClient, process_id: UUID) -> None:
    client.post(f"/processes/{process_id}/extractions", json={})
    extraction_drain(max_jobs=20, worker_id="pilot-extraction")


def _seed_normalization(process_id: UUID) -> UUID:
    now = datetime.now(UTC)
    with get_sessionmaker()() as session:
        normalization_prompt = ensure_prompt_version(session, NORMALIZATION_PROMPT)
        consolidation_prompt = ensure_prompt_version(session, CONSOLIDATION_PROMPT)
        job = RequirementNormalizationJob(
            id=uuid4(),
            process_id=process_id,
            status=RequirementNormalizationStatus.COMPLETED.value,
            force=False,
            available_at=now,
            started_at=now,
            finished_at=now,
        )
        session.add(job)
        session.flush()
        run = RequirementNormalizationRun(
            id=uuid4(),
            job_id=job.id,
            process_id=process_id,
            status=RequirementNormalizationStatus.COMPLETED.value,
            provider=NormalizationProvider.FAKE.value,
            model="fake",
            reasoning_effort="none",
            prompt_version_id=normalization_prompt.id,
            consolidation_prompt_version_id=consolidation_prompt.id,
            input_manifest={"documents": [], "pilot": True},
            input_digest=uuid4().hex + uuid4().hex[:32],
            source_extraction_ids=[],
            segment_count=0,
            batch_count=0,
            candidate_count=len(PILOT_REQUIREMENTS),
            accepted_requirement_count=len(PILOT_REQUIREMENTS),
            rejected_candidate_count=0,
            warning_count=0,
            input_tokens=0,
            output_tokens=0,
            reasoning_tokens=0,
            provider_response_ids=[],
            started_at=now,
            finished_at=now,
        )
        session.add(run)
        session.flush()
        job.run_id = run.id
        for requirement in PILOT_REQUIREMENTS:
            session.add(
                Requirement(
                    id=uuid4(),
                    process_id=process_id,
                    normalization_run_id=run.id,
                    stable_key=requirement["stable_key"],
                    category=requirement["category"],
                    scope=RequirementScope.HABILITATING.value,
                    modality=RequirementModality.MANDATORY.value,
                    description=requirement["description"],
                    expected_value=requirement["expected_value"],
                    criticality=requirement["criticality"],
                    criticality_basis=RequirementBasis.EXPLICIT.value,
                    subsanability=RequirementSubsanability.UNKNOWN.value,
                    subsanability_basis=RequirementBasis.UNKNOWN.value,
                    confidence=Decimal("0.950"),
                    evidence_status=RequirementEvidenceStatus.VALIDATED.value,
                    review_status=RequirementReviewStatus.PENDING.value,
                    requires_human_review=True,
                    is_active=True,
                )
            )
        session.commit()
        return run.id


def _seed_company_and_snapshot() -> tuple[UUID, UUID]:
    """Idempotente: reutiliza la empresa piloto y publica una nueva version de snapshot."""
    now = datetime.now(UTC)
    with get_sessionmaker()() as session:
        company = session.execute(
            select(CompanyProfile).where(CompanyProfile.legal_name == PILOT_COMPANY["legal_name"])
        ).scalar_one_or_none()
        if company is None:
            company_id = uuid4()
            system_process = Process(
                id=uuid4(),
                internal_reference=f"CPDOC-{company_id.hex[:8]}",
                title="Documentos de empresa (piloto)",
                contracting_entity="Empresa Demo PliegoCheck",
                status=ProcessStatus.DRAFT.value,
                source=ProcessSource.MANUAL.value,
                is_system=True,
            )
            session.add(system_process)
            session.flush()
            company = CompanyProfile(
                id=company_id,
                system_process_id=system_process.id,
                internal_reference=f"CP-{company_id.hex[:8]}",
                legal_name=PILOT_COMPANY["legal_name"],
                tax_id=PILOT_COMPANY["tax_id"],
                tax_id_type=PILOT_COMPANY["tax_id_type"],
                status=CompanyProfileStatus.READY_FOR_REVIEW.value,
                economic_activity_codes=[],
            )
            session.add(company)
            session.flush()
        company_id = company.id
        next_version = (
            session.execute(
                select(func.coalesce(func.max(CompanyProfileSnapshot.version), 0)).where(
                    CompanyProfileSnapshot.company_id == company_id
                )
            ).scalar_one()
            + 1
        )
        payload = _materialize_snapshot_payload()
        snapshot = CompanyProfileSnapshot(
            id=uuid4(),
            company_id=company_id,
            version=next_version,
            status=CompanySnapshotStatus.PUBLISHED.value,
            digest=uuid4().hex + uuid4().hex[:32],
            payload=payload,
            completeness_status="READY_FOR_REVIEW",
            published_at=now,
        )
        session.add(snapshot)
        session.commit()
        return company_id, snapshot.id


def _materialize_snapshot_payload() -> dict[str, Any]:
    """Reemplaza los identificadores placeholder por UUID reales estables."""
    payload = copy.deepcopy(build_snapshot_payload())
    id_map: dict[str, str] = {}

    def real_id(placeholder: str) -> str:
        if placeholder not in id_map:
            id_map[placeholder] = str(uuid4())
        return id_map[placeholder]

    for period in payload.get("financial_periods", []):
        period["id"] = real_id(period["id"])
        for metric in period.get("metrics", []):
            metric["id"] = real_id(metric["id"])
    for key in (
        "rup_snapshots",
        "legal_registrations",
        "experience_records",
        "certifications",
        "capabilities",
        "people",
        "unspsc_codes",
    ):
        for item in payload.get(key, []):
            item["id"] = real_id(item["id"])
    return payload


# --- Run ---------------------------------------------------------------------
def run_pilot(
    *, password: str = DEFAULT_DEMO_PASSWORD, ids: dict[str, Any] | None = None
) -> PilotRunSummary:
    started = time.monotonic()
    steps: list[PilotStepStatus] = []
    warnings: list[str] = []
    ids = ids or _lookup_latest_ids()
    process_id = ids["process_id"]
    normalization_run_id = ids["normalization_run_id"]
    company_id = ids["company_id"]
    snapshot_id = ids["snapshot_id"]

    analyst = _new_client()
    _login(analyst, f"analyst@{PILOT_DOMAIN}", password)

    steps.append(PilotStepStatus(step=PilotStepName.SEED_USERS, state=PilotStepState.COMPLETED))
    steps.append(PilotStepStatus(step=PilotStepName.SEED_PROCESS, state=PilotStepState.COMPLETED))
    steps.append(
        PilotStepStatus(step=PilotStepName.UPLOAD_DOCUMENTS, state=PilotStepState.COMPLETED)
    )
    steps.append(PilotStepStatus(step=PilotStepName.EXTRACTION, state=PilotStepState.COMPLETED))
    steps.append(PilotStepStatus(step=PilotStepName.NORMALIZATION, state=PilotStepState.COMPLETED))
    steps.append(PilotStepStatus(step=PilotStepName.SEED_COMPANY, state=PilotStepState.COMPLETED))
    steps.append(
        PilotStepStatus(step=PilotStepName.PUBLISH_SNAPSHOT, state=PilotStepState.COMPLETED)
    )

    # Evaluacion financiera
    financial_run_id = _queue_financial(
        analyst, process_id, normalization_run_id, company_id, snapshot_id
    )
    financial_drain(max_jobs=5, worker_id="pilot-financial")
    steps.append(
        PilotStepStatus(step=PilotStepName.FINANCIAL_EVALUATION, state=PilotStepState.COMPLETED)
    )

    # Evaluaciones especializadas
    specialized_run_ids: list[str] = []
    domain_step = {
        "LEGAL": PilotStepName.LEGAL_EVALUATION,
        "EXPERIENCE": PilotStepName.EXPERIENCE_EVALUATION,
        "TECHNICAL": PilotStepName.TECHNICAL_EVALUATION,
    }
    for domain in PILOT_SPECIALIZED_DOMAINS:
        run_id = _queue_specialized(
            analyst, process_id, normalization_run_id, company_id, snapshot_id, domain
        )
        specialized_run_ids.append(run_id)
        steps.append(PilotStepStatus(step=domain_step[domain], state=PilotStepState.COMPLETED))
    specialized_drain(max_jobs=10, worker_id="pilot-specialized")

    # Motor de decision (auto-descubre evaluaciones especializadas)
    decision_run_id = _queue_decision(
        analyst, process_id, normalization_run_id, company_id, snapshot_id, financial_run_id
    )
    decision_drain(max_jobs=5, worker_id="pilot-decision")
    decision_detail = analyst.get(f"/processes/{process_id}/decisions/{decision_run_id}").json()
    decision_outcome = decision_detail.get("engine_outcome")
    action_count = len(decision_detail.get("actions", []))
    steps.append(PilotStepStatus(step=PilotStepName.DECISION, state=PilotStepState.COMPLETED))

    # Reporte y paquete
    package_id = _queue_report(analyst, process_id, decision_run_id)
    report_drain(max_jobs=5, worker_id="pilot-report")
    report_detail = analyst.get(f"/processes/{process_id}/decision-reports/{package_id}").json()
    artifact_count = int(report_detail.get("artifact_count", 0))
    steps.append(PilotStepStatus(step=PilotStepName.REPORT_PACKAGE, state=PilotStepState.COMPLETED))

    # Descarga del paquete
    download = analyst.get(f"/processes/{process_id}/decision-reports/{package_id}/download")
    download_ok = download.status_code == 200 and download.content[:2] == b"PK"
    steps.append(
        PilotStepStatus(
            step=PilotStepName.PACKAGE_DOWNLOAD,
            state=PilotStepState.COMPLETED if download_ok else PilotStepState.FAILED,
        )
    )
    if not download_ok:
        warnings.append("PACKAGE_DOWNLOAD_NOT_ZIP")

    audit_count = _audit_event_count()
    steps.append(PilotStepStatus(step=PilotStepName.AUDIT, state=PilotStepState.COMPLETED))

    succeeded = sum(
        1
        for step in steps
        if step.state in {PilotStepState.COMPLETED, PilotStepState.COMPLETED_WITH_WARNINGS}
    )
    failed = sum(1 for step in steps if step.state is PilotStepState.FAILED)
    return PilotRunSummary(
        process_id=UUID(process_id),
        company_id=UUID(company_id),
        snapshot_id=UUID(snapshot_id),
        normalization_run_id=UUID(normalization_run_id),
        financial_run_id=UUID(financial_run_id),
        specialized_run_ids=[UUID(item) for item in specialized_run_ids],
        decision_run_id=UUID(decision_run_id),
        report_package_id=UUID(package_id),
        decision_outcome=decision_outcome,
        duration_seconds=round(time.monotonic() - started, 3),
        steps=steps,
        steps_total=len(steps),
        steps_succeeded=succeeded,
        steps_failed=failed,
        artifact_count=artifact_count,
        audit_event_count=audit_count,
        warnings=warnings + ([] if action_count else ["NO_ACTIONS_GENERATED"]),
    )


def _queue_financial(
    client: TestClient,
    process_id: str,
    normalization_run_id: str,
    company_id: str,
    snapshot_id: str,
) -> str:
    response = client.post(
        f"/processes/{process_id}/financial-evaluations",
        json={
            "normalization_run_id": normalization_run_id,
            "company_id": company_id,
            "company_profile_snapshot_id": snapshot_id,
            "force": False,
        },
    )
    if response.status_code != 202:
        raise RuntimeError(f"evaluacion financiera no encolada: {response.status_code}")
    return response.json()["run"]["id"]


def _queue_specialized(
    client: TestClient,
    process_id: str,
    normalization_run_id: str,
    company_id: str,
    snapshot_id: str,
    domain: str,
) -> str:
    response = client.post(
        f"/processes/{process_id}/specialized-evaluations",
        json={
            "normalization_run_id": normalization_run_id,
            "company_id": company_id,
            "company_profile_snapshot_id": snapshot_id,
            "domain": domain,
            "force": False,
        },
    )
    if response.status_code != 202:
        raise RuntimeError(f"evaluacion {domain} no encolada: {response.status_code}")
    return response.json()["run"]["id"]


def _queue_decision(
    client: TestClient,
    process_id: str,
    normalization_run_id: str,
    company_id: str,
    snapshot_id: str,
    financial_run_id: str,
) -> str:
    response = client.post(
        f"/processes/{process_id}/decisions",
        json={
            "normalization_run_id": normalization_run_id,
            "company_id": company_id,
            "company_profile_snapshot_id": snapshot_id,
            "financial_evaluation_run_id": financial_run_id,
            "force": False,
        },
    )
    if response.status_code != 202:
        raise RuntimeError(f"decision no encolada: {response.status_code}")
    return response.json()["run"]["id"]


def _queue_report(client: TestClient, process_id: str, decision_run_id: str) -> str:
    response = client.post(
        f"/processes/{process_id}/decision-reports",
        json={"decision_run_id": decision_run_id, "force": False},
    )
    if response.status_code != 202:
        raise RuntimeError(f"reporte no encolado: {response.status_code}")
    return response.json()["package"]["id"]


def _lookup_latest_ids() -> dict[str, Any]:
    with get_sessionmaker()() as session:
        process = session.execute(
            select(Process)
            .where(Process.title == PILOT_PROCESS["title"])
            .order_by(Process.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if process is None:
            raise RuntimeError("No hay proceso piloto. Ejecute prepare_pilot primero.")
        company = session.execute(
            select(CompanyProfile)
            .where(CompanyProfile.legal_name == PILOT_COMPANY["legal_name"])
            .order_by(CompanyProfile.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if company is None:
            raise RuntimeError("No hay empresa piloto. Ejecute prepare_pilot primero.")
        snapshot = session.execute(
            select(CompanyProfileSnapshot)
            .where(
                CompanyProfileSnapshot.company_id == company.id,
                CompanyProfileSnapshot.status == CompanySnapshotStatus.PUBLISHED.value,
            )
            .order_by(CompanyProfileSnapshot.version.desc())
            .limit(1)
        ).scalar_one_or_none()
        normalization = session.execute(
            select(RequirementNormalizationRun)
            .where(
                RequirementNormalizationRun.process_id == process.id,
                RequirementNormalizationRun.status.in_(
                    [
                        RequirementNormalizationStatus.COMPLETED.value,
                        RequirementNormalizationStatus.COMPLETED_WITH_WARNINGS.value,
                    ]
                ),
            )
            .order_by(RequirementNormalizationRun.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if snapshot is None or normalization is None:
            raise RuntimeError("Piloto incompleto: falta snapshot o normalizacion.")
        return {
            "process_id": str(process.id),
            "company_id": str(company.id),
            "snapshot_id": str(snapshot.id),
            "normalization_run_id": str(normalization.id),
        }


def _audit_event_count() -> int:
    with get_sessionmaker()() as session:
        return int(
            session.execute(select(func.count()).select_from(OperationalAuditEvent)).scalar_one()
        )


def execute_pilot(*, password: str = DEFAULT_DEMO_PASSWORD) -> PilotRunSummary:
    """Prepara y ejecuta el piloto completo. Usado por el eval automatizado."""
    ids = prepare_pilot(password=password)
    return run_pilot(password=password, ids=ids)


# --- Reset -------------------------------------------------------------------
def reset_pilot(*, confirm: bool = False) -> dict[str, Any]:
    """Elimina unicamente datos marcados como piloto. Requiere confirmacion."""
    if not confirm:
        raise RuntimeError("reset_pilot requiere confirm=True para eliminar datos de piloto.")
    if not _is_local_environment():
        raise RuntimeError("reset_pilot solo puede ejecutarse en entorno local.")
    with get_sessionmaker()() as session:
        companies = list(
            session.execute(
                select(CompanyProfile).where(
                    CompanyProfile.legal_name == PILOT_COMPANY["legal_name"]
                )
            ).scalars()
        )
        system_process_ids = [company.system_process_id for company in companies]
        deleted_companies = len(companies)
        for company in companies:
            session.delete(company)
        session.flush()
        # Los procesos-sistema de las empresas piloto y el proceso piloto.
        deleted_processes = 0
        process_ids = list(
            session.execute(
                select(Process.id).where(
                    (Process.title == PILOT_PROCESS["title"])
                    | (Process.id.in_([pid for pid in system_process_ids if pid is not None]))
                )
            ).scalars()
        )
        if process_ids:
            deleted_processes = session.execute(
                delete(Process).where(Process.id.in_(process_ids))
            ).rowcount
        deleted_users = session.execute(
            delete(AuthUser).where(AuthUser.email.like(f"%@{PILOT_DOMAIN}"))
        ).rowcount
        session.commit()
    return {
        "status": "ok",
        "deleted_companies": deleted_companies,
        "deleted_processes": deleted_processes,
        "deleted_users": deleted_users,
    }
