# Roadmap incremental - PliegoCheck-SECOP

Fases pequenas, cada una con entregable verificable. Cada microfase termina integrada en `main`
mediante Pull Request, siguiendo [AGENTS.md](../AGENTS.md).

```text
Microfase 0: fundacion documental (completada)
Microfase 1: esqueleto del monorepo (completada)
Microfase 2: importacion manual de proceso y documentos (completada)
Microfase 3: inventario y extraccion documental (completada)
Microfase 4: normalizacion de requisitos (completada)
Microfase 5: perfil de empresa y evidencias (completada)
Microfase 6: evaluador financiero inicial (completada)
Microfase 7: motor deterministico de decision (completada)
Microfase 8: evaluadores especializados juridico, tecnico y de experiencia (completada)
Microfase 9: reporte ejecutivo y paquete de decision (completada)
Microfase 10: endurecimiento operativo, autenticacion y preparacion de piloto
```

## Microfase 0 - Fundacion documental - completada

- **Objetivo:** fijar vision, arquitectura, dominio, contratos y gobernanza antes de escribir codigo.
- **Entregable:** README, AGENTS.md, ADR-001, modelo de dominio, motor de decision, contratos de
  agentes, estandar de prompting, seguridad y roadmap.
- **Fuera de alcance:** codigo funcional.

## Microfase 1 - Esqueleto del monorepo - completada

- **Objetivo:** materializar la estructura del ADR-001 con tooling minimo funcionando.
- **Entregable:** `apps/web`, `apps/api`, `apps/worker`, `packages/schemas`, workspaces pnpm/uv,
  Prettier, ESLint, Ruff, mypy, vitest, pytest y CI.
- **Fuera de alcance:** base de datos, agentes, UI real y autenticacion.

## Microfase 2 - Importacion manual de proceso y documentos - completada

- **Objetivo:** crear un proceso manualmente y adjuntarle documentos de forma inmutable.
- **Entregable:** entidades `Process`, `ProcessDocument` e `ImportEvent`; almacenamiento local;
  API/UI de creacion, listado, carga multiple, inventario inicial y descarga.
- **Fuera de alcance:** extraccion de contenido, datos abiertos y analisis.

## Microfase 3 - Inventario y extraccion documental - completada

- **Objetivo:** extraer contenido documental con trazabilidad y estados explicitos.
- **Entregable:** cola transaccional `document_processing_jobs`, resultados `document_extractions`,
  segmentos `extracted_segments`, endpoints de inventario/reintento/segmentos, UI de inventario y
  preview, y worker deterministico para PDF, DOCX, XLSX, CSV y TXT.
- **Criterios verificados:** documentos soportados producen segmentos navegables; imagenes quedan
  `NEEDS_OCR`; formatos heredados quedan `UNSUPPORTED`; documentos cifrados quedan `ENCRYPTED`; no
  se inventa texto cuando falta evidencia digital.
- **Fuera de alcance:** OCR, normalizacion de requisitos, evaluaciones LLM, `AgentRun`,
  `PromptVersion` y decisiones GO / NO GO.

## Microfase 4 - Normalizacion de requisitos - completada

- **Objetivo:** convertir extracciones en requisitos normalizados trazables.
- **Entregable:** `RequirementNormalizationAgent`, `RequirementConsolidationAgent`, Responses API,
  Structured Outputs validadas, prompts versionados, snapshot reproducible, batching deterministico,
  cola PostgreSQL, validacion de evidencia, candidatos rechazados, relaciones y UI de revision de
  requisitos.
- **Dependencias:** Microfase 3.
- **Criterios verificados:** de un proceso con extracciones se crea una ejecucion auditable; los
  requisitos aceptados tienen evidencia validada; citas inexistentes se rechazan; no se emiten
  decisiones GO / NO GO; provider real queda aislado y probado con mocks; evals sinteticos pasan.
- **Fuera de alcance:** evaluacion de cumplimiento.

## Microfase 5 - Perfil de empresa y evidencias - completada

- **Objetivo:** capturar la capacidad real de la empresa con soporte documental.
- **Entregable:** `CompanyProfile`, datos juridicos, RUP, UNSPSC, periodos y metricas financieras,
  experiencia, personal, certificaciones, capacidades, carga de soportes empresariales reutilizando
  el pipeline documental, vinculos dato-evidencia, completitud deterministica y snapshots
  inmutables.
- **Criterios verificados:** los identificadores se normalizan y enmascaran; las evidencias no
  exponen rutas fisicas; las citas se validan contra extracciones y segmentos; la completitud nunca
  decide cumplimiento; un snapshot publicado conserva digest estable aunque el perfil editable
  cambie.
- **Fuera de alcance:** evaluacion automatica de cumplimiento contra requisitos de un proceso.

## Microfase 6 - Evaluador financiero inicial - completada

- **Objetivo:** primer evaluador vertical completo: requisitos financieros vs. perfil.
- **Entregable:** reglas financieras persistidas, formulas versionadas, resolucion de periodos,
  comparaciones deterministicas contra snapshot publicado, cola PostgreSQL, worker, API, UI,
  revision manual auditada, contratos compartidos, pruebas y evals.
- **Criterios verificados:** los datos declarados sin soporte producen `UNKNOWN`; la evidencia
  conflictiva produce `CONFLICTING_EVIDENCE`; la evaluacion no llama OpenAI ni emite decision global.
- **Fuera de alcance:** los demas evaluadores y decision final.

## Microfase 7 - Motor deterministico de decision

- **Objetivo:** implementar el motor de [decision-engine.md](decision-engine.md).
- **Entregable:** contratos compartidos, politica versionada, hallazgo canonico, adaptador
  financiero, cobertura, reglas, motor puro, cola PostgreSQL, worker, API, UI, acciones, review,
  overrides, pruebas, evals y documentacion.
- **Criterios verificados:** misma entrada + misma version de reglas produce la misma decision; sin
  cobertura obligatoria completa no emite `GO`; categorias sin adaptador quedan `NOT_EVALUATED`.

## Microfase 8 - Evaluadores especializados juridico, tecnico y de experiencia - completada

- **Objetivo:** ampliar la cobertura del motor con evaluadores no financieros.
- **Entregable:** contratos compartidos, tablas especializadas, reglas por requisito, mapeo
  conservador, resolucion contra snapshot publicado, cola PostgreSQL, worker, API, UI, revision
  manual auditada, adaptadores hacia el motor de decision, pruebas y evals.
- **Criterios verificados:** ausencia de evidencia produce `UNKNOWN`; evidencia declarada sin soporte
  no se eleva a cumplimiento; los evaluadores no llaman IA ni producen GO / NO GO; el motor bloquea
  resultados positivos cuando un requisito obligatorio sigue `UNKNOWN` o `NOT_EVALUATED`.

## Microfase 9 - Reporte ejecutivo y paquete de decision

- **Objetivo:** convertir la decision preliminar y sus hallazgos en un paquete revisable para comite
  de licitaciones.
- **Entregable:** reporte ejecutivo, matriz requisito-evidencia-decision, resumen de riesgos,
  acciones pendientes, manifest auditable, ZIP plano, cola PostgreSQL, worker, API, UI, contratos
  compartidos, pruebas y evals.
- **Criterios verificados:** el reporte no recalcula la decision, no inventa `GO`, escapa HTML,
  produce hashes estables y entradas ZIP seguras, y reutiliza paquetes completados por input digest.

## Microfase 10 - Endurecimiento operativo, autenticacion y preparacion de piloto

- **Objetivo:** operacion multiusuario y multiorganizacion segura.
- **Entregable previsto:** autenticacion, roles, aislamiento por organizacion, limites de costo,
  observabilidad, storage S3-compatible, preparacion de piloto y despliegue reproducible.

## Despues del MVP

Evaluadores restantes a profundidad, busqueda semantica si un caso la justifica, alertas de nuevos
procesos por perfil y analisis de competencia.
