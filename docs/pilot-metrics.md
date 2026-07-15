# Métricas sanitizadas del piloto

Registrar solo agregados: startup y readiness; duración/páginas/filas/warnings/fallos SECOP; candidatos/evaluados/outcomes/promedio de compatibilidad/componentes unknown/faltantes; documentos descubiertos/soportados/no soportados/fallidos/versiones/adendas potenciales; runs/alertas/deduplicadas/fallos/recuperaciones/no leídas; outbox/dry-run/local/retryable/permanent/suppressed; reinicio/backup/restore/retención/incidentes.

No registrar IDs externos, nombres, correos, URLs sensibles, payloads, documentos, tokens ni rutas. Estas métricas no miden probabilidad de adjudicación.

## Resultado técnico agregado

- Smoke previo: 1 registro, latencia aproximada 879 ms, 0 importaciones.
- Discovery supervisado: 50 evaluados, estado `COMPLETED_WITH_WARNINGS`, dentro del máximo de 100.
- Importación explícita: 1 importado y repetición `SKIPPED_DUPLICATE`.
- Documentos: 25 metadatos descubiertos, 0 descargas y 0 jobs de descarga.
- Monitoreo: 1 monitor, baseline con 0 alertas, cambio material con 1 alerta, repetición con 0 alertas nuevas.
- Entrega: 2 mensajes locales en `DRY_RUN`; 1 recuperación desde `PROCESSING`, 0 envíos reales.
- Reinicio: conteos preservados en reinicio de procesos y de infraestructura completa.
- Backup/restore: backup con hashes SHA-256 y restore aislado con 8 grupos de conteos verificados; entorno temporal eliminado.
- Retención: dry-run, 0 payloads limpiados y 0 intentos eliminados.
