# mypy: ignore-errors
"""Eval end-to-end del piloto controlado con datos sinteticos.

No usa OpenAI, no usa datos reales. Ejecuta el flujo completo con auth activo
y valida roles, decision, reporte, ZIP, auditoria y coincidencia con el
resultado esperado del dataset.
"""

from http import HTTPStatus
from zipfile import ZipFile

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def pilot_env(monkeypatch):
    monkeypatch.setenv("PLIEGOCHECK_AUTH_ENABLED", "true")
    monkeypatch.setenv("PLIEGOCHECK_ENVIRONMENT", "test")
    monkeypatch.setenv("PLIEGOCHECK_AUTH_SECRET_KEY", "pilot-e2e-secret-not-real")
    monkeypatch.setenv("PLIEGOCHECK_ALLOW_FAKE_NORMALIZATION_PROVIDER", "true")
    from pliegocheck_api.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _client() -> TestClient:
    from pliegocheck_api.main import app

    return TestClient(app)


def test_pilot_end_to_end_flow(pilot_env) -> None:
    from pliegocheck_worker.pilot import PILOT_DOMAIN
    from pliegocheck_worker.pilot.orchestrator import (
        DEFAULT_DEMO_PASSWORD,
        execute_pilot,
        expected_outcome,
        pilot_readiness,
        reset_pilot,
    )

    # Limpia cualquier residuo de piloto previo para una corrida reproducible.
    reset_pilot(confirm=True)

    summary = execute_pilot(password=DEFAULT_DEMO_PASSWORD)
    expected = expected_outcome()

    # 1. Auth enabled + readiness.
    readiness = pilot_readiness()
    assert readiness.auth_enabled is True
    assert readiness.is_local_environment is True
    assert readiness.pilot_process_present is True
    assert readiness.pilot_company_present is True
    assert set(
        f"{role}@{PILOT_DOMAIN}" for role in ("admin", "analyst", "reviewer", "viewer")
    ) <= set(readiness.pilot_users_present)

    # 2. Flujo end-to-end produce todos los artefactos.
    assert summary.synthetic_data_only is True
    assert summary.steps_failed == 0, summary.model_dump()
    assert summary.decision_run_id is not None
    assert summary.report_package_id is not None
    assert len(summary.specialized_run_ids) == 3

    # 3. Resultado coincide con expected-outcomes del dataset (no forzado a GO).
    assert summary.decision_outcome == expected.decision_outcome
    assert summary.decision_outcome != "GO"
    assert summary.artifact_count == expected.report_artifact_count

    process_id = str(summary.process_id)
    decision_run_id = str(summary.decision_run_id)
    package_id = str(summary.report_package_id)

    # 4. Roles: viewer no puede crear; reviewer puede revisar; login/logout.
    analyst = _client()
    assert (
        analyst.post(
            "/auth/login",
            json={"email": f"analyst@{PILOT_DOMAIN}", "password": DEFAULT_DEMO_PASSWORD},
        ).status_code
        == HTTPStatus.OK
    )

    viewer = _client()
    assert (
        viewer.post(
            "/auth/login",
            json={"email": f"viewer@{PILOT_DOMAIN}", "password": DEFAULT_DEMO_PASSWORD},
        ).status_code
        == HTTPStatus.OK
    )
    # Viewer puede leer procesos pero no crear.
    assert viewer.get(f"/processes/{process_id}").status_code == HTTPStatus.OK
    create_forbidden = viewer.post("/processes", json={"title": "x", "contracting_entity": "y"})
    assert create_forbidden.status_code == HTTPStatus.FORBIDDEN

    # 5. Cobertura de outcomes (estado previo a la revision).
    detail = analyst.get(f"/processes/{process_id}/decisions/{decision_run_id}").json()
    finding_outcomes = [finding["outcome"] for finding in detail["findings"]]
    assert finding_outcomes.count("COMPLIES") >= expected.financial_complies_min
    assert finding_outcomes.count("DOES_NOT_COMPLY") >= expected.financial_does_not_comply_min
    assert finding_outcomes.count("UNKNOWN") >= expected.unknown_min
    assert len(detail["actions"]) >= expected.action_min
    assert detail["requires_human_review"] is True

    # 6. Reviewer confirma; el engine outcome no cambia con la revision.
    reviewer = _client()
    assert (
        reviewer.post(
            "/auth/login",
            json={"email": f"reviewer@{PILOT_DOMAIN}", "password": DEFAULT_DEMO_PASSWORD},
        ).status_code
        == HTTPStatus.OK
    )
    review = reviewer.post(
        f"/processes/{process_id}/decisions/{decision_run_id}/review",
        json={
            "action": "CONFIRM",
            "reason": "Revision sintetica de piloto: se confirma el resultado preliminar.",
        },
    )
    assert review.status_code == HTTPStatus.OK, review.text
    assert review.json()["run"]["engine_outcome"] == expected.decision_outcome

    # 7. ZIP descargable, seguro y sin secretos.
    zip_response = reviewer.get(f"/processes/{process_id}/decision-reports/{package_id}/download")
    assert zip_response.status_code == HTTPStatus.OK
    assert zip_response.content[:2] == b"PK"
    import io

    with ZipFile(io.BytesIO(zip_response.content)) as archive:
        names = archive.namelist()
        blob = b"".join(archive.read(name) for name in names)
    assert ".env" not in names
    assert all("/" not in name and "\\" not in name and ".." not in name for name in names)
    lowered = blob.lower()
    for secret_marker in (b"password_hash", b"begin rsa", b"begin openssh", b"aws_secret"):
        assert secret_marker not in lowered
    assert b"C:\\" not in blob

    # 8. Auditoria contiene eventos y logout invalida la sesion.
    assert summary.audit_event_count > 0
    assert reviewer.post("/auth/logout").status_code == HTTPStatus.OK
    assert reviewer.get(f"/processes/{process_id}").status_code == HTTPStatus.UNAUTHORIZED


def test_pilot_reset_is_safe(pilot_env) -> None:
    from sqlalchemy import func, select

    # Un usuario no-piloto no debe eliminarse.
    from pliegocheck_api.auth import create_user, ensure_roles
    from pliegocheck_api.db import get_sessionmaker
    from pliegocheck_api.models import AuthUser, Process
    from pliegocheck_schemas import AuthRoleName
    from pliegocheck_worker.pilot import PILOT_DOMAIN
    from pliegocheck_worker.pilot.orchestrator import (
        DEFAULT_DEMO_PASSWORD,
        prepare_pilot,
        reset_pilot,
    )

    reset_pilot(confirm=True)
    keep_email = "keep-nonpilot@example.com"
    with get_sessionmaker()() as session:
        ensure_roles(session)
        if (
            session.execute(
                select(AuthUser).where(AuthUser.email == keep_email)
            ).scalar_one_or_none()
            is None
        ):
            create_user(
                session,
                email=keep_email,
                display_name="No Pilot",
                password="keep-this-user-1234",
                roles=[AuthRoleName.VIEWER],
            )
        session.commit()

    prepare_pilot(password=DEFAULT_DEMO_PASSWORD)
    # reset sin confirmacion falla.
    with pytest.raises(RuntimeError):
        reset_pilot(confirm=False)
    result = reset_pilot(confirm=True)
    assert result["status"] == "ok"

    with get_sessionmaker()() as session:
        pilot_users = session.execute(
            select(func.count())
            .select_from(AuthUser)
            .where(AuthUser.email.like(f"%@{PILOT_DOMAIN}"))
        ).scalar_one()
        keep_user = session.execute(
            select(AuthUser).where(AuthUser.email == keep_email)
        ).scalar_one_or_none()
        pilot_processes = session.execute(
            select(func.count()).select_from(Process).where(Process.title.like("Proceso Piloto%"))
        ).scalar_one()
    assert pilot_users == 0
    assert keep_user is not None
    assert pilot_processes == 0
