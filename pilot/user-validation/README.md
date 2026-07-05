# Kit de validacion con usuarios piloto

Este kit organiza una sesion de validacion controlada con datos sinteticos. No usar datos reales,
credenciales reales, documentos institucionales reales ni nombres de personas naturales reales.

Archivos:

- `session-plan.md`: agenda y criterios de ejecucion.
- `tasks-admin.md`: tareas para ADMIN.
- `tasks-analyst.md`: tareas para ANALYST.
- `tasks-reviewer.md`: tareas para REVIEWER.
- `tasks-viewer.md`: tareas para VIEWER.
- `feedback-form.md` y `feedback-form.csv`: captura estructurada.
- `findings-matrix.csv`: matriz de hallazgos.
- `validation-minutes-template.md`: acta de sesion.
- `consent-and-scope-note.md`: nota de alcance y consentimiento.

Comandos base:

```powershell
pnpm controlled:deploy
pnpm controlled:validate
pnpm pilot:run
pnpm controlled:backup-check
pnpm controlled:stop
```
