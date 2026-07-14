"""Errores de dominio serializados de forma estable."""

from http import HTTPStatus
from typing import Any

from pliegocheck_schemas import (
    ApiError,
    AuthErrorCode,
    CompanyErrorCode,
    DecisionErrorCode,
    DecisionReportErrorCode,
    ExternalDocumentErrorCode,
    ExternalProcurementErrorCode,
    ExtractionErrorCode,
    FinancialErrorCode,
    NormalizationErrorCode,
    OpportunityErrorCode,
    UploadErrorCode,
)


class DomainError(Exception):
    """Error controlado de la API que no expone detalles internos."""

    def __init__(
        self,
        code: (
            UploadErrorCode
            | ExtractionErrorCode
            | NormalizationErrorCode
            | CompanyErrorCode
            | FinancialErrorCode
            | DecisionErrorCode
            | DecisionReportErrorCode
            | AuthErrorCode
            | ExternalProcurementErrorCode
            | ExternalDocumentErrorCode
            | OpportunityErrorCode
        ),
        message: str,
        *,
        status_code: int = HTTPStatus.BAD_REQUEST,
        details: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def to_payload(self) -> dict[str, Any]:
        return ApiError(code=self.code, message=self.message, details=self.details).model_dump(
            mode="json"
        )
