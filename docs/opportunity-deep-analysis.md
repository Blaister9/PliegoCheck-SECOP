# Análisis profundo desde oportunidades

La acción verifica proceso importado, inventario, extracción, requisitos normalizados y ejecuciones financiera, especializadas y de decisión. La respuesta enumera `steps_ready`, `steps_queued`, `steps_blocked` y `missing_inputs`.

No se duplican fórmulas, evaluadores ni decisiones. Los resultados existentes se consultan por `process_id`; si falta el proceso o los documentos esenciales, la cadena queda bloqueada explícitamente. La acción registra auditoría, pero nunca genera una decisión silenciosa. La importación reutiliza la deduplicación del conector SECOP y la sincronización documental permanece en su flujo existente.
