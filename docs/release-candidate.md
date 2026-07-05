# Release candidate - Microfase 12

- **Version sugerida:** `0.12.0-rc.1`
- **Commit base:** `29cbed5791ebad26a630cdfa7071ddede03ada48`
- **Estado:** candidato para despliegue controlado con datos sinteticos.

## Alcance

Incluye piloto sintetico end-to-end, auth local, roles, auditoria, decision,
reporte, ZIP, runbooks, checklists, rollback y smoke tests de deployment
readiness.

## Fuera de alcance

SSO, MFA, S3 real obligatorio, despliegue real en servidor, OCR, integracion
SECOP, firma digital, PDF, correos, notificaciones, nuevos evaluadores y nuevas
reglas de decision.

## Validaciones requeridas

- `pnpm deployment:eval`
- `pnpm deployment:backup-check`
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

## Rollback

Seguir [rollback-plan.md](rollback-plan.md). No hacer downgrade automatico si
hay datos no reversibles o backup no verificado.

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
