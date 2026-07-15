# Política de datos del modo restringido

| Clase | Acceso y almacenamiento | Retención, backup y salida |
| --- | --- | --- |
| `PUBLIC_SECOP_DATA` | Roles autorizados; DB/storage | Según fuente/política; backup permitido; exportación revisada |
| `AUTHORIZED_COMPANY_DATA` | Tenant y mínimo privilegio; DB/storage | Política institucional; backup cifrado externo; no logs |
| `SYNTHETIC_DATA` | Validación técnica | Eliminar al cierre si no es evidencia necesaria |
| `SYSTEM_METADATA` | Operadores/admin | Retención operativa; backup según necesidad |
| `AUDIT_DATA` | Admin/auditor | Conservar mínimo trazable; no purga silenciosa |
| `DOCUMENT_CONTENT` | Roles con permiso; storage no web | Hash preservado; eliminación coordinada con derivados |
| `NOTIFICATION_DATA` | Operador/destino autorizado | Payload corto; limpiar antes que metadata; no backup de secretos |

Todo logging minimiza identificadores y excluye contenido, cookies y secretos. Exportación/eliminación requieren autorización y auditoría. Esta política prepara controles técnicos; no afirma cumplimiento legal institucional definitivo.
