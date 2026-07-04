# Runbook operativo

## Desarrollo local

```powershell
pnpm install --frozen-lockfile
uv sync --all-packages --frozen
pnpm infra:up
pnpm db:migrate
pnpm auth:create-admin -- --email admin@example.com --display-name "Admin"
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
