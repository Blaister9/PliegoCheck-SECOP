"""Normalizacion minima y deterministica de texto."""

from collections.abc import Iterable

from pliegocheck_worker.extraction.models import ControlledExtractionError


def normalize_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    lines = [line.rstrip() for line in normalized.split("\n")]
    compact: list[str] = []
    blank_count = 0
    for line in lines:
        if line.strip() == "":
            blank_count += 1
            if blank_count <= 2:
                compact.append("")
            continue
        blank_count = 0
        compact.append(line)
    return "\n".join(compact).strip()


def ensure_character_budget(texts: Iterable[str], max_characters: int) -> int:
    total = 0
    for text in texts:
        total += len(text)
        if total > max_characters:
            raise ControlledExtractionError(
                "EXTRACTION_LIMIT_EXCEEDED",
                "La extraccion excede el limite de caracteres configurado.",
            )
    return total
