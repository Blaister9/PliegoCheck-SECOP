# Evaluacion financiera inicial

La evaluacion financiera compara requisitos financieros normalizados contra un snapshot publicado de
empresa. Es un evaluador especializado por requisito; no decide participacion global.

## Flujo

1. Completar una normalizacion de requisitos.
2. Publicar un snapshot de empresa.
3. Crear una evaluacion:

```bash
curl -X POST http://localhost:8000/processes/{process_id}/financial-evaluations \
  -H "Content-Type: application/json" \
  -d '{
    "normalization_run_id": "...",
    "company_id": "...",
    "company_profile_snapshot_id": "...",
    "force": false
  }'
```

4. Procesar la cola:

```bash
pnpm financial:run-once
pnpm financial:drain -- --max-jobs 10
```

5. Consultar resultados:

```bash
curl http://localhost:8000/processes/{process_id}/financial-evaluations/{run_id}
curl http://localhost:8000/processes/{process_id}/financial-evaluations/{run_id}/results
```

## Estados por requisito

| Estado | Uso |
| --- | --- |
| `COMPLIES` | La metrica soportada o verificada satisface la regla. |
| `DOES_NOT_COMPLY` | La metrica soportada o verificada no satisface la regla. |
| `UNKNOWN` | Falta evidencia, falta metrica, hay ambiguedad, unidad/moneda no coinciden o hay division por cero. |
| `CONFLICTING_EVIDENCE` | Existe evidencia o insumo contradictorio. |
| `NOT_APPLICABLE` | Reservado para reglas no aplicables futuras. |
| `PARTIAL` | Reservado para reglas compuestas futuras. |

## Regla de evidencia

La evidencia declarada sin soporte no se convierte en cumplimiento. Si una metrica esta `SUPPORTED`
pero no `VERIFIED`, el resultado comparativo queda marcado con `requires_human_review=true`.

## Revision manual

La revision se registra con:

```bash
curl -X POST http://localhost:8000/processes/{process_id}/financial-evaluations/{run_id}/results/{result_id}/review \
  -H "Content-Type: application/json" \
  -d '{
    "review_status": "OVERRIDDEN",
    "override_result": "UNKNOWN",
    "override_reason": "Evidencia insuficiente."
  }'
```

El override no cambia `status`; conserva `reviewed_status`, motivo, revisor y fecha.

## Web

El detalle de proceso incluye una seccion "Evaluacion financiera" para seleccionar normalizacion,
empresa y snapshot publicado. La misma vista muestra historial de ejecuciones y resultados por
requisito.

## Limites

- No hay decision global `GO / NO GO`.
- No hay llamadas a OpenAI durante la evaluacion financiera.
- El mapeo de reglas es conservador y deja `UNKNOWN` cuando el requisito no es claro.
- En Microfase 7 estos resultados alimentan el adaptador financiero del motor de decision
  preliminar. El adaptador transforma estados y overrides sin reinterpretar calculos, sin inventar
  subsanabilidad y sin marcar brechas como aliables.
- Los demas evaluadores quedan fuera de esta microfase.
