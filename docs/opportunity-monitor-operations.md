# Operación de monitores

La capacidad está deshabilitada por defecto con `PLIEGOCHECK_MONITORING_ENABLED=false`. Operación acotada:

```text
pnpm monitors:scheduler-run-once
pnpm monitors:run-once
pnpm monitors:drain
```

Los límites de resultados/páginas complementan timeout, rate limit y cache SECOP existentes. Los retries son limitados. Un fallo aislado no alerta; al cruzar el threshold configurado el monitor pasa a `ERROR` y crea una única `MONITOR_FAILURE`. La primera ejecución posterior correcta reactiva el monitor y crea `MONITOR_RECOVERED`.

Los mensajes de error se sanitizan. La retención por defecto es 365 días. No existen email, SMS, WhatsApp, push, Slack, Teams ni webhooks productivos en esta fase.
