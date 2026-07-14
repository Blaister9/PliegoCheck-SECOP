"""Errores sanitizados del proveedor externo."""

from pliegocheck_schemas import ExternalProcurementErrorCode


class ExternalProviderError(RuntimeError):
    def __init__(self, code: ExternalProcurementErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message[:500]
