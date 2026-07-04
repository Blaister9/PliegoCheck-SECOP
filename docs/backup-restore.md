# Backup y restore local

## Backup

```powershell
pnpm ops:backup
```

Genera un directorio bajo `var/backups/` con:

- `database.dump`
- `storage.zip`
- `manifest.json` con SHA-256

No incluye `.env` ni secretos.

## Restore

```powershell
pnpm ops:restore -- -BackupDir var/backups/pliegocheck-YYYYMMDD-HHMMSS -Yes
```

Restore es destructivo sobre la base y el storage local configurados. Debe ejecutarse solo despues
de verificar el manifest y con `-Yes` explicito.
