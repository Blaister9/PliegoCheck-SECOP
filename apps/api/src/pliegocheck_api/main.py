"""Aplicacion FastAPI de PliegoCheck-SECOP."""

from fastapi import FastAPI

from pliegocheck_api.config import settings
from pliegocheck_api.routes import contracts, health

app = FastAPI(
    title=settings.title,
    version=settings.version,
    description=settings.description,
)
app.include_router(health.router)
app.include_router(contracts.router)
