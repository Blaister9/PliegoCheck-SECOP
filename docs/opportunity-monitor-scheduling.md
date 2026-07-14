# Programación de monitores

El scheduler reclama como máximo `PLIEGOCHECK_MONITOR_MAX_ACTIVE_RUNS` monitores activos vencidos con bloqueo PostgreSQL `SKIP LOCKED`. Un índice parcial impide dos runs `PENDING/PROCESSING` del mismo monitor.

`next_run_at` se calcula desde el slot programado anterior, en la zona IANA configurada, y se guarda en UTC. Esto evita drift por duración del trabajo y respeta DST. Tras una caída se colapsan intervalos atrasados: existe como máximo una recuperación inmediata, nunca una tormenta de catch-up.

La frecuencia mínima es una hora. `WEEKDAYS` salta sábado y domingo. Pausados, deshabilitados y futuros no se reclaman.
