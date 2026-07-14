# Sincronizacion y descarga controlada de documentos SECOP

La Microfase 17 agrega un inventario incremental de documentos publicos a los procesos importados. No automatiza ofertas, no ejecuta tramites en SECOP y no produce decisiones GO / NO GO.

## Flujo operativo

1. `POST /processes/{id}/external-sync` crea un trabajo PostgreSQL idempotente.
2. `pnpm secop:sync-run-once` (o `secop:sync-drain`) actualiza un snapshot normalizado, inventario y eventos de cambio.
3. Un usuario con `external:download` confirma `POST .../external-documents/{document_id}/download`.
4. `pnpm secop:document-run-once` descarga en streaming. Solo HTTPS, host permitido, DNS publico, puerto 443, tipos permitidos, firma coherente y tamano acotado llegan a almacenamiento.
5. La descarga crea o reutiliza `ProcessDocument`, pero queda `NOT_QUEUED`.
6. `POST .../extract` inicia explicitamente la extraccion existente. La evaluacion y la decision siguen siendo etapas separadas.

Los endpoints de lectura requieren `external:read`; sincronizar requiere `external:sync`; descargar requiere `external:download`; extraer conserva `document:write`. Admin tiene todos los permisos, Analyst puede operar y Reviewer/Viewer solo consultan.

## Configuracion

Todas las capacidades son opt-in. Los defaults deshabilitan sincronizacion y descarga. `PLIEGOCHECK_SECOP_DOCUMENT_ALLOWED_HOSTS` debe ser un CSV exacto, sin comodines. La allowlist no reemplaza la verificacion DNS: cada URL inicial y cada redireccion se resuelven y se rechazan direcciones privadas, loopback, link-local, multicast, reservadas o no especificadas.

Los limites de archivo, cantidad por sincronizacion, timeout, redirecciones y tipos MIME se documentan en `.env.example`. Nunca se registran tokens, cookies, bytes descargados, `storage_key` ni rutas fisicas en contratos API.

## Operacion y recuperacion

- Consultar readiness: `GET /processes/{id}/external-sync/readiness`.
- Consultar ejecuciones y eventos: `GET /processes/{id}/external-sync-runs` y `GET /processes/{id}/external-sync-runs/{run_id}`.
- Un fallo queda explicito como `FAILED`/`REJECTED`, con codigo controlado; no se interpreta HTML como documento.
- Los workers reclaman filas con `FOR UPDATE SKIP LOCKED`. Los indices parciales impiden dos trabajos activos del mismo tipo.
- Reintentar implica volver a encolar desde la API. Las versiones exitosas son inmutables; un hash identico produce `UNCHANGED` y un hash nuevo enlaza una version nueva con `previous_version_id`.
- El smoke live es solo opt-in: `PLIEGOCHECK_SECOP_DOCUMENT_ALLOW_LIVE_TESTS=true pnpm secop:documents:smoke`. Solo comprueba disponibilidad/esquema, no descarga ni persiste payloads.

## Validacion

```powershell
pnpm secop:documents:test
pnpm secop:documents:eval
pnpm schemas:check
pnpm db:check
```

Las pruebas y evals usan fixtures offline. No almacenan documentos reales ni secretos.
