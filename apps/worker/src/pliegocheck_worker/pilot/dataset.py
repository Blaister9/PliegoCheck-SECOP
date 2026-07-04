"""Dataset sintetico del piloto. Todo es ficticio y esta marcado como piloto.

La fuente autoritativa del dataset es este modulo. Los archivos JSON en
``pilot/seed/`` son copias legibles para humanos que reflejan estos valores.
"""

from __future__ import annotations

from typing import Any

from pliegocheck_worker.pilot import PILOT_DOMAIN

# --- Usuarios sinteticos -----------------------------------------------------
PILOT_USERS: list[dict[str, Any]] = [
    {
        "key": "admin",
        "email": f"admin@{PILOT_DOMAIN}",
        "display_name": "Piloto Admin Sintetico",
        "roles": ["ADMIN"],
    },
    {
        "key": "analyst",
        "email": f"analyst@{PILOT_DOMAIN}",
        "display_name": "Piloto Analyst Sintetico",
        "roles": ["ANALYST"],
    },
    {
        "key": "reviewer",
        "email": f"reviewer@{PILOT_DOMAIN}",
        "display_name": "Piloto Reviewer Sintetico",
        "roles": ["REVIEWER"],
    },
    {
        "key": "viewer",
        "email": f"viewer@{PILOT_DOMAIN}",
        "display_name": "Piloto Viewer Sintetico",
        "roles": ["VIEWER"],
    },
]

# --- Proceso sintetico -------------------------------------------------------
PILOT_PROCESS = {
    "title": "Proceso Piloto Sintetico 001 - Mesa de ayuda",
    "contracting_entity": "Entidad Demo de Contratacion",
    "secop_reference": "CO1.NTC.PILOTO-SINTETICO-001",
    "description": "Proceso sintetico de piloto. Datos ficticios para demostracion end-to-end.",
    "selection_method": "Licitacion publica",
    "estimated_value": "1500000000",
    "currency": "COP",
    "closing_at": "2026-12-31T23:59:00-05:00",
}

# --- Documentos sinteticos del proceso ---------------------------------------
PILOT_PROCESS_DOCUMENTS: list[dict[str, Any]] = [
    {
        "filename": "pliego-sintetico.txt",
        "content_type": "text/plain",
        "document_type": "TERMS",
        "text": (
            "PLIEGO DE CONDICIONES SINTETICO - PROCESO PILOTO 001\n\n"
            "Objeto: prestacion de servicios de mesa de ayuda (datos ficticios).\n\n"
            "3. REQUISITOS HABILITANTES\n"
            "3.1 Financieros: El proponente debe acreditar un indice de liquidez "
            "minimo de 1.2 y un capital de trabajo minimo de 500000000 COP.\n"
            "3.2 Juridicos: El proponente debe aportar RUP vigente.\n"
            "3.3 Experiencia: El proponente debe acreditar experiencia en contratos "
            "similares de mesa de ayuda.\n"
            "3.4 Tecnicos: El proponente debe contar con certificacion de calidad ISO 9001.\n"
        ),
    },
    {
        "filename": "anexo-financiero-sintetico.csv",
        "content_type": "text/csv",
        "document_type": "FINANCIAL_ANNEX",
        "text": (
            "indicador,valor_minimo,unidad\n"
            "indice_liquidez,1.2,ratio\n"
            "capital_trabajo,500000000,COP\n"
        ),
    },
]

# --- Requisitos normalizados controlados (fixture, sin OpenAI) ---------------
# criticality MEDIUM para incumplimientos no bloqueantes: el piloto debe
# producir PENDIENTE_INFORMACION honesto, no un NO_GO ni un GO forzado.
PILOT_REQUIREMENTS: list[dict[str, Any]] = [
    {
        "key": "fin-liquidez",
        "stable_key": "a1" + "0" * 62,
        "category": "FINANCIAL",
        "criticality": "HIGH",
        "description": "El proponente debe acreditar un indice de liquidez minimo de 1.2.",
        "expected_value": {"value": "1.2", "unit": "ratio", "raw_text": "minimo 1.2"},
    },
    {
        "key": "fin-capital",
        "stable_key": "a2" + "0" * 62,
        "category": "FINANCIAL",
        "criticality": "MEDIUM",
        "description": (
            "El proponente debe acreditar un capital de trabajo minimo de 500000000 COP."
        ),
        "expected_value": {
            "value": "500000000",
            "unit": "COP",
            "raw_text": "minimo 500000000 COP",
        },
    },
    {
        "key": "fin-ambiguo",
        "stable_key": "a3" + "0" * 62,
        "category": "FINANCIAL",
        "criticality": "MEDIUM",
        "description": "El proponente debe demostrar solidez financiera adecuada.",
        "expected_value": {},
    },
    {
        "key": "legal-rup",
        "stable_key": "b1" + "0" * 62,
        "category": "LEGAL",
        "criticality": "HIGH",
        "description": "El proponente debe aportar RUP vigente.",
        "expected_value": {},
    },
    {
        "key": "experiencia",
        "stable_key": "c1" + "0" * 62,
        "category": "EXPERIENCE",
        "criticality": "HIGH",
        "description": "El proponente debe acreditar experiencia en contratos similares.",
        "expected_value": {},
    },
    {
        "key": "tecnico-iso",
        "stable_key": "d1" + "0" * 62,
        "category": "TECHNICAL",
        "criticality": "HIGH",
        "description": "El proponente debe contar con certificacion de calidad ISO 9001.",
        "expected_value": {"value": "ISO 9001"},
    },
]

# --- Empresa sintetica -------------------------------------------------------
PILOT_COMPANY = {
    "legal_name": "Empresa Demo PliegoCheck S.A.S.",
    "tax_id": "900123456",
    "tax_id_type": "NIT",
}

# Dominios especializados que se ejecutan en el piloto.
PILOT_SPECIALIZED_DOMAINS = ["LEGAL", "EXPERIENCE", "TECHNICAL"]

# --- Resultado esperado del dataset (sin IA real) ----------------------------
PILOT_EXPECTED_OUTCOME = {
    "decision_outcome": "PENDIENTE_INFORMACION",
    "financial_complies_min": 1,
    "financial_does_not_comply_min": 1,
    "unknown_min": 1,
    "not_evaluated_expected": False,
    "action_min": 1,
    "report_artifact_count": 9,
    "notes": (
        "Dataset sintetico: liquidez cumple, capital de trabajo no cumple, un requisito "
        "financiero ambiguo produce UNKNOWN y la evidencia SUPPORTED exige revision humana. "
        "El resultado honesto es PENDIENTE_INFORMACION; no se fuerza GO."
    ),
}


def build_snapshot_payload() -> dict[str, Any]:
    """Payload sintetico del snapshot publicado con todos los tipos de registro.

    Los identificadores son placeholders estables; el orquestador los reemplaza
    por UUID reales al sembrar para garantizar unicidad.
    """
    return {
        "financial_periods": [
            {
                "id": "PERIOD-1",
                "period_start": "2025-01-01",
                "period_end": "2025-12-31",
                "currency": "COP",
                "status": "SUPPORTED",
                "source_type": "FINANCIAL_STATEMENT",
                "metrics": [
                    {
                        "id": "METRIC-LIQ",
                        "metric_type": "LIQUIDITY_RATIO",
                        "value": "1.75",
                        "unit": "ratio",
                        "status": "SUPPORTED",
                    },
                    {
                        "id": "METRIC-CA",
                        "metric_type": "CURRENT_ASSETS",
                        "value": "100000000",
                        "unit": "COP",
                        "status": "SUPPORTED",
                    },
                    {
                        "id": "METRIC-CL",
                        "metric_type": "CURRENT_LIABILITIES",
                        "value": "80000000",
                        "unit": "COP",
                        "status": "SUPPORTED",
                    },
                ],
            }
        ],
        "rup_snapshots": [
            {"id": "RUP-1", "status": "SUPPORTED", "valid_until": "2027-06-30"},
        ],
        "legal_registrations": [
            {
                "id": "REG-1",
                "registration_type": "CHAMBER_OF_COMMERCE",
                "status": "SUPPORTED",
                "valid_until": "2027-06-30",
            },
        ],
        "experience_records": [
            {
                "id": "EXP-1",
                "status": "SUPPORTED",
                "execution_status": "COMPLETED",
                "contract_title": "Mesa de ayuda sintetica 2024",
                "activities": ["mesa de ayuda"],
                "unspsc_codes": ["81111800"],
                "total_contract_value": "800000000",
                "company_attributable_value": "800000000",
                "currency": "COP",
            },
        ],
        "certifications": [
            {
                "id": "CERT-1",
                "name": "Certificado ISO 9001 Calidad",
                "status": "SUPPORTED",
                "expires_at": "2027-12-31",
            },
        ],
        "capabilities": [
            {
                "id": "CAP-1",
                "name": "Plataforma de mesa de ayuda",
                "description": "Infraestructura sintetica de soporte",
                "territorial_scope": "Nacional",
                "status": "SUPPORTED",
            },
        ],
        "people": [
            {
                "id": "PERSON-1",
                "full_name": "Persona Sintetica Demo",
                "relationship_type": "EMPLOYEE",
                "status": "SUPPORTED",
            },
        ],
        "unspsc_codes": [{"id": "UNSPSC-1", "code": "81111800", "status": "SUPPORTED"}],
        "evidence_documents": [],
        "evidence_links": [],
    }
