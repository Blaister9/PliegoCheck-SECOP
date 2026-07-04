"""Piloto controlado end-to-end con datos sinteticos (Microfase 11).

Este paquete vive en el worker porque necesita coordinar tanto la API
(``pliegocheck_api``) como los orquestadores del worker. Usa exclusivamente
datos sinteticos, no llama a OpenAI y opera sobre la base de datos configurada.
"""

PILOT_DOMAIN = "pilot.pliegocheck.local"
PILOT_REFERENCE_PREFIX = "PILOT-"
