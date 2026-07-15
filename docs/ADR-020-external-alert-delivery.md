# ADR-020 — Entrega externa controlada de alertas

Estado: aceptado para Microfase 20.

## Decisión

`OpportunityAlert` permanece como fuente de verdad. En la misma transacción que crea una alerta, las suscripciones inmediatas elegibles crean un `NotificationOutboxMessage` idempotente. Un worker PostgreSQL reclama mensajes vencidos con `FOR UPDATE SKIP LOCKED`; SMTP y HTTP ocurren fuera de la transacción del motor de alertas.

Se admiten `INTERNAL_ONLY`, `EMAIL_SMTP` y `SIGNED_WEBHOOK`. La entrega externa, cada canal y los envíos reales están deshabilitados por defecto; dry-run está activo. Los secretos solo se resuelven desde variables de entorno referenciadas por nombre. El webhook usa allowlist, validación DNS/IP y HMAC-SHA256 versionado.

## Consecuencias

Un fallo externo nunca elimina ni oculta la alerta interna. La aceptación por SMTP o webhook no acredita lectura o procesamiento. PostgreSQL conserva idempotencia, intentos, backoff, dead-letter lógico y operación auditable sin incorporar otro broker.
