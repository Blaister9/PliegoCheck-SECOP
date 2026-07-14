"""Politica de URL estricta para impedir SSRF en descargas externas."""

from __future__ import annotations

import ipaddress
import socket
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import urlsplit

from pliegocheck_schemas import ExternalDocumentErrorCode


class ExternalDocumentSecurityError(Exception):
    def __init__(self, code: ExternalDocumentErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


Resolver = Callable[[str, int], list[str]]


def system_resolver(host: str, port: int) -> list[str]:
    return sorted(
        {str(item[4][0]) for item in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)}
    )


@dataclass(frozen=True)
class ValidatedPublicUrl:
    url: str
    host: str
    addresses: tuple[str, ...]


def validate_public_download_url(
    url: str, allowed_hosts: list[str], resolver: Resolver = system_resolver
) -> ValidatedPublicUrl:
    parsed = urlsplit(url)
    if (
        parsed.scheme.lower() != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.fragment
    ):
        raise ExternalDocumentSecurityError(
            ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_URL_REJECTED,
            "La URL externa debe ser HTTPS y no contener credenciales ni fragmentos.",
        )
    if parsed.port not in (None, 443):
        raise ExternalDocumentSecurityError(
            ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_URL_REJECTED,
            "El puerto de la URL externa no esta permitido.",
        )
    host = parsed.hostname.rstrip(".").lower()
    allowlist = {item.rstrip(".").lower() for item in allowed_hosts}
    if host not in allowlist:
        raise ExternalDocumentSecurityError(
            ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_HOST_REJECTED,
            "El host de descarga no esta en la lista permitida.",
        )
    try:
        addresses = tuple(resolver(host, 443))
    except OSError as exc:
        raise ExternalDocumentSecurityError(
            ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_URL_REJECTED,
            "No fue posible resolver el host de descarga.",
        ) from exc
    if not addresses:
        raise ExternalDocumentSecurityError(
            ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_URL_REJECTED,
            "El host de descarga no resolvio direcciones.",
        )
    for address in addresses:
        try:
            ip = ipaddress.ip_address(address)
        except ValueError as exc:
            raise ExternalDocumentSecurityError(
                ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_URL_REJECTED,
                "La resolucion DNS devolvio una direccion invalida.",
            ) from exc
        if (
            not ip.is_global
            or ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise ExternalDocumentSecurityError(
                ExternalDocumentErrorCode.EXTERNAL_DOCUMENT_URL_REJECTED,
                "La URL resolvio a una red no publica.",
            )
    return ValidatedPublicUrl(url=url, host=host, addresses=addresses)
