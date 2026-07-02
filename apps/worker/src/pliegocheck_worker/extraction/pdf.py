"""Extractor PDF con PyMuPDF, sin OCR ni renderizado."""

import fitz

from pliegocheck_worker.extraction.limits import ExtractionLimits
from pliegocheck_worker.extraction.models import (
    ControlledExtractionError,
    ExtractionResultData,
    ExtractionWarningData,
    SegmentData,
)
from pliegocheck_worker.extraction.text import ensure_character_budget, normalize_text


def extract_pdf(path: str, limits: ExtractionLimits) -> ExtractionResultData:
    try:
        document = fitz.open(path)
    except Exception as exc:  # biblioteca externa: se sanitiza
        raise ControlledExtractionError(
            "EXTRACTION_FAILED", "No fue posible abrir el PDF."
        ) from exc

    try:
        if document.is_encrypted:
            return ExtractionResultData(
                status="ENCRYPTED",
                detected_format="pdf",
                page_count=document.page_count,
                error_code="ENCRYPTED_DOCUMENT",
                error_message="El PDF esta cifrado y no puede extraerse sin contrasena.",
            )
        if document.page_count > limits.max_pages:
            raise ControlledExtractionError(
                "EXTRACTION_LIMIT_EXCEEDED",
                "El PDF excede el limite de paginas configurado.",
            )

        segments: list[SegmentData] = []
        warnings: list[ExtractionWarningData] = []
        for index in range(document.page_count):
            page_number = index + 1
            try:
                text = normalize_text(document.load_page(index).get_text("text"))
            except Exception:
                warnings.append(
                    ExtractionWarningData(
                        code="PDF_PAGE_EXTRACTION_FAILED",
                        message="No fue posible extraer texto de la pagina.",
                        location={"page_number": page_number},
                    )
                )
                continue
            if text:
                segments.append(
                    SegmentData(
                        sequence=len(segments) + 1,
                        segment_type="PAGE_TEXT",
                        text=text,
                        page_number=page_number,
                        source_location={"page_number": page_number},
                    )
                )
            else:
                warnings.append(
                    ExtractionWarningData(
                        code="PDF_PAGE_WITHOUT_TEXT",
                        message="La pagina no contiene texto digital extraible.",
                        location={"page_number": page_number},
                    )
                )
        character_count = ensure_character_budget(
            (segment.text for segment in segments),
            limits.max_characters,
        )
        if not segments or character_count < 10:
            return ExtractionResultData(
                status="NEEDS_OCR",
                detected_format="pdf",
                segments=[],
                warnings=warnings,
                page_count=document.page_count,
                character_count=character_count,
                error_code="NEEDS_OCR",
                error_message="El PDF no contiene texto digital suficiente.",
            )
        status = "COMPLETED_WITH_WARNINGS" if warnings else "COMPLETED"
        return ExtractionResultData(
            status=status,
            detected_format="pdf",
            segments=segments,
            warnings=warnings,
            page_count=document.page_count,
            character_count=character_count,
        )
    finally:
        document.close()
