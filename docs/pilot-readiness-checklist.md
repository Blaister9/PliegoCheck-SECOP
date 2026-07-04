# Checklist de piloto

- Auth habilitada.
- Admin inicial creado con password no versionado.
- Cookie `Secure=true` en HTTPS.
- CORS limitado a origenes esperados.
- `PLIEGOCHECK_PILOT_MODE=true` valida configuracion.
- Migraciones aplicadas.
- `pnpm check` verde.
- Backup local probado.
- Auditoria visible para admin.
- Viewer no puede modificar datos.
- Reviewer puede revisar decision pero no administrar usuarios.
- Analyst puede crear flujos funcionales.
- No hay secretos en repositorio, logs ni backups.
- Infraestructura local detenida al cerrar pruebas.
