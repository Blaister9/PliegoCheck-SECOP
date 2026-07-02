"""Extractores TXT y CSV con deteccion conservadora de codificacion."""

import csv
from pathlib import Path

from charset_normalizer import from_bytes

from pliegocheck_worker.extraction.limits import ExtractionLimits
from pliegocheck_worker.extraction.models import (
    ExtractionResultData,
    ExtractionWarningData,
    SegmentData,
)
from pliegocheck_worker.extraction.text import ensure_character_budget, normalize_text

LINES_PER_SEGMENT = 40
ROWS_PER_SEGMENT = 40


def _decode(path: str) -> tuple[str, list[ExtractionWarningData]]:
    raw = Path(path).read_bytes()
    if not raw:
        return "", []
    match = from_bytes(raw).best()
    warnings: list[ExtractionWarningData] = []
    if match is None:
        warnings.append(
            ExtractionWarningData(
                code="TEXT_ENCODING_FALLBACK",
                message="No se pudo detectar codificacion; se usa utf-8 con reemplazo.",
            )
        )
        return raw.decode("utf-8", errors="replace"), warnings
    if match.percent_coherence < 40:
        warnings.append(
            ExtractionWarningData(
                code="TEXT_ENCODING_LOW_CONFIDENCE",
                message="La confianza de deteccion de codificacion es baja.",
                location={"encoding": match.encoding},
            )
        )
    return str(match), warnings


def extract_txt(path: str, limits: ExtractionLimits) -> ExtractionResultData:
    text, warnings = _decode(path)
    lines = normalize_text(text).split("\n") if text else []
    segments: list[SegmentData] = []
    for index in range(0, len(lines), LINES_PER_SEGMENT):
        chunk = normalize_text("\n".join(lines[index : index + LINES_PER_SEGMENT]))
        if chunk:
            line_start = index + 1
            line_end = min(index + LINES_PER_SEGMENT, len(lines))
            segments.append(
                SegmentData(
                    sequence=len(segments) + 1,
                    segment_type="TEXT_LINES",
                    text=chunk,
                    line_start=line_start,
                    line_end=line_end,
                    source_location={"line_start": line_start, "line_end": line_end},
                )
            )
    character_count = ensure_character_budget(
        (segment.text for segment in segments),
        limits.max_characters,
    )
    return ExtractionResultData(
        status="COMPLETED_WITH_WARNINGS" if warnings else "COMPLETED",
        detected_format="txt",
        segments=segments,
        warnings=warnings,
        character_count=character_count,
    )


def extract_csv(path: str, limits: ExtractionLimits) -> ExtractionResultData:
    text, warnings = _decode(path)
    rows = list(csv.reader(text.splitlines()))
    segments: list[SegmentData] = []
    for index in range(0, min(len(rows), limits.max_rows_per_sheet), ROWS_PER_SEGMENT):
        block = rows[index : index + ROWS_PER_SEGMENT]
        rendered_rows = [
            "\t".join(cell.replace("\t", " ") for cell in row).strip() for row in block
        ]
        chunk = normalize_text("\n".join(row for row in rendered_rows if row))
        if chunk:
            row_start = index + 1
            row_end = min(index + ROWS_PER_SEGMENT, len(rows), limits.max_rows_per_sheet)
            segments.append(
                SegmentData(
                    sequence=len(segments) + 1,
                    segment_type="SHEET_ROW",
                    text=chunk,
                    sheet_name="csv",
                    row_start=row_start,
                    row_end=row_end,
                    source_location={
                        "sheet_name": "csv",
                        "row_start": row_start,
                        "row_end": row_end,
                    },
                )
            )
    if len(rows) > limits.max_rows_per_sheet:
        warnings.append(
            ExtractionWarningData(
                code="CSV_ROW_LIMIT_REACHED",
                message="El CSV excede el limite de filas configurado.",
                location={"row": limits.max_rows_per_sheet + 1},
            )
        )
    character_count = ensure_character_budget(
        (segment.text for segment in segments),
        limits.max_characters,
    )
    return ExtractionResultData(
        status="COMPLETED_WITH_WARNINGS" if warnings else "COMPLETED",
        detected_format="csv",
        segments=segments,
        warnings=warnings,
        sheet_count=1,
        character_count=character_count,
    )
