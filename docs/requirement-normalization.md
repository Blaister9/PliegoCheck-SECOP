# Normalizacion de requisitos

La Microfase 4 convierte extracciones documentales completadas en requisitos normalizados con
evidencia trazable. No evalua cumplimiento empresarial y no produce decisiones GO / NO GO.

## Flujo

1. La API recibe `POST /processes/{process_id}/requirements/normalizations`.
2. Selecciona documentos con extracciones `COMPLETED` o `COMPLETED_WITH_WARNINGS`.
3. Construye un snapshot inmutable de documentos, extracciones y segmentos.
4. Calcula `input_digest` reproducible.
5. Divide segmentos en lotes deterministas.
6. Encola `requirement_normalization_jobs`.
7. El worker reclama trabajos con `FOR UPDATE SKIP LOCKED`.
8. Cada lote se envia al provider configurado.
9. La salida estructurada se valida contra JSON Schema.
10. `EvidenceValidator` verifica segmento, snapshot, cita y ubicacion.
11. Requisitos validos se persisten; candidatos sin soporte se rechazan.
12. La consolidacion propone duplicados o conflictos para revision humana.

## Configuracion

```text
PLIEGOCHECK_AI_ENABLED=false
OPENAI_API_KEY=
OPENAI_NORMALIZATION_MODEL=gpt-5.5-pro
OPENAI_NORMALIZATION_REASONING_EFFORT=high
OPENAI_NORMALIZATION_BACKGROUND=true
OPENAI_NORMALIZATION_MAX_OUTPUT_TOKENS=16000
OPENAI_NORMALIZATION_TIMEOUT_SECONDS=600
OPENAI_NORMALIZATION_POLL_INTERVAL_SECONDS=5
OPENAI_NORMALIZATION_MAX_CALLS_PER_RUN=50
OPENAI_NORMALIZATION_MAX_SEGMENTS_PER_BATCH=25
OPENAI_NORMALIZATION_MAX_CHARACTERS_PER_BATCH=40000
OPENAI_NORMALIZATION_MAX_TOTAL_CHARACTERS=500000
OPENAI_NORMALIZATION_MAX_RETRIES=3
```

`PLIEGOCHECK_ALLOW_FAKE_NORMALIZATION_PROVIDER=true` solo debe usarse en tests/evals.

## OpenAI

El adapter real usa Responses API con `text.format` de tipo `json_schema`, `strict=true` y sin
tools. Cuando background mode esta deshabilitado se envia `store=false`. Cuando background mode esta
habilitado, el worker crea la respuesta en background y consulta su estado hasta completar o agotar
timeout.

No se suben archivos originales. Cada request contiene solo los segmentos del lote y metadata minima.

## Prompts

Los prompts viven en:

```text
prompts/requirement-normalization/v1/
```

Cada version persistida guarda:

- nombre;
- version semantica;
- `content_sha256`;
- contenido system;
- plantilla user;
- provider;
- estado activo.

## Evidencia

`EvidenceValidator` rechaza:

- segmentos inexistentes;
- segmentos fuera del snapshot;
- citas que no aparecen en el segmento;
- offsets incorrectos;
- ubicacion incompatible.

Un requisito persistido siempre tiene al menos una evidencia `VALID`.

## Comandos

```bash
pnpm normalization:run-once
pnpm normalization:drain -- --max-jobs 10
pnpm normalization:test
pnpm normalization:eval
pnpm normalization:smoke
```

`pnpm normalization:smoke` es manual y opcional. Si no existe `OPENAI_API_KEY` o la IA esta
deshabilitada, termina con estado `skipped` sin fallar la implementacion.

## API

| Endpoint | Uso |
| --- | --- |
| `POST /processes/{process_id}/requirements/normalizations` | Crea una ejecucion asincrona. |
| `GET /processes/{process_id}/requirements/normalizations` | Lista ejecuciones. |
| `GET /processes/{process_id}/requirements/normalizations/{run_id}` | Consulta run, lotes y metricas. |
| `POST /processes/{process_id}/requirements/normalizations/{run_id}/retry` | Reintenta una run fallida. |
| `GET /processes/{process_id}/requirements` | Lista requisitos normalizados. |
| `GET /processes/{process_id}/requirements/{requirement_id}` | Detalle con evidencia y relaciones. |

## Limitaciones

- No hay evaluacion de cumplimiento.
- No hay perfil de empresa.
- No hay OCR.
- No hay embeddings ni vector database.
- No hay decision GO / NO GO.
- Toda salida requiere revision humana.
