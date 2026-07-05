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

En despliegue controlado, validar manualmente viewer read-only, reviewer review, analyst execution y
admin audit con [browser-validation-checklist.md](browser-validation-checklist.md). La web puede
ocultar acciones, pero el backend es la fuente de verdad.
La Microfase 13 agrega tareas por rol en `pilot/user-validation/` para registrar acciones permitidas
y denegadas durante la sesion piloto.
