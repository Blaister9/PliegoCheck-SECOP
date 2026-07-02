"""Validacion segura de documentos originales."""

from pathlib import Path
from zipfile import BadZipFile, ZipFile

from pliegocheck_schemas import UploadErrorCode

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".csv",
    ".txt",
    ".png",
    ".jpg",
    ".jpeg",
}
DANGEROUS_EXTENSIONS = {
    ".bat",
    ".cmd",
    ".com",
    ".dll",
    ".exe",
    ".js",
    ".jse",
    ".msi",
    ".ps1",
    ".scr",
    ".sh",
    ".vbs",
    ".wsf",
}
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}
ALLOWED_DECLARED_TYPES = {
    ".pdf": {"application/pdf", "application/octet-stream"},
    ".doc": {"application/msword", "application/octet-stream"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
        "application/octet-stream",
    },
    ".xls": {"application/vnd.ms-excel", "application/octet-stream"},
    ".xlsx": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/zip",
        "application/octet-stream",
    },
    ".csv": {"text/csv", "text/plain", "application/vnd.ms-excel", "application/octet-stream"},
    ".txt": {"text/plain", "application/octet-stream"},
    ".png": {"image/png", "application/octet-stream"},
    ".jpg": {"image/jpeg", "application/octet-stream"},
    ".jpeg": {"image/jpeg", "application/octet-stream"},
}


class FileValidationError(Exception):
    """Error individual de archivo en una carga multipart."""

    def __init__(
        self,
        code: UploadErrorCode,
        message: str,
        *,
        details: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


def validate_original_filename(filename: str | None) -> tuple[str, str]:
    """Valida el nombre original y retorna ``(filename, extension)``."""

    if filename is None or filename.strip() == "":
        raise FileValidationError(
            UploadErrorCode.FILE_TYPE_NOT_ALLOWED,
            "El archivo debe tener un nombre original.",
        )
    original = filename.strip()
    if len(original) > 255:
        raise FileValidationError(
            UploadErrorCode.FILE_TYPE_NOT_ALLOWED,
            "El nombre del archivo es demasiado largo.",
        )
    if any(separator in original for separator in ("/", "\\")) or ":" in original:
        raise FileValidationError(
            UploadErrorCode.FILE_TYPE_NOT_ALLOWED,
            "El nombre del archivo no puede contener rutas.",
        )
    if any(ord(char) < 32 for char in original):
        raise FileValidationError(
            UploadErrorCode.FILE_TYPE_NOT_ALLOWED,
            "El nombre del archivo contiene caracteres de control.",
        )
    path = Path(original)
    if path.name != original or path.is_absolute():
        raise FileValidationError(
            UploadErrorCode.FILE_TYPE_NOT_ALLOWED,
            "El nombre del archivo no puede ser una ruta.",
        )
    stem_upper = path.stem.upper()
    if stem_upper in WINDOWS_RESERVED_NAMES:
        raise FileValidationError(
            UploadErrorCode.FILE_TYPE_NOT_ALLOWED,
            "El nombre del archivo esta reservado por el sistema operativo.",
        )
    extension = path.suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise FileValidationError(
            UploadErrorCode.FILE_TYPE_NOT_ALLOWED,
            "El formato del archivo no esta permitido.",
            details={"extension": extension or "sin_extension"},
        )
    previous_suffixes = [suffix.lower() for suffix in path.suffixes[:-1]]
    if any(suffix in DANGEROUS_EXTENSIONS for suffix in previous_suffixes):
        raise FileValidationError(
            UploadErrorCode.FILE_CONTENT_MISMATCH,
            "El nombre del archivo contiene una doble extension peligrosa.",
        )
    return original, extension


def validate_declared_content_type(extension: str, content_type: str | None) -> None:
    if content_type is None or content_type.strip() == "":
        return
    normalized = content_type.split(";", maxsplit=1)[0].strip().lower()
    if normalized not in ALLOWED_DECLARED_TYPES[extension]:
        raise FileValidationError(
            UploadErrorCode.FILE_CONTENT_MISMATCH,
            "El Content-Type declarado no coincide con la extension permitida.",
            details={"content_type": normalized, "extension": extension},
        )


def detect_content_type(path: Path, extension: str) -> str:
    with path.open("rb") as fh:
        header = fh.read(8192)

    if extension == ".pdf":
        _require(header.startswith(b"%PDF-"), "El archivo no tiene firma PDF valida.")
        return "application/pdf"
    if extension == ".png":
        _require(header.startswith(b"\x89PNG\r\n\x1a\n"), "El archivo no tiene firma PNG valida.")
        return "image/png"
    if extension in {".jpg", ".jpeg"}:
        _require(header.startswith(b"\xff\xd8\xff"), "El archivo no tiene firma JPEG valida.")
        return "image/jpeg"
    if extension == ".doc":
        _require(_is_cfb(header), "El archivo no tiene firma DOC valida.")
        return "application/msword"
    if extension == ".xls":
        _require(_is_cfb(header), "El archivo no tiene firma XLS valida.")
        return "application/vnd.ms-excel"
    if extension == ".docx":
        _require_office_zip(path, required_prefix="word/")
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if extension == ".xlsx":
        _require_office_zip(path, required_prefix="xl/")
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if extension in {".csv", ".txt"}:
        _require_text_sample(header)
        return "text/csv" if extension == ".csv" else "text/plain"

    raise FileValidationError(
        UploadErrorCode.FILE_TYPE_NOT_ALLOWED,
        "El formato del archivo no esta permitido.",
    )


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise FileValidationError(UploadErrorCode.FILE_CONTENT_MISMATCH, message)


def _is_cfb(header: bytes) -> bool:
    return header.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")


def _require_text_sample(sample: bytes) -> None:
    if b"\x00" in sample:
        raise FileValidationError(
            UploadErrorCode.FILE_CONTENT_MISMATCH,
            "El archivo de texto contiene bytes nulos.",
        )
    for encoding in ("utf-8", "latin-1"):
        try:
            sample.decode(encoding)
            return
        except UnicodeDecodeError:
            continue
    raise FileValidationError(
        UploadErrorCode.FILE_CONTENT_MISMATCH,
        "El archivo de texto no pudo decodificarse.",
    )


def _require_office_zip(path: Path, *, required_prefix: str) -> None:
    try:
        with ZipFile(path) as archive:
            names = set(archive.namelist())
    except BadZipFile as exc:
        raise FileValidationError(
            UploadErrorCode.FILE_CONTENT_MISMATCH,
            "El contenedor Office no es un ZIP valido.",
        ) from exc
    has_required_prefix = any(name.startswith(required_prefix) for name in names)
    if "[Content_Types].xml" not in names or not has_required_prefix:
        raise FileValidationError(
            UploadErrorCode.FILE_CONTENT_MISMATCH,
            "El contenedor Office no coincide con la extension declarada.",
        )
    if any(name.endswith("vbaProject.bin") for name in names):
        raise FileValidationError(
            UploadErrorCode.FILE_CONTENT_MISMATCH,
            "Los documentos Office con macros no estan permitidos.",
        )
