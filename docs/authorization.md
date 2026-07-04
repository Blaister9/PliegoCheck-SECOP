# Autorizacion

La API decide permisos. La web puede ocultar botones, pero no sustituye la autorizacion del
backend.

## Roles

| Rol | Uso |
| --- | --- |
| `ADMIN` | Usuarios, auditoria, configuracion y operacion. |
| `ANALYST` | Procesos, empresas, evaluaciones, decisiones y reportes. |
| `REVIEWER` | Revision, overrides y descarga de reportes. |
| `VIEWER` | Lectura y descarga limitada. |

## Permisos

Los permisos cerrados incluyen `process:read`, `process:write`, `company:read`, `company:write`,
`decision:review`, `report:generate`, `report:download`, `admin:users`, `admin:settings` y
`audit:read`.

Sin sesion la API responde `401`. Sin permiso responde `403` y registra `PERMISSION_DENIED`.
