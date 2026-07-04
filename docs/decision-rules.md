# Reglas de decision

El motor evalua reglas tipadas en `apps/api/src/pliegocheck_api/decision/rules.py`. Cada evaluacion
persistida conserva codigo, version, prioridad, estado, hechos, requisitos, hallazgos, razon y
resultado sugerido.

## Hallazgo canonico

`DecisionInputFinding` conserva requisito, categoria, dominio, outcome, aplicabilidad, evidencia,
review y banderas explicitas:

- `is_blocking`
- `is_remediable`
- `partner_solvable`
- `submission_blocker`

`partner_solvable` y `submission_blocker` son `false` por defecto. Los adaptadores financiero,
juridico, experiencia y tecnico no los infieren desde un incumplimiento.

## Adaptadores disponibles

- `FINANCIAL_EVALUATION`: resultados financieros.
- `SPECIALIZED_EVALUATION` para dominios `LEGAL`, `EXPERIENCE` y `TECHNICAL`.

Los requisitos sin resultado completado para su adaptador se completan como `NOT_EVALUATED`.

## Cobertura

`DecisionCoverageAnalyzer` produce conteos, no probabilidades: totales, obligatorios, opcionales,
evaluados, no evaluados, cumple, no cumple, parcial, desconocido, no aplicable, conflictos, bloqueos,
remediables, aliados, submission blockers y revision humana pendiente. Por categoria reporta
`COMPLETE`, `PARTIAL`, `MISSING` o `NOT_REQUIRED`.

## Reglas activas

- `SUBMISSION_BLOCKER_CONFIRMED`
- `NON_SUBSANABLE_MANDATORY_FAILURE`
- `BLOCKING_NONCOMPLIANCE`
- `CONFLICTING_CRITICAL_EVIDENCE`
- `MANDATORY_REQUIREMENT_NOT_EVALUATED`
- `MANDATORY_REQUIREMENT_UNKNOWN`
- `MANDATORY_REQUIREMENT_PARTIAL`
- `HUMAN_REVIEW_REQUIRED`
- `PARTNER_SOLVABLE_GAP`
- `REMEDIABLE_CONDITION_EXISTS`
- `ALL_MANDATORY_REQUIREMENTS_COMPLY`
- `FULL_REQUIRED_COVERAGE`

Los estados posibles son `TRIGGERED`, `NOT_TRIGGERED`, `NOT_APPLICABLE` e `INDETERMINATE`.

## Acciones

Las acciones se generan deterministamente desde reglas disparadas. No se inventa `due_at`. Cambiar
una accion a `ACKNOWLEDGED`, `RESOLVED` o `DISMISSED` no recalcula el run historico.
