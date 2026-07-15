# Checklist operativo del piloto

- [x] Readiness sin `BLOCKED`.
- [x] Cuenta local autorizada y rol verificados; 401/403 cubiertos por pruebas.
- [x] Perfil sintético con snapshot publicado.
- [x] Consulta SECOP live opt-in dentro de límites; sin payload versionado.
- [x] Discovery, detalle, brechas, importación idempotente y fuente oficial.
- [x] Sync/documentos conservadores y análisis profundo explícito.
- [x] Monitor: baseline, segunda corrida, pausa, reanudación y deduplicación.
- [x] Alertas internas y outbox preservados; entrega dry-run.
- [x] Reinicio y recuperación sin duplicación.
- [x] Backup verificado y restore en destino aislado.
- [x] Retención dry-run con cero eliminación.
- [x] Reporte sanitizado y gate derivados; el apagado se ejecuta al integrar.
