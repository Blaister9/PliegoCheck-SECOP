# Runbook de despliegue controlado

Para el paquete institucional restringido de Microfase 22 no use este Compose de piloto: siga [restricted-deployment-runbook.md](restricted-deployment-runbook.md). Ese modo exige HTTPS, secretos externos, puertos internos no publicados y gate propio; tampoco equivale a despliegue institucional real.

Microfase 21 reutiliza este entorno mediante `pnpm pilot:supervised:deploy`. `validate` es de solo lectura, `stop` conserva volúmenes, `reset` exige `-- --Confirm` y `report` escribe bajo `var/`. SECOP live requiere opt-in y límites del manifiesto.

El worker de discovery se ejecuta con `pnpm pilot:supervised:opportunity-worker-once`. El controlador aplica el opt-in SECOP exclusivamente a ese proceso y fuerza descarga documental, entrega externa, SMTP y webhook apagados, con notificaciones en dry-run. No se debe sustituir por una suposición de herencia desde la API.

Este runbook aplica a demo/piloto controlado. **Controlado/piloto no es
produccion**.
Este despliegue controlado es para validacion piloto con datos sinteticos. No es produccion.

## 1. Prerrequisitos

- Node 22, pnpm 11, Python 3.12, uv, Docker y PostgreSQL local o gestionado.
- Repo en `main`, CI verde y working tree limpio.
- Variables desde `.env.pilot.example` copiadas a `.env` local no versionado.

## 2. Variables de entorno

Usar origenes exactos, nunca `*`. En HTTPS, `PLIEGOCHECK_AUTH_COOKIE_SECURE=true`.
`PLIEGOCHECK_AUTH_SECRET_KEY` debe venir de gestor de secretos o `.env` local.

## 3. Base de datos y migraciones

Opcion automatizada para sesion piloto:

```powershell
pnpm controlled:deploy
pnpm controlled:validate
```

Opcion manual:

```powershell
docker compose -f compose.pilot.yaml up -d postgres controlled-storage
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
pnpm controlled:eval
pnpm controlled:data-scan
pnpm mvp:eval
pnpm mvp:data-scan
```

## 8. Pilot prepare y validacion posterior

```powershell
pnpm pilot:readiness
pnpm pilot:prepare
pnpm pilot:run
pnpm pilot:eval
pnpm controlled:validate
```

Completar [browser-validation-checklist.md](browser-validation-checklist.md) y el kit
[`pilot/user-validation`](../pilot/user-validation/README.md).
Para cierre de MVP controlado, revisar tambien [mvp-delivery-index.md](mvp-delivery-index.md) y
[mvp-final-findings.md](mvp-final-findings.md).

## 9. Backup previo y posterior

```powershell
pnpm deployment:backup-check
pnpm controlled:backup-check
pnpm ops:backup -- -OutputDir var/backups
```

Revisar `manifest.json`, hashes y exclusion de `.env`.
Ejecutar backup antes y despues de la sesion. Si falla migracion, web, worker o storage, detener
servicios con `pnpm controlled:stop`, conservar logs/hallazgos y seguir [rollback-plan.md](rollback-plan.md).

## 10. Logs y errores comunes

- 401: falta sesion o cookie.
- 403: rol sin permiso; revisar auditoria `PERMISSION_DENIED`.
- Ready `storage=error`: ruta no escribible.
- Pilot mode falla al arrancar: secreto, CORS o cookie segura incompletos.

## 11. Rollback y apagado seguro

Seguir [rollback-plan.md](rollback-plan.md). Para apagar localmente:

```powershell
pnpm controlled:stop
pnpm controlled:reset -Confirm
pnpm infra:down
```
