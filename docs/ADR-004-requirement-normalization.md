# ADR-004 - Normalizacion de requisitos con IA y evidencia trazable

- **Estado:** Aceptado
- **Fecha:** 2026-07-02
- **Decisores:** Equipo PliegoCheck

## Contexto

La Microfase 4 introduce el primer flujo real de IA: convertir segmentos extraidos en requisitos
normalizados, conservando evidencia verificable y sin evaluar cumplimiento empresarial.

La decision GO / NO GO sigue fuera de alcance. El modelo propone candidatos; el sistema valida
deterministicamente que cada cita exista en segmentos del snapshot de la ejecucion.

## Decision

Implementar normalizacion asincrona con:

- OpenAI Responses API mediante SDK oficial de Python.
- Structured Outputs estrictos derivados de Pydantic/JSON Schema.
- `RequirementNormalizationProvider` como interfaz de dominio.
- `OpenAIResponsesNormalizationProvider` para operacion real.
- `FakeNormalizationProvider` solo para tests/evals y entornos explicitamente habilitados.
- Prompts versionados en `prompts/requirement-normalization/v1/`.
- `PromptVersion` persistido con hash SHA-256 del contenido usado.
- Snapshot inmutable de extracciones y segmentos elegibles.
- Batching deterministico por orden de documento, extraccion y segmento.
- `EvidenceValidator` deterministico antes de persistir requisitos.
- Cola PostgreSQL `requirement_normalization_jobs` con `FOR UPDATE SKIP LOCKED`.

## Tablas nuevas

- `prompt_versions`
- `requirement_normalization_jobs`
- `requirement_normalization_runs`
- `requirement_normalization_batches`
- `requirements`
- `requirement_evidence`
- `requirement_relations`
- `rejected_requirement_candidates`

## Reglas

- `PLIEGOCHECK_AI_ENABLED=false` por defecto.
- No se llama OpenAI en CI.
- No se suben archivos originales a OpenAI; solo segmentos seleccionados y metadata minima.
- No se dan herramientas al modelo.
- No se usa web search, file search ni computer use.
- Todo requisito persistido debe tener evidencia valida.
- Candidatos sin evidencia o con citas falsas se guardan como rechazados.
- Subsanabilidad no explicita queda `UNKNOWN`.
- Todos los requisitos inician `review_status=PENDING` y `requires_human_review=true`.
- La normalizacion no produce estados `COMPLIES`, `DOES_NOT_COMPLY` ni decisiones GO / NO GO.

## Consecuencias

El worker ya no procesa solo extraccion documental. Tambien puede reclamar trabajos de normalizacion
y continuar lotes pendientes. La API crea ejecuciones auditables pero no llama al proveedor en linea.
La web muestra requisitos, evidencia y relaciones como texto plano.

## Riesgos y mitigaciones

| Riesgo | Mitigacion |
| --- | --- |
| Prompt injection documental | Segmentos delimitados como datos no confiables, sin herramientas y con validacion de evidencia. |
| Salidas estructuradas invalidas | Pydantic/JSON Schema estricto, rechazo controlado y tests de provider mockeado. |
| Citas inventadas | `EvidenceValidator` verifica `segment_id`, snapshot, cita, offsets y ubicacion. |
| Costo de tokens | Limites por lote, total, llamadas por run y registro de usage. |
| Confundir normalizacion con decision | UI, docs y contratos excluyen cumplimiento y GO / NO GO. |

## Fuera de alcance

Perfil de empresa, evaluacion juridica/financiera/tecnica, cumplimiento, OCR, embeddings, vector
database, SECOP II automatico, autenticacion y multiempresa.
