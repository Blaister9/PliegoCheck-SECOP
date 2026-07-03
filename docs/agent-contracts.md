# Contratos de agentes — PliegoCheck-SECOP

Define la responsabilidad, entradas, salidas y límites de cada agente de IA de la plataforma. Los prompts que implementan estos contratos siguen el [estándar de prompting](agent-prompting-standard.md). Las entidades referenciadas están en [domain-model.md](domain-model.md).

> **El motor de decisión NO es un agente LLM.** Es un servicio determinístico ([decision-engine.md](decision-engine.md)). Ningún contrato de esta lista incluye la facultad de emitir la decisión final.

## Principios transversales

1. Un agente no debe realizar funciones de los demás: responsabilidad única.
2. El orquestador coordina, pero no sustituye a los especialistas.
3. Los evaluadores no modifican el texto extraído.
4. El extractor no determina cumplimiento.
5. El explicador no cambia la decisión.
6. Toda afirmación relevante apunta a evidencia (documento, página, sección).
7. Cada ejecución almacena versión de prompt, modelo y entradas (`AgentRun`).
8. Una salida que no valida contra su esquema **se rechaza**; nunca se interpreta libremente. Se reintenta con límite o se escala.
9. Lo desconocido se marca `UNKNOWN`; nunca se inventa.

Errores esperados comunes a todos: salida inválida contra esquema, timeout del modelo, límite de tokens excedido, entrada incompleta. En todos los casos: registrar en `AgentRun`, reintentar dentro del límite configurado o escalar; nunca degradar silenciosamente.

---

## 1. OrchestratorAgent

- **Responsabilidad única:** coordinar la secuencia de agentes para un análisis, gestionar reintentos y consolidar el estado del pipeline.
- **Entradas:** identificador de `ProcessVersion`, identificador de `CompanyProfile`, configuración del análisis.
- **Salidas:** plan de ejecución, estado de cada etapa, referencias a los `AgentRun` producidos.
- **Herramientas permitidas:** invocación de los demás agentes, consulta de estado del pipeline, encolado de trabajos.
- **Datos prohibidos:** contenido documental crudo (no lo necesita; coordina por referencias), credenciales, datos de otras organizaciones.
- **Condiciones de parada:** todas las etapas completadas, o etapa crítica fallida tras agotar reintentos, o escalamiento humano emitido.
- **Errores esperados:** agente subordinado fallido, dependencias incompletas, presupuesto de tokens agotado.
- **Escala a revisión humana cuando:** una etapa crítica falla repetidamente o el pipeline queda en estado inconsistente.
- **Qué no debe decidir:** el resultado GO/NO GO; el contenido de ninguna evaluación; el estado de ningún requisito.

```json
{
  "process_version_id": "PV-001",
  "company_profile_id": "CP-001",
  "pipeline_status": "COMPLETED | FAILED | ESCALATED | IN_PROGRESS",
  "stages": [
    {"agent": "DocumentExtractionAgent", "status": "COMPLETED", "agent_run_id": "AR-010"}
  ],
  "escalations": [],
  "errors": []
}
```

## 2. SecopIngestionAgent

- **Responsabilidad única:** registrar un proceso desde datos abiertos de Colombia Compra Eficiente o desde carga manual, creando `Process`/`ProcessVersion` con metadatos trazables.
- **Entradas:** identificador SECOP o conjunto de archivos cargados manualmente.
- **Salidas:** `Process` y `ProcessVersion` creados, metadatos del proceso con fuente de origen por campo.
- **Herramientas permitidas:** API de datos abiertos, almacenamiento de documentos, registro en base de datos.
- **Datos prohibidos:** datos de la plataforma transaccional de SECOP II vía scraping; datos de otros tenants.
- **Condiciones de parada:** proceso registrado con sus metadatos, o fuente inaccesible tras reintentos.
- **Errores esperados:** proceso no encontrado en datos abiertos, respuesta incompleta de la API, archivo corrupto.
- **Escala a revisión humana cuando:** los metadatos de datos abiertos contradicen los documentos cargados.
- **Qué no debe decidir:** qué documentos son relevantes para el análisis; ningún juicio sobre el contenido.

```json
{
  "process_id": "PR-001",
  "process_version_id": "PV-001",
  "source": "OPEN_DATA | MANUAL_UPLOAD",
  "metadata": {"secop_id": "...", "entity": "...", "budget": null},
  "field_sources": [{"field": "budget", "source": "OPEN_DATA", "retrieved_at": "..."}],
  "warnings": []
}
```

## 3. DocumentInventoryAgent

- **Responsabilidad única:** inventariar y clasificar los documentos de una `ProcessVersion` (pliego, anexos, formatos, adendas, estudios previos) y detectar faltantes evidentes.
- **Entradas:** `ProcessDocument`s de la versión.
- **Salidas:** inventario clasificado con confianza por clasificación, lista de documentos posiblemente faltantes.
- **Herramientas permitidas:** lectura de metadatos y primeras páginas de documentos almacenados.
- **Datos prohibidos:** documentos de otros procesos u organizaciones.
- **Condiciones de parada:** todos los documentos clasificados o marcados como no clasificables.
- **Errores esperados:** documento ilegible, formato no soportado, documento duplicado.
- **Escala a revisión humana cuando:** el pliego principal no es identificable o el inventario sugiere que faltan documentos esenciales.
- **Qué no debe decidir:** el contenido de los requisitos; si el proceso es viable.

```json
{
  "process_version_id": "PV-001",
  "inventory": [
    {"document_id": "DOC-001", "type": "PLIEGO | ANEXO | ADENDA | FORMATO | ESTUDIO_PREVIO | OTRO",
     "confidence": 0.0, "notes": ""}
  ],
  "possibly_missing": ["..."],
  "unclassifiable": []
}
```

## 4. DocumentExtractionAgent

- **Responsabilidad única:** extraer el contenido (texto, tablas, estructura) de cada `ProcessDocument`, produciendo `DocumentExtraction`s con calidad medida.
- **Entradas:** `ProcessDocument` (PDF, DOCX, XLSX, imagen).
- **Salidas:** contenido estructurado por página/sección, método usado (texto nativo u OCR), métricas de calidad, páginas fallidas.
- **Herramientas permitidas:** librerías de extracción y OCR, lectura del almacenamiento documental.
- **Datos prohibidos:** contenido inventado para páginas ilegibles; texto de otros documentos.
- **Condiciones de parada:** documento completamente procesado o marcado parcialmente extraíble con detalle de fallos.
- **Errores esperados:** PDF escaneado de baja calidad, documento protegido, tablas complejas mal reconocidas.
- **Escala a revisión humana cuando:** la calidad de extracción del pliego principal cae por debajo del umbral configurado.
- **Qué no debe decidir:** qué es un requisito; ningún cumplimiento. **El extractor no determina cumplimiento.**

```json
{
  "document_id": "DOC-001",
  "method": "NATIVE_TEXT | OCR | MIXED",
  "pages": [{"page": 1, "content": "...", "quality": 0.0}],
  "failed_pages": [],
  "tables": [],
  "overall_quality": 0.0
}
```

## 5. RequirementNormalizationAgent

- **Responsabilidad única:** convertir el contenido extraido en candidatos de
  `Requirement` normalizados, con evidencia exacta (documento, extraccion,
  segmento, pagina/seccion y cita literal).
- **Entradas:** snapshot inmutable de `ProcessDocument`, `DocumentExtraction` y
  `DocumentExtractionSegment`; taxonomia de categorias de
  [domain-model.md](domain-model.md).
- **Salidas:** candidatos de requisitos con categoria, alcance, modalidad,
  condicion, valor esperado, criticidad, subsanabilidad, confianza y evidencia
  citada. La salida debe validar contra
  `RequirementNormalizationAgentOutput`.
- **Herramientas permitidas:** lectura de extracciones; consulta de la taxonomía de categorías.
- **Datos prohibidos:** requisitos no presentes en los documentos; umbrales de otros procesos; valores esperados no escritos en el pliego.
- **Condiciones de parada:** todo el contenido relevante recorrido y cada candidato
  con evidencia minima o rechazo explicito por insuficiencia de evidencia.
- **Errores esperados:** requisitos duplicados entre documentos, redacción ambigua, referencias cruzadas rotas en el pliego.
- **Escala a revisión humana cuando:** requisitos contradictorios entre pliego y adendas, o subsanabilidad indeterminable en requisitos bloqueantes.
- **Qué no debe decidir:** cumplimiento, valor de empresa, `GO`, `NO_GO`,
  decision final, ni subsanabilidad no explicita (queda `UNKNOWN`).

```json
{
  "batch_id": "BATCH-001",
  "candidates": [
    {
      "candidate_id": "CAND-001",
      "category": "FINANCIAL",
      "scope": "ORGANIZATION",
      "modality": "REQUIREMENT",
      "requirement_text": "El proponente debe acreditar liquidez mayor o igual a 1.2.",
      "condition_text": null,
      "expected_value": {
        "raw_value": "1.2",
        "normalized_number": 1.2,
        "unit": "ratio",
        "comparator": ">="
      },
      "requirement_basis": "EXPLICIT",
      "criticality": "REQUIRES_REVIEW",
      "subsanability": "UNKNOWN",
      "confidence": 0.82,
      "evidence": [
        {
          "role": "PRIMARY",
          "document_id": "DOC-001",
          "extraction_id": "EXT-001",
          "segment_id": "SEG-001",
          "quote": "liquidez mayor o igual a 1.2",
          "source_location": {"page": 12, "section": "3.2"}
        }
      ]
    }
  ],
  "rejected_candidates": []
}
```

## 5.1 RequirementConsolidationAgent

- **Responsabilidad unica:** analizar requisitos ya validados y proponer relaciones de duplicidad,
  conflicto o adenda potencial.
- **Entradas:** candidatos/requisitos aceptados por `EvidenceValidator`, con evidencia minima.
- **Salidas:** relaciones `INDEPENDENT`, `EXACT_DUPLICATE`, `POTENTIAL_DUPLICATE`,
  `POTENTIAL_CONFLICT` o `POTENTIAL_AMENDMENT`.
- **Herramientas permitidas:** ninguna.
- **Datos prohibidos:** crear requisitos nuevos, eliminar evidencia, resolver juridicamente una
  adenda, decidir que requisito gana o emitir cumplimiento.
- **Condiciones de parada:** todos los candidatos recibidos comparados.
- **Escala a revision humana cuando:** la relacion sea potencial, haya conflicto documental o exista
  ambiguedad.

## 5.2 EvidenceValidator

No es un agente LLM. Es un componente deterministico que resuelve `segment_id`, verifica pertenencia
al snapshot, valida cita, offsets y ubicacion, y rechaza candidatos sin soporte como
`REJECTED_UNSUPPORTED`. No interpreta juridicamente el contenido ni decide cumplimiento.

## 5.3 FinancialEvaluationEngine

No es un agente LLM. En Microfase 6 reemplaza al futuro evaluador financiero LLM para el primer
vertical financiero. Lee requisitos `FINANCIAL`, reglas financieras persistidas y un
`CompanyProfileSnapshot` publicado; produce resultados por requisito con formulas versionadas,
periodo resuelto, metricas usadas, evidencia y codigo de explicacion. No llama OpenAI, no modifica
requisitos y no emite decision global.

## 6–11. Agentes evaluadores especializados

Los seis evaluadores comparten estructura de contrato; se listan sus diferencias tras el contrato común.

**Contrato común**

- **Responsabilidad única:** contrastar los `Requirement`s de su categoría contra el `CompanyProfile` y sus `CompanyCapability`s y evidencias, proponiendo `status` por requisito **siempre con evidencia citada**.
- **Entradas:** requisitos normalizados de su categoría, perfil de empresa, evidencias disponibles.
- **Salidas:** `Evaluation` con estados propuestos, `Finding`s y evidencia citada por requisito.
- **Herramientas permitidas:** lectura de requisitos, perfil y evidencias; cálculos aritméticos deterministas (p. ej. comparar índices).
- **Datos prohibidos:** modificar el texto extraído; usar valores de empresa sin soporte documental; conocimiento externo no citado como si fuera evidencia del expediente.
- **Condiciones de parada:** todos los requisitos de su categoría con `status` asignado (incluido `UNKNOWN`) y evidencia o ausencia registrada.
- **Errores esperados:** evidencia vencida, valores no comparables (unidades distintas), información de empresa desactualizada.
- **Escalan a revisión humana cuando:** evidencia contradictoria (`CONFLICTING_EVIDENCE`), ambigüedad jurídica del requisito, o evidencia crítica con validez dudosa.
- **Qué no deben decidir:** la decisión final GO/NO GO; requisitos de otras categorías; reescribir o reinterpretar el requisito extraído.

```json
{
  "evaluation_type": "LEGAL | FINANCIAL | EXPERIENCE | TECHNICAL | OPERATIONAL | ECONOMIC",
  "process_version_id": "PV-001",
  "company_profile_id": "CP-001",
  "requirement_assessments": [
    {
      "requirement_id": "REQ-001",
      "status": "COMPLIES | DOES_NOT_COMPLY | PARTIAL | UNKNOWN | NOT_APPLICABLE | CONFLICTING_EVIDENCE",
      "company_value": null,
      "evidence_ids": ["EV-001"],
      "reasoning": "Comparación explícita valor exigido vs. valor acreditado",
      "confidence": 0.0,
      "requires_human_review": false
    }
  ],
  "findings": [
    {"type": "GAP | RISK | CONFLICT | MISSING_DATA", "severity": "BLOCKING | HIGH | MEDIUM | LOW",
     "requirement_id": "REQ-001", "description": "...", "evidence_ids": []}
  ]
}
```

**Especializaciones**

| Agente | Categorías que evalúa | Notas específicas |
| --- | --- | --- |
| **LegalEvaluationAgent** | Jurídicos, riesgos e inhabilidades, garantías, documentales | Nunca afirma certeza jurídica; las interpretaciones normativas siempre marcan `requires_human_review`. |
| **FinancialEvaluationAgent** | Financieros, organizacionales | Compara indicadores del pliego contra estados financieros soportados; los cálculos derivados citan sus operandos. |
| **ExperienceEvaluationAgent** | Experiencia (contratos, montos, códigos UNSPSC) | Valida coincidencia de códigos UNSPSC y suficiencia de montos solo con certificaciones soportadas. |
| **TechnicalEvaluationAgent** | Técnicos, equipo de trabajo | Contrasta especificaciones y perfiles exigidos contra capacidades documentadas. |
| **OperationalEvaluationAgent** | Operativos, cronograma | Evalúa capacidad instalada, cobertura y compatibilidad del cronograma con la operación. |
| **EconomicEvaluationAgent** | Económicos | Analiza presupuesto, forma de pago y estructura de costos frente a la viabilidad económica declarada; no fija precios de oferta. |

## 12. EvidenceVerificationAgent

- **Responsabilidad única:** verificar que cada `status` propuesto por los evaluadores esté respaldado por evidencia existente, vigente y coherente; detectar conflictos y degradar estados sin soporte.
- **Entradas:** `Evaluation`s de todos los evaluadores, evidencias referenciadas.
- **Salidas:** informe de verificación por requisito: evidencia confirmada, evidencia faltante, conflictos detectados, estados degradados a `UNKNOWN` o `CONFLICTING_EVIDENCE`.
- **Herramientas permitidas:** lectura de evaluaciones, evidencias y documentos referenciados.
- **Datos prohibidos:** crear evidencia; modificar el contenido de las evaluaciones más allá de degradar estados sin soporte.
- **Condiciones de parada:** todos los estados propuestos verificados.
- **Errores esperados:** referencias a evidencias inexistentes, evidencia vencida, citas que no corresponden al contenido citado.
- **Escala a revisión humana cuando:** detecta evidencia contradictoria o citas falsas (posible alucinación de un evaluador).
- **Qué no debe decidir:** la decisión final; el contenido de las evaluaciones (solo su respaldo).

```json
{
  "process_version_id": "PV-001",
  "verifications": [
    {"requirement_id": "REQ-001", "original_status": "COMPLIES",
     "verified_status": "COMPLIES | UNKNOWN | CONFLICTING_EVIDENCE",
     "evidence_check": "CONFIRMED | MISSING | INVALID | EXPIRED | CONTRADICTORY",
     "notes": ""}
  ],
  "conflicts": [],
  "hallucination_suspects": []
}
```

## 13. DecisionExplanationAgent

- **Responsabilidad única:** redactar la explicación auditable de una `Decision` **ya emitida** por el motor determinístico, en lenguaje claro y con citas a la evidencia determinante.
- **Entradas:** `Decision` con sus requisitos determinantes, evidencias y versión de reglas.
- **Salidas:** explicación estructurada: resultado, factores determinantes con citas, condiciones o capacidades a complementar, limitaciones de la evidencia.
- **Herramientas permitidas:** lectura de la decisión, requisitos y evidencias referenciadas.
- **Datos prohibidos:** información no presente en la decisión y sus referencias; juicios adicionales propios.
- **Condiciones de parada:** explicación completa que cubre todos los factores determinantes.
- **Errores esperados:** decisión con referencias incompletas.
- **Escala a revisión humana cuando:** los factores determinantes no permiten construir una explicación coherente (señal de inconsistencia aguas arriba).
- **Qué no debe decidir:** **no cambia la decisión**, no añade ni quita factores, no matiza el resultado.

```json
{
  "decision_id": "DE-001",
  "result": "GO | GO_CONDICIONADO | BUSCAR_ALIADO | NO_GO | NO_CARGAR | PENDIENTE_INFORMACION",
  "summary": "Explicación en lenguaje claro",
  "determining_factors": [
    {"requirement_id": "REQ-001", "explanation": "...", "evidence_ids": ["EV-001"],
     "source_citation": {"document_id": "DOC-001", "page": 12, "section": "3.2"}}
  ],
  "conditions": [],
  "limitations": ["Evidencia financiera con corte a ..."]
}
```

---

## Matriz de separación de responsabilidades

| Capacidad | Único autorizado |
| --- | --- |
| Coordinar el pipeline | OrchestratorAgent |
| Registrar procesos y fuentes | SecopIngestionAgent |
| Clasificar documentos | DocumentInventoryAgent |
| Extraer contenido | DocumentExtractionAgent |
| Normalizar requisitos | RequirementNormalizationAgent |
| Proponer duplicados/conflictos de requisitos | RequirementConsolidationAgent |
| Validar citas de requisitos normalizados | EvidenceValidator (deterministico) |
| Proponer cumplimiento por categoría | Evaluadores especializados (6–11) |
| Verificar respaldo de evidencia | EvidenceVerificationAgent |
| **Emitir la decisión final** | **Motor determinístico (no LLM)** |
| Explicar la decisión | DecisionExplanationAgent |
