# Observabilidad local

La observabilidad actual es local y suficiente para demo/piloto controlado, no
para produccion.

## Request id

La API agrega `X-Request-ID` a respuestas y errores. Usarlo para correlacionar
errores de navegador, API y auditoria.

## Health

- `/health/live`: proceso API vivo.
- `/health/ready`: DB, storage, auth config y CORS.
- `pnpm worker:health`: colas, evaluadores, decision, reportes, auth y piloto.

## Auditoria

`/admin/audit-events` muestra eventos operacionales sanitizados. No debe incluir
passwords, tokens, cookies, documentos completos ni rutas fisicas.

## Summaries

- `pnpm pilot:run` imprime `PilotRunSummary`.
- `pnpm deployment:eval` valida readiness y falla con salida pytest.
- Backups generan `manifest.json` con hashes.

## Limites conocidos

No hay trazas distribuidas, metricas externas, alertas ni log aggregation. Para
despliegue productivo se requiere una fase posterior.
