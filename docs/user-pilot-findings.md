# Hallazgos de usuarios piloto

Matriz viva para la sesion de usuarios piloto. Los estados permitidos son `OPEN`, `TRIAGED`,
`ACCEPTED`, `DEFERRED`, `RESOLVED` y `OUT_OF_SCOPE`.

No se recibió retroalimentación real de usuarios piloto en esta microfase. Para el cierre del MVP
controlado, los pendientes heredados quedan cerrados o diferidos con evidencia explicita; no se
registran hallazgos nuevos simulados.

| id | rol | escenario | descripcion | resultado esperado | resultado observado | severidad | evidencia | decision | estado | fase destino |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UPF-001 | ALL | Sesion piloto | Validacion real con usuarios aun pendiente. | Usuarios ejecutan tareas por rol y registran feedback. | No se recibio retroalimentacion real. | HIGH | `pilot/user-validation/session-plan.md` | Diferir a Microfase 15; bloquea produccion y afirmaciones de validacion real, no el cierre documental del MVP controlado. | DEFERRED | Microfase 15 |
| UPF-002 | ADMIN | Identidad | SSO/MFA fuera de alcance. | Auth local suficiente para piloto sintetico. | No hay SSO/MFA. | OBSERVATION | `docs/authentication.md` | Mantener fuera de alcance; no usar como produccion. | DEFERRED | Fase futura |
| UPF-003 | ADMIN | Storage | S3 real fuera de alcance. | Storage local controlado con backup. | No hay S3 obligatorio. | OBSERVATION | `docs/backup-restore.md` | Aceptado para piloto sintetico. | DEFERRED | Fase futura |
| UPF-004 | REVIEWER | Reporte | PDF/firma digital fuera de alcance. | ZIP HTML/Markdown/JSON/CSV con manifest. | No hay PDF firmado. | OBSERVATION | `docs/decision-package.md` | Mantener como limitacion visible. | OUT_OF_SCOPE | Fase futura |
| UPF-005 | ALL | Datos | Datos reales prohibidos en esta etapa. | Solo dataset sintetico. | Control automatizado vigente. | HIGH | `pnpm controlled:data-scan`, `pnpm mvp:data-scan` | Mantener como criterio bloqueante si aparece dato real. | RESOLVED | Microfase 14 |
| UPF-006 | ALL | Navegacion | Navegacion browser manual debe ejecutarse en sesion piloto. | Checklist completada por rol. | No hubo nueva sesion real. | HIGH | `docs/browser-validation-checklist.md` | Diferir a proxima sesion real; no afirmar validacion manual ejecutada. | DEFERRED | Microfase 15 |

Severidades permitidas: `BLOCKER`, `HIGH`, `MEDIUM`, `LOW`, `OBSERVATION`.
