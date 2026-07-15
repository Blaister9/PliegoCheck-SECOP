# Backup y restore restringidos

`pnpm restricted:backup` obtiene `pg_dump` desde PostgreSQL sin publicarlo, archiva storage, calcula SHA-256 y escribe manifest con versión, commit, schema y timestamp. Usa lock, directorio temporal y rename final; excluye secretos, entornos, claves, logs y temporales. El destino es externo al checkout.

`restricted:backup:verify` vuelve a calcular hashes. `restricted:restore:verify` crea una base temporal aislada dentro del PostgreSQL restringido, restaura el dump, cuenta tablas, extrae storage en un temporal, reporta conteos sanitizados y limpia ambos. Nunca reemplaza DB/storage activos ni ejecuta downgrade.

Programar backup según RPO institucional, copiarlo a medio autorizado y probar restore. Retención dry-run lista candidatos; eliminación exige `--confirm-retention` y preserva auditoría mínima y documentos activos. Un backup/restore fallido bloquea el gate.
