"""Registro de extractores por extension."""

from pliegocheck_worker.extraction.csv_text import extract_csv, extract_txt
from pliegocheck_worker.extraction.docx import extract_docx
from pliegocheck_worker.extraction.limits import ExtractionLimits
from pliegocheck_worker.extraction.models import ExtractionResultData
from pliegocheck_worker.extraction.pdf import extract_pdf
from pliegocheck_worker.extraction.xlsx import extract_xlsx


def extract_by_extension(
    path: str, extension: str, limits: ExtractionLimits
) -> ExtractionResultData:
    normalized = extension.lower()
    if normalized == ".pdf":
        return extract_pdf(path, limits)
    if normalized == ".docx":
        return extract_docx(path, limits)
    if normalized == ".xlsx":
        return extract_xlsx(path, limits)
    if normalized == ".csv":
        return extract_csv(path, limits)
    if normalized == ".txt":
        return extract_txt(path, limits)
    if normalized in {".png", ".jpg", ".jpeg"}:
        return ExtractionResultData(
            status="NEEDS_OCR",
            detected_format=normalized.removeprefix("."),
            error_code="NEEDS_OCR",
            error_message="El documento es imagen y requiere OCR; OCR no esta habilitado.",
        )
    if normalized in {".doc", ".xls"}:
        return ExtractionResultData(
            status="UNSUPPORTED",
            detected_format=normalized.removeprefix("."),
            error_code="UNSUPPORTED_FORMAT",
            error_message="El formato legacy se conserva, pero no se extrae en esta fase.",
        )
    return ExtractionResultData(
        status="UNSUPPORTED",
        detected_format=normalized.removeprefix(".") or "unknown",
        error_code="UNSUPPORTED_FORMAT",
        error_message="El formato no tiene extractor configurado.",
    )
