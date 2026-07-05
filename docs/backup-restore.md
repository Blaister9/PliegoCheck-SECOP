# Backup y restore local

## Backup

```powershell
pnpm ops:backup
pnpm deployment:backup-check
```

Genera un directorio bajo `var/backups/` con:

- `database.dump`
- `storage.zip`
- `manifest.json` con SHA-256

No incluye `.env` ni secretos.
`pnpm deployment:backup-check` valida de forma reproducible que los scripts declaran manifest,
hashes y exclusiones sensibles.

## Restore

```powershell
pnpm ops:restore -- -BackupDir var/backups/pliegocheck-YYYYMMDD-HHMMSS -Yes
```

Restore es destructivo sobre la base y el storage local configurados. Debe ejecutarse solo despues
de verificar el manifest y con `-Yes` explicito.

Para despliegue controlado, ejecutar backup antes y despues del smoke. Si el restore requiere borrar
storage, el script solo permite rutas bajo `var/` para evitar reemplazar rutas inesperadas.
