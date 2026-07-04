# mypy: ignore-errors
"""Evals sinteticos de evaluadores especializados.

No usan IA ni base de datos: prueban reglas puras contra snapshots sinteticos.
"""

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from pliegocheck_api.decision.coverage import DecisionCoverageAnalyzer
from pliegocheck_api.decision.engine import DecisionContext, DeterministicDecisionEngine
from pliegocheck_api.decision.findings import DecisionAdapterRegistry
from pliegocheck_api.decision.policy import load_active_policy
from pliegocheck_api.specialized_evaluation import (
    evaluate_specialized_requirement,
    map_specialized_requirement,
)
from pliegocheck_schemas import (
    DecisionFindingOutcome,
    DecisionFindingSourceType,
    DecisionOutcome,
    RequirementCategory,
)


class Req:
    def __init__(self, category: str, description: str, expected_value: dict | None = None) -> None:
        self.id = uuid4()
        self.process_id = uuid4()
        self.normalization_run_id = uuid4()
        self.stable_key = "a" * 64
        self.category = category
        self.description = description
        self.condition_text = None
        self.expected_value = expected_value or {}
        self.scope = "COMPANY"
        self.modality = "MANDATORY"
        self.criticality = "BLOCKING"
        self.criticality_basis = "INFERRED"
        self.subsanability = "UNKNOWN"
        self.subsanability_basis = "UNKNOWN"


def decide(requirement: Req, domain: str, snapshot: dict) -> str:
    rule = map_specialized_requirement(requirement, domain)
    result = evaluate_specialized_requirement(
        requirement=requirement,
        rule=rule,
        snapshot_payload=snapshot,
        effective_at=datetime(2026, 7, 4, tzinfo=UTC),
    )
    return result["status"]


def supported_link(subject_id: str) -> dict:
    return {
        "id": str(uuid4()),
        "subject_id": subject_id,
        "document_id": str(uuid4()),
        "evidence_role": "PRIMARY",
        "review_status": "SUPPORTED",
        "validation_status": "VALID",
        "quoted_text": "soporte sintetico",
    }


def test_01_rup_exists_and_valid() -> None:
    rup_id = str(uuid4())
    snapshot = {
        "rup_snapshots": [{"id": rup_id, "status": "SUPPORTED", "valid_until": "2027-01-01"}],
        "evidence_links": [supported_link(rup_id)],
    }
    req = Req(RequirementCategory.LEGAL.value, "Debe aportar RUP vigente")
    assert decide(req, "LEGAL", snapshot) == "COMPLIES"


def test_02_rup_missing_is_unknown() -> None:
    req = Req(RequirementCategory.LEGAL.value, "Debe aportar RUP vigente")
    assert decide(req, "LEGAL", {"rup_snapshots": [], "evidence_links": []}) == "UNKNOWN"


def test_03_expired_registration_does_not_comply() -> None:
    reg_id = str(uuid4())
    snapshot = {
        "legal_registrations": [
            {
                "id": reg_id,
                "registration_type": "CHAMBER_OF_COMMERCE",
                "status": "SUPPORTED",
                "expires_at": "2025-01-01",
            }
        ],
        "evidence_links": [supported_link(reg_id)],
    }
    req = Req(RequirementCategory.LEGAL.value, "Camara de comercio vigente")
    assert decide(req, "LEGAL", snapshot) == "DOES_NOT_COMPLY"


def test_04_required_document_exists() -> None:
    doc_id = str(uuid4())
    snapshot = {
        "evidence_documents": [
            {"id": doc_id, "title": "Documento habilitante", "status": "SUPPORTED"}
        ],
        "evidence_links": [supported_link(doc_id)],
    }
    req = Req(RequirementCategory.DOCUMENTARY.value, "Debe aportar documento habilitante")
    assert decide(req, "LEGAL", snapshot) == "COMPLIES"


def test_05_required_document_missing() -> None:
    req = Req(RequirementCategory.DOCUMENTARY.value, "Debe aportar documento habilitante")
    assert decide(req, "LEGAL", {"evidence_documents": [], "evidence_links": []}) == "UNKNOWN"


def test_06_ineligibility_without_data_is_unknown() -> None:
    req = Req(RequirementCategory.RISK_AND_INELIGIBILITY.value, "Declaracion de no inhabilidad")
    assert decide(req, "LEGAL", {"evidence_documents": [], "evidence_links": []}) == "UNKNOWN"


def test_07_guarantee_without_evaluable_value_is_unknown() -> None:
    req = Req(RequirementCategory.GUARANTEE.value, "Garantia con valor asegurable")
    assert decide(req, "LEGAL", {"evidence_documents": [], "evidence_links": []}) == "UNKNOWN"


def test_08_experience_value_complies() -> None:
    exp_id = str(uuid4())
    snapshot = {
        "experience_records": [
            {
                "id": exp_id,
                "status": "SUPPORTED",
                "execution_status": "COMPLETED",
                "total_contract_value": "200",
                "currency": "COP",
            }
        ],
        "evidence_links": [supported_link(exp_id)],
    }
    req = Req(RequirementCategory.EXPERIENCE.value, "Experiencia por valor minimo 100 COP")
    assert decide(req, "EXPERIENCE", snapshot) == "COMPLIES"


def test_09_experience_value_not_comply() -> None:
    exp_id = str(uuid4())
    snapshot = {
        "experience_records": [
            {
                "id": exp_id,
                "status": "SUPPORTED",
                "execution_status": "COMPLETED",
                "total_contract_value": "50",
                "currency": "COP",
            }
        ],
        "evidence_links": [supported_link(exp_id)],
    }
    req = Req(RequirementCategory.EXPERIENCE.value, "Experiencia por valor minimo 100 COP")
    assert decide(req, "EXPERIENCE", snapshot) == "DOES_NOT_COMPLY"


def test_10_experience_count_complies() -> None:
    snapshot = {"experience_records": [], "evidence_links": []}
    for _ in range(2):
        exp_id = str(uuid4())
        snapshot["experience_records"].append(
            {"id": exp_id, "status": "SUPPORTED", "execution_status": "COMPLETED"}
        )
        snapshot["evidence_links"].append(supported_link(exp_id))
    req = Req(RequirementCategory.EXPERIENCE.value, "Al menos 2 contratos ejecutados")
    assert decide(req, "EXPERIENCE", snapshot) == "COMPLIES"


def test_11_activity_not_comparable_unknown() -> None:
    exp_id = str(uuid4())
    snapshot = {
        "experience_records": [
            {
                "id": exp_id,
                "status": "SUPPORTED",
                "execution_status": "COMPLETED",
                "activities": ["redes"],
            }
        ],
        "evidence_links": [supported_link(exp_id)],
    }
    req = Req(
        RequirementCategory.EXPERIENCE.value, "Actividad mesa de ayuda", {"value": "mesa de ayuda"}
    )
    assert decide(req, "EXPERIENCE", snapshot) == "UNKNOWN"


def test_12_unspsc_exact_match_complies() -> None:
    exp_id = str(uuid4())
    snapshot = {
        "experience_records": [
            {
                "id": exp_id,
                "status": "SUPPORTED",
                "execution_status": "COMPLETED",
                "unspsc_codes": ["81111800"],
            }
        ],
        "evidence_links": [supported_link(exp_id)],
    }
    req = Req(RequirementCategory.EXPERIENCE.value, "UNSPSC 81111800", {"value": "81111800"})
    assert decide(req, "EXPERIENCE", snapshot) == "COMPLIES"


def test_13_consortium_without_percentage_unknown() -> None:
    exp_id = str(uuid4())
    snapshot = {
        "experience_records": [
            {
                "id": exp_id,
                "status": "SUPPORTED",
                "execution_status": "COMPLETED",
                "total_contract_value": "200",
                "currency": "COP",
                "consortium_name": "UT Test",
            }
        ],
        "evidence_links": [supported_link(exp_id)],
    }
    req = Req(RequirementCategory.EXPERIENCE.value, "Experiencia por valor minimo 100 COP")
    assert decide(req, "EXPERIENCE", snapshot) == "UNKNOWN"


def test_14_in_progress_contract_does_not_count_as_completed() -> None:
    exp_id = str(uuid4())
    snapshot = {
        "experience_records": [
            {"id": exp_id, "status": "SUPPORTED", "execution_status": "IN_PROGRESS"}
        ],
        "evidence_links": [supported_link(exp_id)],
    }
    req = Req(RequirementCategory.EXPERIENCE.value, "Experiencia ejecutada")
    assert decide(req, "EXPERIENCE", snapshot) == "UNKNOWN"


def test_15_currency_incompatible_unknown() -> None:
    exp_id = str(uuid4())
    snapshot = {
        "experience_records": [
            {
                "id": exp_id,
                "status": "SUPPORTED",
                "execution_status": "COMPLETED",
                "total_contract_value": "200",
                "currency": "USD",
            }
        ],
        "evidence_links": [supported_link(exp_id)],
    }
    req = Req(RequirementCategory.EXPERIENCE.value, "Experiencia por valor minimo 100 COP")
    assert decide(req, "EXPERIENCE", snapshot) == "UNKNOWN"


def test_16_technical_certification_valid_complies() -> None:
    cert_id = str(uuid4())
    snapshot = {
        "certifications": [
            {"id": cert_id, "status": "SUPPORTED", "name": "ISO 9001", "expires_at": "2027-01-01"}
        ],
        "evidence_links": [supported_link(cert_id)],
    }
    req = Req(
        RequirementCategory.TECHNICAL.value, "Certificacion ISO 9001 vigente", {"value": "ISO 9001"}
    )
    assert decide(req, "TECHNICAL", snapshot) == "COMPLIES"


def test_17_technical_certification_expired_not_comply() -> None:
    cert_id = str(uuid4())
    snapshot = {
        "certifications": [
            {"id": cert_id, "status": "SUPPORTED", "name": "ISO 9001", "expires_at": "2025-01-01"}
        ],
        "evidence_links": [supported_link(cert_id)],
    }
    req = Req(
        RequirementCategory.TECHNICAL.value, "Certificacion ISO 9001 vigente", {"value": "ISO 9001"}
    )
    assert decide(req, "TECHNICAL", snapshot) == "DOES_NOT_COMPLY"


def test_18_declared_capability_without_evidence_unknown() -> None:
    cap_id = str(uuid4())
    snapshot = {
        "capabilities": [{"id": cap_id, "status": "DECLARED", "name": "Mesa de ayuda"}],
        "evidence_links": [],
    }
    req = Req(
        RequirementCategory.TECHNICAL.value, "Capacidad mesa de ayuda", {"value": "Mesa de ayuda"}
    )
    assert decide(req, "TECHNICAL", snapshot) == "UNKNOWN"


def test_19_person_role_supported_complies() -> None:
    person_id = str(uuid4())
    snapshot = {
        "people": [{"id": person_id, "status": "SUPPORTED", "full_name": "Ingeniera residente"}],
        "evidence_links": [supported_link(person_id)],
    }
    req = Req(
        RequirementCategory.WORKFORCE.value,
        "Profesional Ingeniera residente",
        {"value": "Ingeniera"},
    )
    assert decide(req, "TECHNICAL", snapshot) == "COMPLIES"


def test_20_person_missing_unknown() -> None:
    req = Req(RequirementCategory.WORKFORCE.value, "Profesional certificado")
    assert decide(req, "TECHNICAL", {"people": [], "evidence_links": []}) == "UNKNOWN"


def test_21_role_missing_unknown() -> None:
    person_id = str(uuid4())
    snapshot = {
        "people": [{"id": person_id, "status": "SUPPORTED", "full_name": "Auxiliar"}],
        "evidence_links": [supported_link(person_id)],
    }
    req = Req(RequirementCategory.WORKFORCE.value, "Director de proyecto", {"value": "Director"})
    assert decide(req, "TECHNICAL", snapshot) == "UNKNOWN"


def test_22_coverage_exact_complies() -> None:
    cap_id = str(uuid4())
    snapshot = {
        "capabilities": [{"id": cap_id, "status": "SUPPORTED", "territorial_scope": "Bogota"}],
        "evidence_links": [supported_link(cap_id)],
    }
    req = Req(
        RequirementCategory.OPERATIONAL.value, "Cobertura territorial Bogota", {"value": "Bogota"}
    )
    assert decide(req, "TECHNICAL", snapshot) == "COMPLIES"


def test_23_technology_not_equivalent_unknown() -> None:
    cap_id = str(uuid4())
    snapshot = {
        "capabilities": [{"id": cap_id, "status": "SUPPORTED", "name": "Linux"}],
        "evidence_links": [supported_link(cap_id)],
    }
    req = Req(
        RequirementCategory.TECHNICAL.value,
        "Tecnologia Windows Server",
        {"value": "Windows Server"},
    )
    assert decide(req, "TECHNICAL", snapshot) == "UNKNOWN"


def test_24_no_ai_dependencies() -> None:
    import inspect

    import pliegocheck_api.specialized_evaluation as module

    source = inspect.getsource(module).lower()
    for forbidden in ("openai", "anthropic", "embedding", "llm", "prompt("):
        assert forbidden not in source


def test_25_legal_and_financial_results_cover_decision_findings() -> None:
    legal_req = Req(RequirementCategory.LEGAL.value, "Debe aportar RUP vigente")
    financial_req = Req(RequirementCategory.FINANCIAL.value, "Liquidez minima 1")
    registry = DecisionAdapterRegistry()
    findings = registry.collect_all_findings(
        requirements=[legal_req, financial_req],
        context={
            "financial_evaluation_run_id": uuid4(),
            "financial_results_by_requirement": {
                financial_req.id: financial_result(financial_req.id, "COMPLIES")
            },
            "specialized_results_by_requirement": {
                legal_req.id: specialized_result(legal_req.id, "LEGAL", "COMPLIES")
            },
        },
    )
    assert {finding.outcome for finding in findings} == {DecisionFindingOutcome.COMPLIES}
    assert all(
        finding.source_type != DecisionFindingSourceType.MISSING_ADAPTER for finding in findings
    )


def test_26_experience_noncompliance_reaches_decision_finding() -> None:
    req = Req(RequirementCategory.EXPERIENCE.value, "Experiencia por valor minimo 100 COP")
    findings = DecisionAdapterRegistry().collect_all_findings(
        requirements=[req],
        context={
            "financial_evaluation_run_id": uuid4(),
            "financial_results_by_requirement": {},
            "specialized_results_by_requirement": {
                req.id: specialized_result(req.id, "EXPERIENCE", "DOES_NOT_COMPLY")
            },
        },
    )
    assert len(findings) == 1
    assert findings[0].outcome == DecisionFindingOutcome.DOES_NOT_COMPLY


def test_27_technical_unknown_blocks_go_in_decision_engine() -> None:
    req = Req(RequirementCategory.TECHNICAL.value, "Tecnologia Windows Server")
    registry = DecisionAdapterRegistry()
    findings = registry.collect_all_findings(
        requirements=[req],
        context={
            "financial_evaluation_run_id": uuid4(),
            "financial_results_by_requirement": {},
            "specialized_results_by_requirement": {
                req.id: specialized_result(req.id, "TECHNICAL", "UNKNOWN")
            },
        },
    )
    coverage = DecisionCoverageAnalyzer(registry.available_domains()).analyze(findings)
    policy, _, _ = load_active_policy()
    output = DeterministicDecisionEngine().decide(
        DecisionContext(
            policy=policy,
            findings=findings,
            coverage=coverage,
            effective_at=datetime(2026, 7, 4, tzinfo=UTC),
        )
    )
    assert output.engine_outcome == DecisionOutcome.PENDIENTE_INFORMACION
    assert output.engine_outcome != DecisionOutcome.GO


def specialized_result(requirement_id, domain: str, status: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        run_id=uuid4(),
        requirement_id=requirement_id,
        domain=domain,
        status=status,
        reviewed_status=None,
        review_status="PENDING",
        requires_human_review=False,
        evidence_refs={"links": []},
        explanation_parameters={"usability": "VERIFIED"},
    )


def financial_result(requirement_id, status: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        requirement_id=requirement_id,
        status=status,
        reviewed_status=None,
        review_status="PENDING",
        requires_human_review=False,
        evidence_refs={"links": []},
        explanation_parameters={"usability": "VERIFIED"},
    )
