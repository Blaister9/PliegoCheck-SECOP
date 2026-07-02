"""Limites configurables para extraccion documental."""

from dataclasses import dataclass

from pliegocheck_api.config import Settings


@dataclass(frozen=True)
class ExtractionLimits:
    max_seconds: int
    max_characters: int
    max_pages: int
    max_sheets: int
    max_rows_per_sheet: int
    max_zip_entries: int
    max_uncompressed_bytes: int
    max_compression_ratio: int

    @classmethod
    def from_settings(cls, settings: Settings) -> "ExtractionLimits":
        return cls(
            max_seconds=settings.extraction_max_seconds,
            max_characters=settings.extraction_max_characters,
            max_pages=settings.extraction_max_pages,
            max_sheets=settings.extraction_max_sheets,
            max_rows_per_sheet=settings.extraction_max_rows_per_sheet,
            max_zip_entries=settings.extraction_max_zip_entries,
            max_uncompressed_bytes=settings.extraction_max_uncompressed_bytes,
            max_compression_ratio=settings.extraction_max_compression_ratio,
        )
