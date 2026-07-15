# Plan de piloto supervisado

Secuencia: readiness → entorno controlado → auth → snapshot publicado → consulta SECOP limitada → discovery → revisión/importación → sync documental → análisis explícito → monitor/baseline/segunda corrida → alertas → entrega local o dry-run → reinicio/recuperación → backup/restore aislado → retención dry-run → reporte → apagado.

Condiciones de parada: las enumeradas en `config/pilot/supervised-pilot-v1.json`. Todo dato live queda solo en base/storage local ignorado y el informe conserva únicamente conteos, latencias, estados y warnings sanitizados.
