"""Plantillas versionadas para explicaciones estructuradas."""

TEMPLATES = {
    "TEXT_STRONG_MATCH": (
        "Coincidencia textual fuerte entre el objeto del proceso y la actividad empresarial."
    ),
    "TEXT_PARTIAL_MATCH": "Coincidencia textual parcial; requiere revisar el alcance contractual.",
    "TEXT_MISMATCH": (
        "El objeto del proceso no coincide con las actividades documentadas del snapshot."
    ),
    "TEXT_INFORMATION_MISSING": "No hay texto suficiente para evaluar relevancia.",
    "UNSPSC_PRODUCT_MATCH": "Coincidencia fuerte en producto UNSPSC {code}.",
    "UNSPSC_CLASS_MATCH": "Coincidencia de clase UNSPSC {code}.",
    "UNSPSC_FAMILY_MATCH": "Coincidencia parcial de familia UNSPSC {code}.",
    "UNSPSC_SEGMENT_MATCH": "Coincidencia debil de segmento UNSPSC {code}.",
    "UNSPSC_UNKNOWN": "No hay codigos UNSPSC suficientes para comparar.",
    "EXPERIENCE_EVIDENCE_AVAILABLE": "El snapshot contiene experiencia estructurada relacionada.",
    "EXPERIENCE_PARTIAL": "La experiencia relacionada es parcial o de menor cuantia.",
    "EXPERIENCE_NOT_FOUND": "No se encontro experiencia relacionada en el snapshot.",
    "EXPERIENCE_UNKNOWN": "No hay experiencia estructurada suficiente.",
    "PRELIMINARY_VALUE_FIT": "La cuantia esta dentro de la capacidad o experiencia documentada.",
    "PRELIMINARY_VALUE_MISMATCH": "La cuantia supera la capacidad o experiencia documentada.",
    "FINANCIAL_DATA_MISSING": "Faltan datos financieros para una comparacion preliminar.",
    "DEEP_FINANCIAL_REVIEW_REQUIRED": (
        "La comparacion financiera definitiva requiere requisitos normalizados."
    ),
    "TECHNICAL_DATA_AVAILABLE": "El snapshot contiene capacidades tecnicas relacionadas.",
    "TECHNICAL_DATA_MISSING": "No se encontraron capacidades tecnicas estructuradas.",
    "LEGAL_DATA_AVAILABLE": "El snapshot contiene registros juridicos vigentes o soportados.",
    "LEGAL_DATA_MISSING": "No se encontraron registros juridicos suficientes.",
    "GEOGRAPHIC_MATCH": "La ubicacion coincide con la cobertura empresarial documentada.",
    "GEOGRAPHIC_GAP": "La ubicacion no coincide con la cobertura documentada.",
    "GEOGRAPHIC_UNKNOWN": "No hay informacion geografica suficiente.",
    "DEADLINE_CLOSED": "El proceso esta cerrado o su fecha limite ya vencio.",
    "DEADLINE_CRITICAL": "Quedan menos de 48 horas para el cierre.",
    "DEADLINE_URGENT": "Quedan entre 2 y 5 dias para el cierre.",
    "DEADLINE_NORMAL": "Quedan entre 6 y 20 dias para el cierre.",
    "DEADLINE_LONG": "El cierre esta a mas de 20 dias.",
    "DEADLINE_UNKNOWN": "La fuente no ofrece una fecha de cierre confiable.",
    "DOCUMENTS_AVAILABLE": "Existen documentos vinculados o inventariados.",
    "DOCUMENTS_UNAVAILABLE": "No hay documentos suficientes para analisis profundo.",
    "INFORMATION_COMPLETE": "La metadata minima esta disponible.",
    "INFORMATION_PARTIAL": "La metadata presenta campos faltantes.",
    "INFORMATION_INSUFFICIENT": "La metadata critica es insuficiente.",
    "NO_PARTNER_NEED_IDENTIFIED": "No se identifico una brecha asociable explicita.",
    "POTENTIAL_PARTNER_NEED": (
        "Se identifico una brecha potencialmente cubrible por un aliado, sujeta al pliego."
    ),
}


def explain(reason_code: str, parameters: dict[str, object] | None = None) -> str:
    template = TEMPLATES.get(reason_code, reason_code.replace("_", " ").capitalize() + ".")
    return template.format(**(parameters or {}))
