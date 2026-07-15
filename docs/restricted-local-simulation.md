# Evidencia de simulación local restricted

Fecha técnica: 2026-07-14/15 (America/Bogota). Alcance: equivalencia local `RESTRICTED_SINGLE_HOST`, no despliegue institucional.

| Verificación | Resultado |
| --- | --- |
| Preflight con config/secrets/TLS sintéticos externos | `PASS_WITH_WARNINGS` (firewall/VPN requieren revisión humana) |
| Builds multi-stage backend/web y Compose | PASS |
| Migraciones y seis servicios declarados | PASS |
| API/web/PostgreSQL sin puertos publicados | PASS |
| HTTPS, redirect, certificado y seis headers | PASS |
| CORS permitido/denegado y host denegado | PASS |
| Login, cookie Secure/HttpOnly/SameSite, ADMIN y VIEWER 403 | PASS |
| Worker heartbeat; scheduler deshabilitado | PASS |
| SECOP opt-in, consulta no transaccional limitada a un resultado | PASS; sin importación ni descarga |
| Entrega externa | dry-run; SMTP/webhook apagados |
| Backup, manifest y SHA-256 | PASS |
| Restore verification aislado | PASS; 96 tablas; base/temporales eliminados |
| Retención dry-run | PASS; cero eliminaciones |
| Reinicio, deploy repetido y bootstrap repetido | PASS; un solo ADMIN, credenciales sin cambio |
| Stop | PASS; cero contenedores, volumen/storage/backup preservados |

Defectos hallados y corregidos durante la simulación: biblioteca `libpq` ausente en runtime, assets de configuración no copiados a backend, healthcheck incompatible con TrustedHost, permisos/capacidades del proxy no root, bootstrap ejecutado sin entrypoint y preflight de puertos no idempotente. Ningún fallo produjo pérdida de datos o exposición de secretos.

No se usaron servidor, dominio, certificado, cuenta, dato empresarial ni autorización institucional real. Los artefactos sintéticos se mantuvieron ignorados y se eliminan al cierre.
