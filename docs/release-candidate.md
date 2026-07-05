# Release candidate - Microfase 14

- **Version sugerida:** `0.14.0-mvp-controlled`
- **Commit base para cierre:** `dbcf168c528c58625fc761a995d0da4875e915f5`
- **Commit final:** PR de Microfase 14 al integrarse en `main`.
- **Estado:** candidato de cierre de MVP controlado, no productivo.

No se recibió retroalimentación real de usuarios piloto en esta microfase.

## Alcance incluido

Incluye piloto sintetico end-to-end, auth local, roles, auditoria, decision
deterministica, reporte, ZIP, runbooks, checklists, rollback, smoke tests de
deployment readiness, scripts `controlled:*`, data scan, kit de usuarios piloto,
matriz de hallazgos, cierre MVP, criterios de aceptacion/no produccion y guia de
demo final.

## Fuera de alcance

Produccion, datos reales, SSO, MFA, S3 real obligatorio, despliegue real en
servidor, OCR, integracion SECOP, firma digital, PDF, correos, notificaciones,
nuevos evaluadores y nuevas reglas de decision.

## Validaciones requeridas

- `pnpm pilot:eval`
- `pnpm deployment:eval`
- `pnpm deployment:backup-check`
- `pnpm controlled:eval`
- `pnpm controlled:data-scan`
- `pnpm mvp:eval`
- `pnpm mvp:data-scan`
- `pnpm check`
- Checklist de navegador antes de una nueva sesion real.
- CI verde.
- Escaneo de secretos sin hallazgos reales.

## Criterios de aceptacion

- No hay hallazgos `BLOCKER` abiertos en `docs/mvp-final-findings.md`.
- Los hallazgos diferidos quedan marcados como diferidos, no cerrados sin
  evidencia.
- Admin puede operar y auditar en entorno controlado.
- Viewer no modifica.
- Reviewer puede revisar decision.
- ZIP se descarga sin secretos ni rutas fisicas.
- Feedback estructurado sigue disponible para cada rol.
- No hay datos reales en `pilot/`, `docs/`, `evals` ni scripts.

## Criterios de no produccion

- No existe validacion real con usuarios piloto.
- No hay SSO/MFA productivo.
- No hay almacenamiento productivo ni politica completa de retencion.
- No hay aprobacion juridica, seguridad y operacion para datos reales.
- No hay integracion SECOP ni OCR.
- Cualquier hallazgo `BLOCKER` o `HIGH` abierto sin aceptacion formal bloquea
  produccion.

## Riesgos

- Evidencia sintetica no equivale a validacion juridica real.
- La falta de feedback real impide afirmar usabilidad o valor con usuarios.
- `PENDIENTE_INFORMACION` sigue siendo resultado esperado y honesto cuando falta
  evidencia critica.
- Storage local no sustituye S3 productivo.

## Rollback

Seguir [rollback-plan.md](rollback-plan.md). No hacer downgrade automatico si
hay datos no reversibles o backup no verificado.

## Indice de entrega

Ver [mvp-delivery-index.md](mvp-delivery-index.md).

## Siguiente decision

Microfase 15 - Decision ejecutiva sobre evolucion a piloto real o pausa tecnica.
