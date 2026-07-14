"""Descarga en streaming con limites, firmas y validacion antes de persistir."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Protocol
from urllib.parse import urljoin

import httpx

from pliegocheck_api.config import Settings
from pliegocheck_api.external_documents.security import (
    Resolver,
    system_resolver,
    validate_public_download_url,
)
from pliegocheck_api.file_validation import (
    FileValidationError,
    detect_content_type,
    validate_declared_content_type,
    validate_original_filename,
)
from pliegocheck_schemas import ExternalDocumentErrorCode


class ExternalDownloadError(Exception):
    def __init__(self, code: ExternalDocumentErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class DownloadedArtifact:
    path: Path
    filename: str
    extension: str
    sha256: str
    size_bytes: int
    declared_content_type: str
    detected_content_type: str
    final_url: str


class DocumentDownloader(Protocol):
    def download(self, url: str, title: str) -> DownloadedArtifact: ...

    def close(self) -> None: ...


CONTENT_TYPE_EXTENSIONS = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "text/csv": ".csv",
    "text/plain": ".txt",
}


class SafeDocumentDownloader:
    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.BaseTransport | None = None,
        resolver: Resolver = system_resolver,
    ) -> None:
        self.settings = settings
        self.resolver = resolver
        self.client = httpx.Client(
            timeout=settings.secop_document_timeout_seconds,
            follow_redirects=False,
            transport=transport,
            headers={
                "User-Agent": "PliegoCheck-SECOP/0.17",
                "Accept": ", ".join(settings.secop_document_allowed_content_types),
            },
        )

    def close(self) -> None:
        self.client.close()

    def download(self, url: str, title: str) -> DownloadedArtifact:
        current = url
        response: httpx.Response | None = None
        for redirect_count in range(self.settings.secop_document_max_redirects + 1):
            validate_public_download_url(
                current, self.settings.secop_document_allowed_hosts, self.resolver
            )
            try:
                request = self.client.build_request("GET", current)
                response = self.client.send(request, stream=True)
            except httpx.HTTPError as exc:
                raise ExternalDownloadError(
                    ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_DOWNLOAD_FAILED,
                    "La descarga publica no pudo iniciarse.",
                ) from exc
            if response.status_code in {301, 302, 303, 307, 308}:
                location = response.headers.get("location")
                response.close()
                if not location or redirect_count >= self.settings.secop_document_max_redirects:
                    raise ExternalDownloadError(
                        ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_URL_REJECTED,
                        "La cadena de redirecciones no es aceptable.",
                    )
                current = urljoin(current, location)
                continue
            break
        assert response is not None
        try:
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
            if content_type in {"text/html", "application/xhtml+xml"}:
                raise ExternalDownloadError(
                    ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_HTML_RESPONSE,
                    "La fuente respondio HTML en vez de un documento.",
                )
            if content_type not in self.settings.secop_document_allowed_content_types:
                raise ExternalDownloadError(
                    ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_CONTENT_TYPE_REJECTED,
                    "El Content-Type de la respuesta no esta permitido.",
                )
            declared_length = response.headers.get("content-length")
            if (
                declared_length
                and int(declared_length) > self.settings.secop_document_max_file_size_bytes
            ):
                raise ExternalDownloadError(
                    ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_TOO_LARGE,
                    "El documento excede el limite configurado.",
                )
            extension = CONTENT_TYPE_EXTENSIONS[content_type]
            filename = _safe_filename(title, extension)
            validate_original_filename(filename)
            validate_declared_content_type(extension, content_type)
            digest = hashlib.sha256()
            size = 0
            with NamedTemporaryFile(
                prefix="pliegocheck-sec-", suffix=extension, delete=False
            ) as temp:
                path = Path(temp.name)
                try:
                    for chunk in response.iter_bytes(chunk_size=64 * 1024):
                        size += len(chunk)
                        if size > self.settings.secop_document_max_file_size_bytes:
                            raise ExternalDownloadError(
                                ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_TOO_LARGE,
                                "El documento excede el limite configurado.",
                            )
                        digest.update(chunk)
                        temp.write(chunk)
                except Exception:
                    temp.close()
                    path.unlink(missing_ok=True)
                    raise
            if size == 0:
                path.unlink(missing_ok=True)
                raise ExternalDownloadError(
                    ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_DOWNLOAD_FAILED,
                    "La fuente devolvio un documento vacio.",
                )
            try:
                detected = detect_content_type(path, extension)
            except FileValidationError as exc:
                path.unlink(missing_ok=True)
                raise ExternalDownloadError(
                    ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_CONTENT_TYPE_REJECTED, exc.message
                ) from exc
            return DownloadedArtifact(
                path, filename, extension, digest.hexdigest(), size, content_type, detected, current
            )
        except (ValueError, httpx.HTTPError) as exc:
            raise ExternalDownloadError(
                ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_DOWNLOAD_FAILED,
                "La respuesta de descarga no fue valida.",
            ) from exc
        finally:
            response.close()


def _safe_filename(title: str, extension: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._ -]+", "_", title).strip(" ._") or "documento-secOP"
    stem = stem[: 255 - len(extension)]
    if stem.lower().endswith(extension):
        stem = stem[: -len(extension)]
    return f"{stem}{extension}"
