# Paquete RESTRICTED_SINGLE_HOST

Paquete reproducible para un host institucional detrás de VPN/red/allowlist. No es prueba de despliegue institucional ni autorización de producción.

Prepare un env externo desde `restricted.env.example`, secretos `*_FILE`, certificado/cadena y clave, storage y backup fuera del checkout. Exporte `PLIEGOCHECK_RESTRICTED_ENV_FILE`. Ejecute:

```text
pnpm restricted:preflight
pnpm restricted:deploy
pnpm restricted:validate
pnpm restricted:status
pnpm restricted:backup
pnpm restricted:backup:verify
pnpm restricted:restore:verify
pnpm restricted:retention:dry-run
pnpm restricted:stop
```

Use wrappers `.ps1` o `.sh` equivalentes. Retention real exige `--confirm-retention`; rollback exige target y confirmación. Stop conserva datos. Consulte los runbooks y checklists de `delivery/`.
