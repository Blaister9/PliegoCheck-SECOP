"""Configuracion de la API. Sin secretos: solo metadatos del servicio."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Metadatos del servicio API."""

    service_name: str = "api"
    version: str = "0.1.0"
    title: str = "PliegoCheck-SECOP API"
    description: str = (
        "API de PliegoCheck-SECOP. Fundacion tecnica (Microfase 1): "
        "expone endpoints de salud y el catalogo de contratos compartidos. "
        "Todavia no implementa analisis de procesos."
    )


settings = Settings()
