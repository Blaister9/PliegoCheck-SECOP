# Deduplicación de alertas

El estado incremental conserva únicamente outcome, compatibilidad, urgencia, completitud, cierre, hashes documental/de assessment y estado de fuente. JSON se canonicaliza antes de obtener SHA-256; su orden no altera el resultado.

El fingerprint combina monitor, fuente e identidad del proceso, tipo de alerta, identidad del cambio material, hash de política y snapshot empresarial. Una condición persistente actualiza `last_seen_at`. Un nuevo cierre, documento o transición produce una identidad distinta. Reintentos y workers concurrentes convergen por el constraint único.

Archivar conserva el histórico. Si ocurre después un cambio material se crea otra alerta; resolver tampoco cambia la oportunidad.
