# ADR-022 — Despliegue institucional restringido

## Decisión

Se adopta `RESTRICTED_SINGLE_HOST`: un host o VM, Docker Compose, Nginx como único reverse proxy, web, API, worker, scheduler opt-in y PostgreSQL. Solo Nginx publica HTTP/HTTPS en la dirección configurada; API, web y PostgreSQL permanecen en redes Compose. HTTPS usa certificado y clave suministrados externamente. Los secretos se montan desde archivos externos y nunca forman parte de imágenes, Compose renderizado persistente ni Git.

PostgreSQL usa volumen nombrado; documentos y backups usan rutas persistentes externas al checkout. Backend y web son imágenes multi-stage, no root y con versiones fijadas. Los servicios tienen health checks, límites de logs, `no-new-privileges` y capacidades mínimas. El scheduler permanece deshabilitado salvo opt-in. Backup incluye dump, storage, manifest y SHA-256; restore verification crea una base aislada y nunca reemplaza el entorno activo. Rollback cambia imágenes, exige confirmación y no hace downgrade automático de Alembic.

## Consecuencias

El modelo reduce superficie y es reproducible, pero no aporta alta disponibilidad. La autenticación local es temporal y solo es aceptable detrás de VPN/red/allowlist. SSO, MFA, almacenamiento objeto, PostgreSQL administrado, SIEM y operación 24/7 son evoluciones futuras. Para pasar a `PACKAGE_READY` hacen falta host, red, dominio, certificados y usuarios institucionales reales, aprobación humana y ausencia de riesgos HIGH.
