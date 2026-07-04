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

## Piloto controlado end-to-end (Microfase 11)

El flujo end-to-end con datos sinteticos esta automatizado y validado:

- `pnpm pilot:prepare` siembra el dataset sintetico (usuarios, proceso, documentos, empresa, snapshot).
- `pnpm pilot:run` ejecuta proceso -> extraccion -> normalizacion controlada -> evaluaciones ->
  decision -> reporte -> ZIP -> auditoria y devuelve un resumen JSON.
- `pnpm pilot:eval` valida el flujo con auth activo (roles, decision, reporte, ZIP, auditoria, logout).
- `pnpm pilot:reset -- --confirm` limpia unicamente datos de piloto.

Ver [demo-script.md](demo-script.md), [pilot-demo-checklist.md](pilot-demo-checklist.md) y
[pilot-dataset.md](pilot-dataset.md). El resultado honesto del dataset es `PENDIENTE_INFORMACION`.
