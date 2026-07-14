# ADR-019 — Monitoreo periódico y alertas internas

Estado: aceptado (Microfase 19).

## Decisión

Los monitores fijan empresa, snapshot publicado y hash de política. PostgreSQL conserva el calendario, reclama filas con `FOR UPDATE SKIP LOCKED` y garantiza un único run activo por monitor. Cada run reutiliza discovery y screening de la Microfase 18; después compara un estado compacto y genera alertas mediante un motor determinístico independiente del ORM.

La primera ejecución es baseline y no alerta resultados existentes salvo opt-in explícito. Un fingerprint SHA-256 incluye monitor, identidad SECOP, tipo, cambio material, política y snapshot. Los reintentos actualizan `last_seen_at`; no duplican alertas.

## Consecuencias

No se incorporan Redis, Celery, correo, SMS, webhooks ni frecuencias menores de una hora. La disponibilidad depende de SECOP. Las alertas requieren revisión humana y no automatizan una oferta.
