# Preflight restringido

`pnpm restricted:preflight` es de solo lectura salvo probes eliminables en storage/backup. Valida Docker y Compose, daemon, OpenSSL, CPU, disco, puertos, Compose, esquema, HTTPS, origins/hosts/proxies explícitos, cookie segura, rutas externas escribibles, archivos secretos, placeholders, bootstrap y certificado (parseo, vigencia, hostname y correspondencia con clave). La clave nunca se imprime.

Estados: `PASS`, `PASS_WITH_WARNINGS` y `FAIL`. Firewall/VPN, memoria institucional, DNS y permisos del host requieren revisión humana adicional. Un fallo de certificado, secreto, puerto o configuración bloquea deploy.
