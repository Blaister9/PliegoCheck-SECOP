# ADR-013 - Controlled deployment user validation

## Estado

Aceptada.

## Contexto

La Microfase 12 dejo una release candidate de despliegue controlado. La siguiente necesidad no es
produccion, sino una sesion piloto reproducible donde usuarios con roles `ADMIN`, `ANALYST`,
`REVIEWER` y `VIEWER` ejecuten tareas sinteticas y entreguen retroalimentacion estructurada.

Este despliegue controlado es para validacion piloto con datos sinteticos. No es produccion.

## Decision

Se agregan scripts `controlled:*`, `compose.pilot.yaml`, evals de controlled deployment, data scan
estatico, kit de validacion por rol, checklist de readiness, matriz de hallazgos, acta plantilla y
guia de observacion. No se agregan endpoints ni contratos nuevos porque la informacion requerida ya
existe en health, auth, worker, piloto, reportes y auditoria.

## Consecuencias

- El entorno controlado puede levantarse localmente con PostgreSQL en Docker y API/web como procesos
  locales supervisados.
- CI valida el camino reproducible con TestClient y scripts versionados, sin OpenAI real ni datos
  reales.
- La retroalimentacion queda normalizada antes de decidir la Microfase 14.
- SSO, MFA, S3 real obligatorio, OCR, PDF, firma digital e integracion SECOP siguen fuera de alcance.
