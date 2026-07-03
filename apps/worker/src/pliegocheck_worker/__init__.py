"""Worker de PliegoCheck-SECOP.

Procesa trabajos asincronos de extraccion documental y normalizacion de requisitos.
La normalizacion usa proveedores aislados, prompts versionados y validacion
deterministica de evidencia.
"""

SERVICE_NAME = "worker"
SERVICE_VERSION = "0.1.0"
