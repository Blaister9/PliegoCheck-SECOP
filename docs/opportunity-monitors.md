# Monitores de oportunidades

Un monitor es una búsqueda SECOP tipada y periódica vinculada a un snapshot empresarial publicado e inmutable. Admite `HOURLY`, `EVERY_3_HOURS`, `EVERY_6_HOURS`, `EVERY_12_HOURS`, `DAILY` y `WEEKDAYS`; su zona por defecto es `America/Bogota`.

Estados: `ACTIVE`, `PAUSED`, `DISABLED` y `ERROR`. El usuario puede crear, editar, pausar, reanudar y solicitar una ejecución manual desde `/monitors`. Cambiar snapshot es explícito, queda auditado y crea un baseline nuevo. No se sustituye automáticamente cuando aparece otro snapshot o una política posterior.

Los filtros almacenan únicamente contratos SECOP permitidos, no payloads completos ni secretos. El baseline guarda el estado actual sin alertas masivas; `alert_on_initial_results` habilita la excepción conscientemente.
