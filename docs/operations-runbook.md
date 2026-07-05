# Runbook operativo

## Desarrollo local

```powershell
pnpm install --frozen-lockfile
uv sync --all-packages --frozen
pnpm infra:up
pnpm db:migrate
pnpm auth:create-admin -- --email admin@example.com --display-name "Admin"
pnpm deployment:eval
pnpm dev:api
pnpm dev:web
```

## Health

- `GET /health/live`: proceso vivo.
- `GET /health/ready`: DB, storage, CORS y config auth.
- `pnpm worker:health`: capacidades de colas, decision, reportes y auth.

## Auditoria

`GET /admin/audit-events` lista eventos sanitizados. No contiene passwords, tokens, cookies,
documentos completos ni rutas fisicas.

## Errores

Todo error controlado usa envelope `ApiError`. Los errores internos se sanitizan y devuelven
`X-Request-ID`.

## Piloto controlado

El piloto controlado end-to-end usa exclusivamente datos sinteticos y no llama a OpenAI.

- `pnpm pilot:readiness` — diagnostico de preparacion (entorno local, usuarios, dataset).
- `pnpm pilot:prepare` — siembra usuarios, proceso, documentos, empresa y snapshot sinteticos.
- `pnpm pilot:run` — ejecuta el flujo completo y devuelve un `PilotRunSummary` en JSON.
- `pnpm pilot:reset -- --confirm` — elimina UNICAMENTE datos de piloto; nunca datos ajenos ni `.env`.

Guion y checklist: [demo-script.md](demo-script.md), [pilot-demo-checklist.md](pilot-demo-checklist.md).
Dataset: [pilot-dataset.md](pilot-dataset.md). Retroalimentacion: [pilot-feedback-log.md](pilot-feedback-log.md).

## Despliegue controlado

El despliegue controlado sigue siendo piloto, no produccion. Antes de una demo o validacion con
usuarios ejecutar:

- [post-pilot-findings.md](post-pilot-findings.md)
- [browser-validation-checklist.md](browser-validation-checklist.md)
- [controlled-deployment-runbook.md](controlled-deployment-runbook.md)
- [pre-deployment-checklist.md](pre-deployment-checklist.md)
- [post-deployment-checklist.md](post-deployment-checklist.md)
- [rollback-plan.md](rollback-plan.md)
- [release-candidate.md](release-candidate.md)

Comandos:

```powershell
pnpm deployment:eval
pnpm deployment:backup-check
pnpm pilot:eval
```
