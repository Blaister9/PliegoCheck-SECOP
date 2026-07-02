"""Controles de seguridad para contenedores Office."""

from pathlib import PurePosixPath
from zipfile import BadZipFile, ZipFile

from pliegocheck_worker.extraction.limits import ExtractionLimits
from pliegocheck_worker.extraction.models import ControlledExtractionError


def inspect_zip_container(path: str, limits: ExtractionLimits) -> bool:
    """Valida metadata ZIP sin extraerlo. Retorna si contiene macros."""

    try:
        with ZipFile(path) as archive:
            infos = archive.infolist()
    except BadZipFile as exc:
        raise ControlledExtractionError(
            "EXTRACTION_FAILED",
            "El contenedor Office no es un ZIP valido.",
        ) from exc

    if len(infos) > limits.max_zip_entries:
        raise ControlledExtractionError(
            "EXTRACTION_LIMIT_EXCEEDED",
            "El contenedor excede el limite de entradas ZIP.",
        )

    compressed = 0
    uncompressed = 0
    contains_macros = False
    for info in infos:
        name = info.filename.replace("\\", "/")
        parts = PurePosixPath(name).parts
        if PurePosixPath(name).is_absolute() or any(part in {"", ".", ".."} for part in parts):
            raise ControlledExtractionError(
                "EXTRACTION_FAILED",
                "El contenedor contiene rutas peligrosas.",
            )
        compressed += max(info.compress_size, 1)
        uncompressed += info.file_size
        if name.endswith("vbaProject.bin"):
            contains_macros = True

    if uncompressed > limits.max_uncompressed_bytes:
        raise ControlledExtractionError(
            "EXTRACTION_LIMIT_EXCEEDED",
            "El contenedor excede el limite descomprimido configurado.",
        )
    if compressed > 0 and uncompressed / compressed > limits.max_compression_ratio:
        raise ControlledExtractionError(
            "EXTRACTION_LIMIT_EXCEEDED",
            "El contenedor excede el ratio de compresion permitido.",
        )
    if contains_macros:
        raise ControlledExtractionError(
            "UNSUPPORTED_FORMAT",
            "Los documentos Office con macros no son compatibles en esta fase.",
            status="UNSUPPORTED",
        )
    return contains_macros
