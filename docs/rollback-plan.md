# Plan de rollback

Rollback en despliegue controlado no es garantia de reversibilidad perfecta.
Ejecutarlo solo si la validacion falla y antes de incorporar datos reales.

## Aplicacion

1. Detener web, API y worker.
2. Volver al commit anterior aprobado.
3. Reinstalar dependencias si cambiaron lockfiles.
4. Reiniciar servicios y ejecutar health checks.

## Migraciones

Usar downgrade de Alembic solo si la migracion es reversible y no hay datos
criticos nuevos. Si hay duda, preferir restaurar backup completo.

```powershell
uv run alembic -c apps/api/alembic.ini downgrade <revision-anterior>
```

## Backup y storage

```powershell
pnpm ops:restore -- -BackupDir var/backups/pliegocheck-YYYYMMDD-HHMMSS -Yes
```

Verificar manifest antes de restaurar. El restore local reemplaza DB y storage
local configurado; no debe ejecutarse contra datos ajenos al piloto.

## Sesion piloto controlada

- Backup antes de sesion: `pnpm ops:backup` y revision de `manifest.json`.
- Backup despues de sesion: repetir backup y conservar hallazgos/acta fuera del reset.
- Falla de migracion: detener servicios, restaurar backup si existe, no hacer downgrade si hay duda.
- Falla de web: `pnpm controlled:stop`, revisar `var/controlled/logs/web.err.log` y volver al commit
  aprobado.
- Falla de worker: revisar `pnpm worker:health`, colas y logs; no borrar datos antes de capturar
  evidencia.
- Falla de storage: no continuar si `PLIEGOCHECK_STORAGE_PATH` no es escribible o expone rutas
  fisicas.
- Limpieza sintetica: `pnpm controlled:reset -Confirm` solo despues de conservar feedback y
  evidencia permitida.

## Verificacion posterior

- `pnpm db:check`
- `GET /health/ready`
- `pnpm worker:health`
- login admin
- auditoria visible

## Cuando no hacer downgrade automatico

- Si usuarios ya cargaron datos reales.
- Si la migracion transformo datos de forma irreversible.
- Si no existe backup verificado.
- Si el problema es de configuracion y puede corregirse sin tocar datos.
