"""Storage y empaquetado ZIP de reportes."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path
from typing import BinaryIO
from uuid import UUID

from pliegocheck_api.config import get_settings
from pliegocheck_api.reports.manifest import bytes_digest
from pliegocheck_api.reports.renderer import RenderedArtifact
from pliegocheck_api.storage import LocalDocumentStorage, StorageError

FORBIDDEN_NAMES = {".env", "env", "logs"}


class ReportArtifactStorage:
    """Almacenamiento de artefactos bajo claves generadas por servidor."""

    def __init__(self) -> None:
        root = Path(get_settings().storage_path) / "reports"
        self.storage = LocalDocumentStorage(root)

    def key_for(self, package_id: UUID, filename: str) -> str:
        safe = _safe_filename(filename)
        return f"{package_id}/{safe}"

    def save_bytes(self, data: bytes, storage_key: str) -> None:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(data)
            tmp_path = Path(tmp.name)
        try:
            self.storage.save(tmp_path, storage_key)
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink()
            raise

    def open(self, storage_key: str) -> BinaryIO:
        return self.storage.open(storage_key)

    def delete(self, storage_key: str) -> None:
        self.storage.delete(storage_key)


def build_zip(artifacts: list[RenderedArtifact]) -> bytes:
    with tempfile.SpooledTemporaryFile(max_size=10_000_000) as buffer:
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            for artifact in artifacts:
                filename = _safe_filename(artifact.filename)
                if filename == "decision-package.zip":
                    continue
                info = zipfile.ZipInfo(filename)
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, artifact.content)
        buffer.seek(0)
        return buffer.read()


def artifact_record(
    filename: str, artifact_type: str, content_type: str, content: bytes
) -> dict[str, object]:
    return {
        "filename": filename,
        "artifact_type": artifact_type,
        "content_type": content_type,
        "size_bytes": len(content),
        "sha256": bytes_digest(content),
    }


def _safe_filename(filename: str) -> str:
    if "/" in filename or "\\" in filename or ":" in filename or filename in FORBIDDEN_NAMES:
        raise StorageError("Nombre de artefacto invalido.")
    if filename.startswith(".") or ".." in filename:
        raise StorageError("Nombre de artefacto invalido.")
    return filename
