# ADR-012 - Ajustes post-piloto y preparacion de despliegue controlado

- **Estado:** Aceptado
- **Fecha:** 2026-07-04
- **Decisores:** Equipo PliegoCheck

## Contexto

La Microfase 11 valido el flujo end-to-end con datos sinteticos, autenticacion y
auditoria activa. Antes de un despliegue controlado se requiere convertir esa
validacion en una release candidate operable: hallazgos post-piloto
clasificados, smoke tests reproducibles, checklist manual de navegador,
configuracion de entorno piloto, runbook, rollback y documentacion de riesgos.

## Decision

1. Mantener el despliegue controlado como **piloto**, no produccion.
2. Resolver por scripts/evals y documentacion antes que por endpoints nuevos.
3. Agregar `pnpm deployment:eval` como smoke de configuracion, health, auth,
   worker, storage, backup y subpaso `pilot:eval`.
4. Agregar `pnpm deployment:backup-check` como verificacion estatica de
   manifest, hashes y exclusion de secretos.
5. Documentar validacion manual de navegador en
   [browser-validation-checklist.md](browser-validation-checklist.md).
6. No crear tag de release en esta microfase.

## Consecuencias

- CI valida readiness de despliegue sin llamadas externas ni OpenAI real.
- La release candidate queda documentada, pero requiere ejecucion manual de
  navegador antes de un piloto con usuarios.
- SSO, MFA, S3 real, OCR, SECOP real, firma digital y alta disponibilidad
  siguen fuera de alcance.
