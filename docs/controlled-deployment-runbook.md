# Runbook de despliegue controlado

Este runbook aplica a demo/piloto controlado. **Controlado/piloto no es
produccion**.

## 1. Prerrequisitos

- Node 22, pnpm 11, Python 3.12, uv, Docker y PostgreSQL local o gestionado.
- Repo en `main`, CI verde y working tree limpio.
- Variables desde `.env.pilot.example` copiadas a `.env` local no versionado.

## 2. Variables de entorno

Usar origenes exactos, nunca `*`. En HTTPS, `PLIEGOCHECK_AUTH_COOKIE_SECURE=true`.
`PLIEGOCHECK_AUTH_SECRET_KEY` debe venir de gestor de secretos o `.env` local.

## 3. Base de datos y migraciones

```powershell
pnpm infra:up
pnpm db:migrate
pnpm db:check
```

## 4. Storage local

Verificar que `PLIEGOCHECK_STORAGE_PATH` y `PLIEGOCHECK_BACKUP_OUTPUT_DIR` sean
escribibles y no apunten fuera del directorio operativo acordado.

## 5. Admin inicial

```powershell
Get-Content .\admin-password.txt | pnpm auth:create-admin -- --email admin@example.com --display-name "Admin" --password-stdin
```

Eliminar `admin-password.txt` del entorno local despues de crear el usuario.

## 6. Inicio de servicios

```powershell
pnpm dev:api
pnpm worker:health
pnpm dev:web
```

Para Linux/macOS usar los mismos comandos en shells separados.

## 7. Health checks y smoke

```powershell
Invoke-RestMethod http://localhost:8000/health/live
Invoke-RestMethod http://localhost:8000/health/ready
pnpm deployment:eval
```

## 8. Pilot prepare y validacion posterior

```powershell
pnpm pilot:readiness
pnpm pilot:prepare
pnpm pilot:run
pnpm pilot:eval
```

Completar [browser-validation-checklist.md](browser-validation-checklist.md).

## 9. Backup previo y posterior

```powershell
pnpm deployment:backup-check
pnpm ops:backup -- -OutputDir var/backups
```

Revisar `manifest.json`, hashes y exclusion de `.env`.

## 10. Logs y errores comunes

- 401: falta sesion o cookie.
- 403: rol sin permiso; revisar auditoria `PERMISSION_DENIED`.
- Ready `storage=error`: ruta no escribible.
- Pilot mode falla al arrancar: secreto, CORS o cookie segura incompletos.

## 11. Rollback y apagado seguro

Seguir [rollback-plan.md](rollback-plan.md). Para apagar localmente:

```powershell
pnpm pilot:reset -- --confirm
pnpm infra:down
```
