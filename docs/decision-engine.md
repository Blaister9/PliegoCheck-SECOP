# Motor determinístico de decisión

Especificación conceptual del componente que produce la decisión final GO / NO GO. **No es un agente LLM**: es un servicio determinístico con reglas versionadas, independiente de los modelos de IA.

## Principio rector

El LLM **no asigna directamente el resultado final**. Los agentes extraen, normalizan y proponen estados de cumplimiento con evidencia; el motor determinístico combina esos estados mediante reglas verificables y versionadas, y produce la decisión. Dos ejecuciones con las mismas entradas y la misma versión de reglas producen la misma decisión.

## Entrada del motor: requisitos normalizados

Cada requisito normalizado que llega al motor debe contener, como mínimo:

> Nota Microfase 4: la normalizacion actual solo persiste requisitos del proceso con evidencia del
> pliego. No produce `status` de cumplimiento empresarial, `company_value` ni decisiones. Esos campos
> pertenecen a microfases posteriores de evaluacion contra perfil de empresa.

```json
{
  "requirement_id": "REQ-001",
  "category": "FINANCIAL",
  "description": "Texto normalizado del requisito",
  "source_document_id": "DOC-001",
  "source_location": {
    "page": 12,
    "section": "3.2"
  },
  "criticality": "BLOCKING",
  "subsanability": "UNKNOWN",
  "expected_value": null,
  "company_value": null,
  "status": "UNKNOWN",
  "evidence_ids": [],
  "confidence": 0,
  "requires_human_review": true
}
```

Campos clave:

- `source_document_id` + `source_location`: todo requisito es trazable a documento, página y sección. Un requisito sin origen no entra al motor.
- `expected_value` / `company_value`: valores comparables cuando el requisito es cuantitativo; `null` cuando no aplica o no se conoce.
- `evidence_ids`: evidencias (`RequirementEvidence`) que respaldan el `status`. Un `status` distinto de `UNKNOWN` sin evidencia es inválido.
- `confidence`: confianza del agente evaluador (0–1). **Informativa, nunca sustituye evidencia.**
- `requires_human_review`: bandera que obliga revisión humana antes de decisión definitiva.

## Vocabularios

### Estados de requisito (`status`)

```text
COMPLIES              → cumple, con evidencia
DOES_NOT_COMPLY       → no cumple, con evidencia
PARTIAL               → cumple parcialmente
UNKNOWN               → no hay evidencia suficiente para determinar
NOT_APPLICABLE        → no aplica a este oferente/proceso
CONFLICTING_EVIDENCE  → evidencias contradictorias entre sí
```

### Criticidad (`criticality`)

```text
BLOCKING       → su incumplimiento impide participar o gana el rechazo de la oferta
HIGH           → afecta gravemente la viabilidad
MEDIUM         → relevante pero gestionable
LOW            → menor
INFORMATIONAL  → contexto, sin efecto en la decisión
```

### Subsanabilidad (`subsanability`)

```text
SUBSANABLE      → corregible dentro del proceso según el pliego
NON_SUBSANABLE  → no corregible; su incumplimiento es definitivo
CONDITIONAL     → subsanable bajo condiciones definidas en el pliego
UNKNOWN         → el pliego no permite determinarlo con certeza
```

> La subsanabilidad real la define cada pliego y la normativa aplicable al proceso. El sistema registra lo que el pliego dice; cuando no es determinable, queda `UNKNOWN` y escala a revisión humana. Nunca se asume.

## Reglas iniciales

Las siguientes reglas son **principios de diseño del motor, no interpretación jurídica definitiva**. Cada proceso puede modularlas según su pliego, y toda regla aplicada queda registrada con su versión.

| # | Regla | Resultado posible |
| --- | --- | --- |
| R1 | Un requisito `BLOCKING` con `status = DOES_NOT_COMPLY` puede producir | `NO_GO` |
| R2 | Un requisito `BLOCKING` con `status = DOES_NOT_COMPLY` y `subsanability = NON_SUBSANABLE` puede producir | `NO_CARGAR` |
| R3 | Ausencia de evidencia crítica (`BLOCKING`/`HIGH` con `status = UNKNOWN`) produce | `PENDIENTE_INFORMACION`, nunca `GO` |
| R4 | Una capacidad insuficiente pero complementable mediante tercero (consorcio, unión temporal, aliado) puede producir | `BUSCAR_ALIADO` |
| R5 | Pendientes `SUBSANABLE` con plan, responsable y fecha definidos pueden producir | `GO_CONDICIONADO` |
| R6 | `GO` exige: ningún bloqueo conocido **y** evidencia suficiente en todos los requisitos `BLOCKING` y `HIGH` | `GO` |
| R7 | Cualquier requisito con `status = CONFLICTING_EVIDENCE` obliga revisión humana antes de decisión definitiva | bloqueo hasta `HumanReview` |
| R8 | La confianza (`confidence`) del modelo no reemplaza la evidencia: un `COMPLIES` sin `evidence_ids` se degrada a `UNKNOWN` | saneamiento de entrada |
| R9 | Toda decisión almacena la versión exacta de reglas (`DecisionRule`) y de prompts/modelos (`AgentRun`/`PromptVersion`) usados | trazabilidad |

Precedencia conceptual: `NO_CARGAR` > `NO_GO` > `PENDIENTE_INFORMACION` > `BUSCAR_ALIADO` > `GO_CONDICIONADO` > `GO`. La revisión humana (R7) suspende la emisión de la decisión definitiva, no altera la precedencia.

## Flujo del motor (pseudocódigo conceptual)

No es código ejecutable; es la especificación del comportamiento.

```text
función decidir(requisitos, versión_reglas):

    # 1. Saneamiento de entrada (R8)
    para cada r en requisitos:
        si r.status == COMPLIES y r.evidence_ids está vacío:
            r.status = UNKNOWN
            r.requires_human_review = verdadero
        si r.source_document_id es nulo:
            rechazar r          # un requisito sin origen no entra al motor

    # 2. Revisión humana obligatoria (R7)
    conflictos = requisitos donde status == CONFLICTING_EVIDENCE
    pendientes_revision = requisitos donde requires_human_review y sin HumanReview resuelta
    si conflictos o pendientes_revision no están vacíos:
        retornar DecisiónSuspendida(motivo = revisión humana pendiente,
                                    requisitos = conflictos + pendientes_revision)

    # 3. Causales insubsanables (R2)
    si existe r con criticality == BLOCKING
             y status == DOES_NOT_COMPLY
             y subsanability == NON_SUBSANABLE:
        retornar Decisión(NO_CARGAR, determinantes = esos r, versión_reglas)

    # 4. Incumplimientos bloqueantes (R1, R4)
    bloqueantes_incumplidos = r donde criticality == BLOCKING y status == DOES_NOT_COMPLY
    si bloqueantes_incumplidos no está vacío:
        si todos son complementables_por_tercero(r):        # capacidad financiera,
            retornar Decisión(BUSCAR_ALIADO, ...)            # experiencia o técnica
        retornar Decisión(NO_GO, determinantes = bloqueantes_incumplidos, versión_reglas)

    # 5. Evidencia crítica faltante (R3)
    criticos_desconocidos = r donde criticality en {BLOCKING, HIGH} y status == UNKNOWN
    si criticos_desconocidos no está vacío:
        retornar Decisión(PENDIENTE_INFORMACION, faltantes = criticos_desconocidos, ...)

    # 6. Pendientes subsanables (R5)
    subsanables_pendientes = r donde status en {PARTIAL, DOES_NOT_COMPLY}
                                y subsanability en {SUBSANABLE, CONDITIONAL}
    si subsanables_pendientes no está vacío:
        si cada uno tiene plan, responsable y fecha:
            retornar Decisión(GO_CONDICIONADO, condiciones = subsanables_pendientes, ...)
        retornar Decisión(PENDIENTE_INFORMACION, ...)   # sin plan no hay condicional

    # 7. GO (R6)
    retornar Decisión(GO, evidencia = resumen_evidencias(requisitos), versión_reglas)
```

## Salida del motor

Toda decisión emitida incluye:

- Resultado (`GO` … `PENDIENTE_INFORMACION`).
- Requisitos determinantes con sus evidencias.
- Condiciones y plan (cuando aplique `GO_CONDICIONADO`).
- Capacidades a complementar (cuando aplique `BUSCAR_ALIADO`).
- Versión de reglas (`DecisionRule`), versiones de prompts y modelos (`PromptVersion`, `AgentRun`).
- Estado de revisión humana.

Con esto, cualquier decisión es reproducible y auditable: misma entrada + misma versión de reglas ⇒ misma salida.

## Relación con los agentes

Los agentes descritos en [agent-contracts.md](agent-contracts.md) alimentan el motor pero no lo sustituyen. El `DecisionExplanationAgent` redacta la explicación de la decisión ya tomada; **no puede cambiarla**.
