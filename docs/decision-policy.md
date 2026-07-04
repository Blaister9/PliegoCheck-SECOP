# Politica de decision

La politica activa esta en `config/decision-policies/v1/policy.json` y se valida con Pydantic antes
de usarse. No es un lenguaje dinamico: no se permite `eval`, `exec`, SQL dinamico ni expresiones de
politica ejecutables.

## Versionado

Cada `DecisionRun` referencia un `DecisionPolicyVersion` con:

- `policy_name`
- `semantic_version`
- `content_sha256`
- `policy_payload`
- `engine_version`
- `created_at`
- `is_active`

Si el contenido cambia sin cambiar la version semantica, la API rechaza la politica con
`DECISION_POLICY_INVALID`.

## Precedencia

La politica no distingue si un hallazgo proviene del evaluador financiero o de un evaluador
especializado. Una vez adaptado a `DecisionInputFinding`, `UNKNOWN`, `NOT_EVALUATED`,
`CONFLICTING_EVIDENCE`, incumplimientos obligatorios y revisiones humanas pendientes se tratan con
las mismas reglas de precedencia.

La precedencia de `pliegocheck-default` 1.0.0 es:

1. `NO_CARGAR`
2. `NO_GO`
3. `PENDIENTE_INFORMACION`
4. `BUSCAR_ALIADO`
5. `GO_CONDICIONADO`
6. `GO`

El motor toma la sugerencia de mayor precedencia entre reglas disparadas. Si no hay sugerencias y se
cumplen los prerequisitos de cobertura total y cumplimiento obligatorio, produce `GO`; en cualquier
otro caso conserva `PENDIENTE_INFORMACION`.

## Digest e idempotencia

El manifiesto de entrada incluye proceso, normalizacion, snapshot de empresa, evaluacion financiera,
requisitos, hash de politica y version de motor. `effective_at` se persiste, pero se excluye del
digest de idempotencia para evitar que el reloj cree duplicados arbitrarios. `force=true` crea un
nuevo run y conserva el historico.

## Reportes

Los reportes de Microfase 9 tienen su propio input manifest y digest. Ese digest resume la decision
ya persistida, reviews, acciones, evaluadores y templates; no reemplaza ni reinterpreta el digest de
la `DecisionRun`.
