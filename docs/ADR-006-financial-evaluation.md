# ADR-006 - Evaluacion financiera inicial

## Estado

Aceptada. Microfase 6.

## Contexto

La normalizacion de requisitos ya produce requisitos financieros trazables y el perfil de empresa ya
puede publicar snapshots inmutables con periodos, metricas y evidencias. Faltaba el primer evaluador
vertical que comparara un requisito financiero concreto contra un snapshot especifico de empresa sin
emitir decision global.

## Decision

Implementar la evaluacion financiera como flujo deterministico:

- API en `/processes/{process_id}/financial-evaluations`.
- Cola PostgreSQL con `financial_evaluation_jobs` y `financial_evaluation_runs`.
- Worker `financial-run-once` / `financial-drain`.
- Reglas financieras persistidas en `financial_requirement_rules`.
- Resultados por requisito en `financial_evaluation_results`.
- Calculos derivados en `financial_metric_calculations`.
- Revision manual auditada en `financial_evaluation_result_reviews`.
- Eventos de auditoria en `financial_evaluation_events`.

La evaluacion usa un snapshot publicado de empresa. No consulta datos mutables del perfil durante el
worker. El digest de entrada incluye proceso, normalizacion, snapshot, requisitos, reglas y versiones
de formulas.

## Reglas

El mapeo inicial reconoce solo requisitos `FINANCIAL`. Si una metrica, operador, periodo o valor
exigido no se puede determinar de forma conservadora, la regla queda `AMBIGUOUS` y el resultado es
`UNKNOWN`.

La evidencia controla la decision por requisito:

- `VERIFIED`: puede producir `COMPLIES` o `DOES_NOT_COMPLY`.
- `SUPPORTED`: puede producir resultado comparativo, pero con `requires_human_review=true`.
- `DECLARED_ONLY`, evidencia faltante o datos no soportados: `UNKNOWN`.
- evidencia conflictiva: `CONFLICTING_EVIDENCE`.

La ausencia de evidencia critica nunca produce cumplimiento.

## Consecuencias

- La evaluacion financiera no depende de OpenAI ni de prompts.
- Los resultados son reproducibles con el mismo snapshot y las mismas reglas.
- No se emite `GO`, `NO_GO` ni otro estado global.
- La Microfase 7 consumira estos resultados como insumo del motor deterministico de decision.

## Alternativas consideradas

- Evaluar directamente en la API: descartado para mantener cola auditable y reintentos.
- Usar un agente LLM financiero: descartado para esta microfase; las reglas aritmeticas deben ser
  reproducibles.
- Evaluar contra el perfil mutable: descartado porque rompe reproducibilidad y trazabilidad.
