# Evaluación de preparación del piloto supervisado

Evaluación previa sobre la base `75045eaecff05a26e67d0bbd71f1f7343de61ed8`. Estados permitidos: `VERIFIED`, `PARTIAL`, `NOT_VERIFIED`, `BLOCKED` y `NOT_APPLICABLE`.

| Control | Estado previo | Evidencia / condición |
| --- | --- | --- |
| Main y CI verdes | VERIFIED | PR #21 integrada; base local y remota coincidentes al iniciar. |
| Infraestructura y migraciones | VERIFIED | Compose controlado, migraciones y health checks existentes. |
| Feature flags conocidas | VERIFIED | SECOP, monitoreo y entrega externa son opt-in. |
| Auth y usuario autorizado | VERIFIED | Login técnico local y controles 401/403 verificados; ninguna credencial se versiona. |
| Empresa y snapshot publicado | VERIFIED | Perfil sintético y snapshot `PUBLISHED` usados en discovery y monitoreo. |
| Fuentes SECOP habilitables | VERIFIED | Solo Datos Abiertos oficial, consulta live opt-in y limitada. |
| Scheduler controlable | VERIFIED | Deshabilitado por defecto y ejecución manual disponible. |
| Kill switch y dry-run | VERIFIED | Entrega externa apagada y `dry_run=true`. |
| Retención | VERIFIED | Políticas y dry-run existentes. |
| Backup, restore y rollback | VERIFIED | Backup real con hashes y restore real en base/almacenamiento aislados; destino temporal eliminado. |
| Participante humano | NOT_VERIFIED | No se recibió evidencia humana al preparar este documento. |
| Entrega externa real | NOT_APPLICABLE | No es requisito; se limita a local o dry-run. |

No hay un `BLOCKED` de seguridad previo. Las acciones live requieren flags explícitos, perfil sintético o autorizado y límites del manifiesto.
