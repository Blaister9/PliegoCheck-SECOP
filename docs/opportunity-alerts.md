# Alertas internas de oportunidades

Las alertas señalan novedades o cambios relevantes según la política configurada. No constituyen una recomendación automática de presentar oferta.

La bandeja `/alerts` permite filtrar, marcar leída/no leída, archivar, restaurar y resolver. Ninguna acción modifica por sí sola la oportunidad. Las severidades `INFO`, `LOW`, `MEDIUM`, `HIGH` y `CRITICAL` expresan atención operativa, no compatibilidad.

Se cubren nuevas oportunidades prioritarias, cambios materiales de outcome o score, urgencia, cierres, estado documental, posibles adendas, fallos repetidos y recuperación. Información faltante y cambios `UNKNOWN → UNKNOWN` no crean alertas positivas. El digest interno agrupa hoy, 24 horas o 7 días; no se entrega externamente.

Los cambios documentales se comparan contra el inventario persistido de `ExternalProcessDocument` del proceso importado: un aumento de identidades produce `NEW_DOCUMENT_DISCOVERED`, un cambio de versión sin aumentar el inventario produce `DOCUMENT_UPDATED`, y los estados `POTENTIAL_ADDENDUM` o `CONFIRMED_ADDENDUM` conservan su clasificación de fuente. Si el candidato aún no está enlazado a un proceso interno no se inventa un inventario ni una adenda; solo se conserva el estado documental resumido de discovery.

Las ejecuciones fallidas programan reintentos con espera incremental (uno y dos minutos por defecto antes del umbral de tres fallos). La cola solo reclama reintentos cuyo `scheduled_for` ya venció; al alcanzar el umbral el monitor pasa a `ERROR` y genera una alerta interna crítica.
