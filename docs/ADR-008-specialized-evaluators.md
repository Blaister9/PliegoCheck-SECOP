# ADR-008 - Evaluadores especializados juridico, experiencia y tecnico

## Estado

Aceptada - Microfase 8.

## Contexto

El motor de decision ya puede combinar hallazgos canonicos, pero en Microfase 7 solo recibia
resultados financieros. Para reducir `NOT_EVALUATED` sin convertir el LLM en juez final, se
requieren evaluadores especializados que comparen requisitos normalizados contra un
`CompanyProfileSnapshot` publicado.

## Decision

Implementar evaluadores deterministas para los dominios `LEGAL`, `EXPERIENCE` y `TECHNICAL`.
Cada evaluador persiste una regla especializada por requisito, resuelve datos desde el snapshot,
produce resultados tipados por requisito y expone revision manual auditada.

Los evaluadores no llaman OpenAI, no usan prompts, no infieren equivalencias libres y no producen
GO / NO GO. Sus resultados se adaptan a `DecisionInputFinding` con `source_type =
SPECIALIZED_EVALUATION`; el motor deterministico conserva la decision global.

## Consecuencias

- La ausencia de dato, soporte o comparabilidad produce `UNKNOWN`.
- La evidencia conflictiva o no verificable no se transforma en cumplimiento.
- Las revisiones humanas pueden confirmar, rechazar u overridear el resultado efectivo, sin borrar
  el resultado automatico original.
- Las categorias fuera de financiero, juridico, experiencia y tecnico siguen cubiertas como
  `NOT_EVALUATED`.
- La decision final sigue siendo reproducible: requisitos + snapshot + reglas + politica versionada.
