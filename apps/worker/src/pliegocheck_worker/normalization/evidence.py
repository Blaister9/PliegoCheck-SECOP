"""Validacion deterministica de evidencia propuesta por el modelo."""

from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import UUID

from pliegocheck_api.normalization import segment_index
from pliegocheck_schemas import RequirementCandidateEvidence, RequirementEvidenceValidationStatus


@dataclass(frozen=True)
class EvidenceValidationResult:
    status: RequirementEvidenceValidationStatus
    message: str
    extraction_id: UUID | None
    segment: dict[str, object] | None


class EvidenceValidator:
    """Valida evidencia contra el snapshot inmutable de la ejecucion."""

    def __init__(self, manifest: dict[str, object]) -> None:
        self._segments = segment_index(manifest)

    def validate(self, evidence: RequirementCandidateEvidence) -> EvidenceValidationResult:
        segment = self._segments.get(evidence.segment_id)
        if segment is None:
            return EvidenceValidationResult(
                status=RequirementEvidenceValidationStatus.OUTSIDE_SNAPSHOT,
                message="El segmento citado no pertenece al snapshot de la ejecucion.",
                extraction_id=None,
                segment=None,
            )
        text = str(segment.get("text", ""))
        quote = evidence.quoted_text.strip()
        if not _contains_quote(text, quote):
            return EvidenceValidationResult(
                status=RequirementEvidenceValidationStatus.QUOTE_NOT_FOUND,
                message="La cita no aparece en el texto del segmento.",
                extraction_id=UUID(str(segment["extraction_id"])),
                segment=segment,
            )
        if evidence.quote_start is not None and evidence.quote_end is not None:
            exact = text[evidence.quote_start : evidence.quote_end]
            if exact != quote:
                return EvidenceValidationResult(
                    status=RequirementEvidenceValidationStatus.QUOTE_NOT_FOUND,
                    message="Los offsets no corresponden exactamente a la cita.",
                    extraction_id=UUID(str(segment["extraction_id"])),
                    segment=segment,
                )
        if not _location_matches(segment, evidence):
            return EvidenceValidationResult(
                status=RequirementEvidenceValidationStatus.LOCATION_MISMATCH,
                message="La ubicacion declarada no corresponde al segmento.",
                extraction_id=UUID(str(segment["extraction_id"])),
                segment=segment,
            )
        return EvidenceValidationResult(
            status=RequirementEvidenceValidationStatus.VALID,
            message="Evidencia valida.",
            extraction_id=UUID(str(segment["extraction_id"])),
            segment=segment,
        )


def _contains_quote(text: str, quote: str) -> bool:
    if quote in text:
        return True
    normalized_text = _normalize_space(text)
    normalized_quote = _normalize_space(quote)
    return normalized_quote in normalized_text


def _normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _location_matches(segment: dict[str, object], evidence: RequirementCandidateEvidence) -> bool:
    location = evidence.source_location
    checks = {
        "page_number": location.page_number,
        "paragraph_index": location.paragraph_index,
        "table_index": location.table_index,
        "sheet_name": location.sheet_name,
        "row_start": location.row_start,
        "row_end": location.row_end,
        "line_start": location.line_start,
        "line_end": location.line_end,
    }
    for key, expected in checks.items():
        if expected is None:
            continue
        if segment.get(key) != expected:
            return False
    return True
