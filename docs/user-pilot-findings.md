# Hallazgos de usuarios piloto

Matriz viva para la sesion de usuarios piloto. Los estados permitidos son `OPEN`, `TRIAGED`,
`ACCEPTED`, `DEFERRED`, `RESOLVED` y `OUT_OF_SCOPE`.

| id | rol | escenario | descripcion | resultado esperado | resultado observado | severidad | evidencia | decision | estado | fase destino |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UPF-001 | ALL | Sesion piloto | Validacion real con usuarios aun pendiente. | Usuarios ejecutan tareas por rol y registran feedback. | Pendiente de ejecucion. | BLOCKER | `pilot/user-validation/session-plan.md` | Ejecutar en Microfase 13 antes de pasar a ajustes. | OPEN | Microfase 13 |
| UPF-002 | ADMIN | Identidad | SSO/MFA fuera de alcance. | Auth local suficiente para piloto sintetico. | No hay SSO/MFA. | OBSERVATION | `docs/authentication.md` | Mantener fuera de alcance; no usar como produccion. | DEFERRED | Fase futura |
| UPF-003 | ADMIN | Storage | S3 real fuera de alcance. | Storage local controlado con backup. | No hay S3 obligatorio. | OBSERVATION | `docs/backup-restore.md` | Aceptado para piloto sintetico. | DEFERRED | Fase futura |
| UPF-004 | REVIEWER | Reporte | PDF/firma digital fuera de alcance. | ZIP HTML/Markdown/JSON/CSV con manifest. | No hay PDF firmado. | OBSERVATION | `docs/decision-package.md` | Mantener como limitacion visible. | OUT_OF_SCOPE | Fase futura |
| UPF-005 | ALL | Datos | Datos reales prohibidos en esta etapa. | Solo dataset sintetico. | Pendiente de vigilancia en sesion. | HIGH | `pnpm controlled:data-scan` | Bloquear sesion si aparece dato real. | OPEN | Microfase 13 |
| UPF-006 | ALL | Navegacion | Navegacion browser manual debe ejecutarse en sesion piloto. | Checklist completada por rol. | Pendiente. | HIGH | `docs/browser-validation-checklist.md` | Registrar evidencia y fricciones. | OPEN | Microfase 13 |

Severidades permitidas: `BLOCKER`, `HIGH`, `MEDIUM`, `LOW`, `OBSERVATION`.
