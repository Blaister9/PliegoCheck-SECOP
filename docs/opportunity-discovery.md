# Descubrimiento de oportunidades

`POST /opportunities/discovery-runs` exige empresa, snapshot publicado y filtros SECOP o IDs de resultados persistidos. El worker ejecuta la búsqueda pública existente, crea candidatos y aplica screening. Los comandos `opportunity-discovery-*` y `opportunity-assessment-*` consumen la misma unidad transaccional porque cada candidato se evalúa dentro de su discovery.

La ejecución pasa por `PENDING`, `PROCESSING` y un estado terminal. Repetir inputs normalizados reutiliza la ejecución; `force=true`, otro snapshot o un hash de política distinto crea historial. La UI `/opportunities` permite empresa, snapshot, fuente, palabra clave, ubicación, outcome y orden, y consulta el progreso.

Fuentes incompletas no bloquean el screening: producen estados desconocidos y campos faltantes. SECOP I sin cierre confiable mantiene urgencia `UNKNOWN`.
