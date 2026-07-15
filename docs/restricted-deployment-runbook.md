# Runbook de despliegue restringido

1. Instalar Docker/Compose, OpenSSL, Python 3.12, Node 22, pnpm 11 y uv; sincronizar un commit aprobado.
2. Crear fuera del checkout: configuración, secretos, TLS, storage y backups. Copiar `deploy/restricted/restricted.env.example` y reemplazar todos los placeholders.
3. Exportar `PLIEGOCHECK_RESTRICTED_ENV_FILE` con la ruta de configuración.
4. Ejecutar `pnpm restricted:preflight`. Un `FAIL` impide continuar; documentar warnings humanos de red/firewall.
5. Ejecutar `pnpm restricted:deploy`. Es idempotente: construye imágenes, inicia DB, aplica Alembic, inicia servicios y valida HTTPS.
6. Si se habilitó bootstrap, comprobar creación única, cambiar la contraseña, poner el flag en `false` y reiniciar. Crear ANALYST, REVIEWER y VIEWER únicamente con autorización.
7. Ejecutar `pnpm restricted:validate` y `pnpm restricted:status`; completar checklists de `deploy/restricted/delivery/`.
8. Habilitar SECOP, scheduler o entrega solo después de aprobación, con límites, allowlists y dry-run.
9. Programar backup; ejecutar `restricted:backup:verify` y `restricted:restore:verify` periódicamente.
10. Para detener sin perder datos: `pnpm restricted:stop`. Nunca usar reset como operación normal.

La URL mostrada procede de la configuración, no prueba que exista DNS o acceso institucional. Escalar incidentes según `restricted-incident-response.md`.
