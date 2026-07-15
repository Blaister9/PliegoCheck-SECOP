# Entrega de notificaciones

Flujo: alerta interna → selección de suscripción → outbox idempotente → worker → intento. Destinos y suscripciones pueden pausarse independientemente. Quiet hours difieren alertas no críticas; el bypass crítico es explícito. Kill switch, canal, allowlists de piloto y rate limits se comprueban antes de abrir red.

Comandos: `pnpm notifications:run-once`, `notifications:drain`, `notifications:digest-run-once`, `notifications:digest-drain`, `notifications:retention-run-once` y `notifications:retention-dry-run`.
