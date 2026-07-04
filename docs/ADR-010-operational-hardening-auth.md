# ADR-010 - Endurecimiento operativo y autenticacion local

- **Estado:** Aceptado
- **Fecha:** 2026-07-04
- **Decisores:** Equipo PliegoCheck

## Contexto

Las microfases anteriores dejaron flujos funcionales de documentos, evaluaciones, decision y
reporte. Para un piloto controlado se necesita proteger API y web, crear usuarios locales,
registrar auditoria operacional y validar configuracion sin introducir SSO ni multi-tenant
productivo completo.

## Decision

Implementar autenticacion local con usuario/password, hash PBKDF2, sesiones persistidas en
PostgreSQL y cookie HttpOnly. La autorizacion se aplica en backend mediante middleware por permisos
basicos y la web solo refleja el estado de sesion.

| Area | Decision |
| --- | --- |
| Passwords | PBKDF2-SHA256 con salt; nunca texto plano. |
| Sesiones | Token aleatorio en cookie HttpOnly; solo hash en DB. |
| Roles | `ADMIN`, `ANALYST`, `REVIEWER`, `VIEWER`. |
| Permisos | Matriz cerrada en `AuthPermission`. |
| API | Middleware global protege endpoints funcionales. |
| Web | Middleware Next redirige rutas internas a `/login` si no hay cookie. |
| Auditoria | `operational_audit_events` y `auth_login_events` sin secretos. |
| Config | `PLIEGOCHECK_PILOT_MODE=true` exige auth y cookie segura. |

## Consecuencias

- El piloto puede operar sin credenciales compartidas ni usuarios por defecto.
- Tests y desarrollo pueden usar `PLIEGOCHECK_AUTH_ENABLED=false` de forma explicita.
- SSO, MFA, recuperacion por correo y permisos por fila quedan fuera de alcance.
