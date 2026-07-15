# Runbook de piloto de notificaciones

En el piloto supervisado la entrega queda `LOCAL_OR_DRY_RUN`. Un canal real requiere configuración explícita, consentimiento, allowlist, credenciales, kill switch y desactivar dry-run conscientemente; su ausencia no bloquea la validación técnica.

1. Confirmar consentimiento y allowlist sintética.
2. Mantener kill switch apagado y dry-run activo.
3. Levantar PostgreSQL y `docker compose -f compose.notifications.yaml up -d`.
4. Validar destino y prueba en dry-run.
5. Para Mailpit local únicamente, habilitar SMTP, host `localhost`, puerto 1025 e insecure local.
6. Activar un solo monitor y límite diario bajo.
7. Revisar `/operations/notifications` y `/notification-deliveries`.
8. Ante anomalía, apagar `PLIEGOCHECK_EXTERNAL_DELIVERY_ENABLED` y drenar únicamente tras revisión.
9. Cerrar, exportar evidencia sanitizada y bajar infraestructura.

Este procedimiento prepara un piloto; no demuestra que usuarios reales lo hayan ejecutado.
