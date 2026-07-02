"""Aplicacion FastAPI de PliegoCheck-SECOP."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pliegocheck_api.config import settings
from pliegocheck_api.errors import DomainError
from pliegocheck_api.routes import contracts, health, processes
from pliegocheck_schemas import ApiError, UploadErrorCode

app = FastAPI(
    title=settings.title,
    version=settings.version,
    description=settings.description,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_web_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)
app.include_router(health.router)
app.include_router(contracts.router)
app.include_router(processes.router)


@app.exception_handler(DomainError)
def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.to_payload())


@app.exception_handler(RequestValidationError)
def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    details: dict[str, str] = {}
    for index, error in enumerate(exc.errors()):
        location = ".".join(str(part) for part in error.get("loc", ()))
        details[f"error_{index}"] = f"{location}: {error.get('msg', 'invalid')}"
    payload = ApiError(
        code=UploadErrorCode.INVALID_PROCESS_DATA,
        message="Los datos enviados no cumplen el contrato esperado.",
        details=details,
    )
    return JSONResponse(status_code=422, content=payload.model_dump(mode="json"))
