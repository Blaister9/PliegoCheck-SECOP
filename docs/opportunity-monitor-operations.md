# Operación de monitores

El piloto supervisado permite como máximo dos monitores, dos páginas y veinte alertas. Debe verificar baseline sin spam, segunda corrida deduplicada, pausa/reanudación y recuperación; un reinicio no debe crear alertas por sí mismo.

La entrega externa de Microfase 20 es opt-in y se opera por separado; no añade SMS, WhatsApp, push, Slack ni Teams específico y no garantiza lectura.

La capacidad está deshabilitada por defecto con `PLIEGOCHECK_MONITORING_ENABLED=false`. Operación acotada:

```text
pnpm monitors:scheduler-run-once
pnpm monitors:run-once
pnpm monitors:drain
```

Los límites de resultados/páginas complementan timeout, rate limit y cache SECOP existentes. Los retries son limitados. Un fallo aislado no alerta; al cruzar el threshold configurado el monitor pasa a `ERROR` y crea una única `MONITOR_FAILURE`. La primera ejecución posterior correcta reactiva el monitor y crea `MONITOR_RECOVERED`.

Los mensajes de error se sanitizan. La retención por defecto es 365 días. No existen email, SMS, WhatsApp, push, Slack, Teams ni webhooks productivos en esta fase.
