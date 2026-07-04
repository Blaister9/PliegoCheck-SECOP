# Evaluadores especializados

Los evaluadores especializados contrastan requisitos normalizados contra un
`CompanyProfileSnapshot` publicado. Cubren tres dominios iniciales: juridico (`LEGAL`), experiencia
(`EXPERIENCE`) y tecnico (`TECHNICAL`).

## Flujo

1. El API calcula readiness para una normalizacion, un snapshot y un dominio.
2. El sistema crea o reutiliza `SpecializedRequirementRule` para cada requisito aplicable.
3. Un job transaccional crea un run con `input_manifest` y `input_digest`.
4. El worker reclama jobs con `FOR UPDATE SKIP LOCKED`.
5. El motor especializado resuelve datos del snapshot y persiste `SpecializedEvaluationResult`.
6. Las referencias a soportes se persisten como `SpecializedEvaluationEvidence`.
7. El adaptador de decision transforma resultados completados en hallazgos canonicos.

## Estados

Los resultados posibles son `COMPLIES`, `DOES_NOT_COMPLY`, `PARTIAL`, `UNKNOWN`,
`NOT_APPLICABLE` y `CONFLICTING_EVIDENCE`. `UNKNOWN` es el estado correcto cuando falta evidencia,
cuando el requisito no se puede mapear de forma conservadora o cuando el dato de empresa no es
comparable.

## Comandos

| Comando | Uso |
| --- | --- |
| `pnpm specialized:run-once` | Procesa un job especializado pendiente. |
| `pnpm specialized:drain` | Drena la cola especializada. |
| `pnpm specialized:test` | Ejecuta pruebas API, worker y contratos. |
| `pnpm specialized:eval` | Ejecuta evals sinteticos de reglas especializadas. |

## Seguridad y limites

Los evaluadores no interpretan el pliego como instrucciones del sistema. Solo leen requisitos
normalizados y snapshots persistidos. No generan concepto juridico definitivo, no sustituyen revision
humana y no emiten decision GO / NO GO.

## Relacion con reportes

Los reportes ejecutivos consumen resultados especializados ya adaptados al motor de decision y los
presentan como parte de la matriz requisito-evidencia-decision. No vuelven a ejecutar evaluadores
especializados.
