# Release candidate - Microfase 13

- **Version sugerida:** `0.13.0-rc.1`
- **Commit base:** `51ebe660abb45ee6450f01dc6d382ba5e96cad88`
- **Estado:** candidato para validacion controlada con usuarios piloto y datos sinteticos.

## Alcance

Incluye piloto sintetico end-to-end, auth local, roles, auditoria, decision, reporte, ZIP, runbooks,
checklists, rollback, smoke tests de deployment readiness, scripts `controlled:*`, data scan, kit de
usuarios piloto, tareas por rol, formulario de feedback, acta plantilla y matriz de hallazgos.

## Fuera de alcance

SSO, MFA, S3 real obligatorio, despliegue real en servidor, OCR, integracion
SECOP, firma digital, PDF, correos, notificaciones, nuevos evaluadores y nuevas
reglas de decision.

## Validaciones requeridas

- `pnpm deployment:eval`
- `pnpm deployment:backup-check`
- `pnpm controlled:eval`
- `pnpm controlled:data-scan`
- `pnpm pilot:eval`
- `pnpm check`
- Checklist de navegador ejecutada.
- CI verde.
- Escaneo de secretos sin hallazgos reales.

## Riesgos

- No hay SSO/MFA ni multi-tenant productivo completo.
- Storage local no sustituye S3 productivo.
- Evidencia sintetica no equivale a validacion juridica real.
- `PENDIENTE_INFORMACION` es resultado esperado y honesto del dataset.

## Criterios de aceptacion

- Smoke tests y CI en verde.
- Admin puede operar y auditar.
- Viewer no modifica.
- Reviewer puede revisar decision.
- ZIP se descarga sin secretos ni rutas fisicas.
- Feedback estructurado disponible para cada rol.
- No hay datos reales en `pilot/`, `docs/`, `evals` ni scripts.

## Criterios para sesion piloto

- `pnpm controlled:deploy` o preparacion manual equivalente completada.
- `pnpm controlled:validate` pasa.
- Roles `ADMIN`, `ANALYST`, `REVIEWER` y `VIEWER` disponibles.
- Backup previo verificado.
- Formulario y matriz de hallazgos listos.

## Criterios para bloquear sesion piloto

- Cualquier dato real o secreto aparece en pantalla, logs, ZIP o repositorio.
- Health/readiness queda en error.
- Login falla para roles principales.
- ZIP no descarga.
- Viewer puede modificar datos.
- Backup previo no existe o manifest no valida.

## Rollback

Seguir [rollback-plan.md](rollback-plan.md). No hacer downgrade automatico si
hay datos no reversibles o backup no verificado.

## Checklist de evidencia

- Commit y PR.
- Resultado de CI.
- Salida de `pnpm controlled:eval`.
- Salida de `pnpm controlled:data-scan`.
- Manifest de backup previo y posterior.
- Acta de validacion.
- Matriz de hallazgos.

## Pasos de despliegue controlado

Seguir [controlled-deployment-runbook.md](controlled-deployment-runbook.md) y
checklists pre/post despliegue.

## Responsables genericos

- Operacion tecnica: prepara entorno, migraciones y backups.
- Lider de piloto: ejecuta demo y checklist.
- Revisor juridico/negocio: revisa resultado y limitaciones.

## Checklist de aprobacion

- [ ] Pre-deployment checklist completo.
- [ ] Browser validation checklist completo.
- [ ] Post-deployment checklist completo.
- [ ] Riesgos aceptados por responsables.
