# Roadmap incremental - PliegoCheck-SECOP

Estado vigente: Microfases 16, 17, 18, 19, 20, 21 y 22 completadas.

```text
Microfase 16 — completada
Microfase 17 — completada
Microfase 18 — completada
Microfase 19 — completada
Microfase 20 — completada
Microfase 21 — completada
Microfase 22 — completada
```

Siguiente según gate: Microfase 23 — Despliegue institucional restringido y validación con usuarios autorizados.

Fases pequenas, cada una con entregable verificable. Cada microfase termina integrada en `main`
mediante Pull Request, siguiendo [AGENTS.md](../AGENTS.md).

```text
Microfase 0: completada - fundacion documental
Microfase 1: completada - esqueleto del monorepo
Microfase 2: completada - importacion manual de proceso y documentos
Microfase 3: completada - inventario y extraccion documental
Microfase 4: completada - normalizacion de requisitos
Microfase 5: completada - perfil de empresa y evidencias
Microfase 6: completada - evaluador financiero inicial
Microfase 7: completada - motor deterministico de decision
Microfase 8: completada - evaluadores especializados juridico, tecnico y de experiencia
Microfase 9: completada - reporte ejecutivo y paquete de decision
Microfase 10: completada - endurecimiento operativo, autenticacion y preparacion de piloto
Microfase 11: completada - piloto controlado end-to-end con datos sinteticos y retroalimentacion
Microfase 12: completada - ajustes post-piloto y preparacion de despliegue controlado
Microfase 13: completada - despliegue controlado y validacion con usuarios piloto
Microfase 14: completada - ajustes derivados de usuarios piloto y cierre de MVP controlado
Microfase 15: pendiente de decisión humana - evolución a piloto real o pausa técnica
Microfase 16: completada - conector SECOP de búsqueda e importación
Microfase 17: completada - descarga controlada de documentos públicos y actualización incremental
Microfase 18: completada - bandeja priorizada de oportunidades compatibles
Microfase 19: completada - monitoreo periódico y alertas de nuevas oportunidades
Microfase 20: completada - entrega externa configurable de alertas y operación piloto sintético
Microfase 21: completada - piloto técnico supervisado y cierre de brechas operativas verificables
Microfase 22: completada - preparación para despliegue institucional restringido
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
- **Entregable:** autenticacion local, roles, permisos, sesiones HttpOnly, proteccion API/web,
  auditoria operacional, configuracion validada, headers, readiness, backup local, pantallas admin,
  eval de piloto, pruebas, CI y documentacion.

## Microfase 11 - Piloto controlado end-to-end con datos sinteticos y retroalimentacion - completada

- **Objetivo:** ejecutar un piloto completo con datos sinteticos y feedback de uso.
- **Entregable:** dataset sintetico (`pilot/`), comandos `pnpm pilot:prepare|run|reset|readiness`,
  eval end-to-end con auth (`evals/pilot-end-to-end`), guion de demo y checklist
  ([docs/demo-script.md](demo-script.md), [docs/pilot-demo-checklist.md](pilot-demo-checklist.md)),
  registro de retroalimentacion ([docs/pilot-feedback-log.md](pilot-feedback-log.md)),
  contratos de piloto (`PilotRunSummary`, `PilotReadiness`, ...) y
  [ADR-011](ADR-011-controlled-pilot.md). Resultado honesto del dataset:
  `PENDIENTE_INFORMACION` (no forzado a GO).

## Microfase 12 - Ajustes post-piloto y preparacion de despliegue controlado - completada

- **Objetivo:** incorporar la retroalimentacion del piloto y endurecer el despliegue.
- **Entregable:** hallazgos post-piloto clasificados, `deployment:eval`, `deployment:backup-check`,
  perfiles `.env` local/piloto, checklist de navegador, runbook de despliegue controlado,
  checklists pre/post despliegue, rollback, observabilidad local y release candidate documentada.

## Microfase 13 - Despliegue controlado y validacion con usuarios piloto - completada

- **Objetivo:** convertir la preparacion de despliegue en un flujo reproducible, validable por
  usuarios piloto y cubierto por evals.
- **Entregable:** `compose.pilot.yaml`, scripts `controlled:deploy|validate|stop|reset`, eval
  `controlled:eval`, data scan `controlled:data-scan`, kit `pilot/user-validation/`, checklist de
  readiness, matriz de hallazgos, acta plantilla, guia de observacion, runbooks actualizados y
  release candidate `0.13.0-rc.1`.
- **Criterios verificados:** health, auth, worker, DB, storage, dataset piloto, reporte ZIP,
  auditoria, backup manifest, no secretos, no datos reales y documentacion de rollback.
- **Fuera de alcance:** despliegue productivo real, SSO, MFA, S3 real obligatorio, OCR, PDF, firma
  digital, SECOP, nuevos evaluadores y nuevas reglas de decision.

## Microfase 14 - Ajustes derivados de usuarios piloto y cierre de MVP controlado - completada

- **Objetivo:** consolidar hallazgos, cerrar el MVP controlado y dejar explicitos criterios de
  aceptacion, limitaciones, no produccion y demo final.
- **Entregable:** ADR-014, hallazgos finales, alcance MVP, limitaciones conocidas, criterios de
  aceptacion/no produccion, guia de demo final, checklist de cierre, indice de entrega, `mvp:eval`,
  `mvp:data-scan` y CI actualizado.
- **Criterios verificados:** no hay `BLOCKER` abierto para cierre MVP, la ausencia de feedback real
  queda declarada, el data scan sigue vigente y la documentacion no habilita produccion.
- **Nota de integridad:** No se recibió retroalimentación real de usuarios piloto en esta
  microfase.
- **Fuera de alcance:** produccion, datos reales, SSO/MFA, S3 obligatorio, OCR, SECOP en linea y
  afirmaciones de validacion juridica o de usuarios reales.

## Microfase 15 - Decisión ejecutiva sobre evolución a piloto real o pausa técnica - pendiente humana

- **Objetivo:** decidir con responsables humanos si el MVP controlado pasa a piloto real con datos y
  usuarios autorizados, o si se pausa tecnicamente.
- **Entregable previsto:** decision ejecutiva, condiciones de avance o pausa, responsables,
  controles adicionales y presupuesto de riesgos.

## Microfase 16 - Conector SECOP de búsqueda e importación - completada

- **Objetivo:** buscar procesos en fuentes públicas oficiales e importarlos con trazabilidad.
- **Entregable:** catálogo SECOP II/SECOP I verificado, cliente Socrata acotado, filtros, paginación,
  normalización, persistencia, deduplicación, auditoría, permisos, API, UI, evals offline y smoke
  live opt-in.
- **Criterios verificados:** importar crea un proceso sin iniciar análisis; repetir la importación no
  duplica; el payload se reduce a campos permitidos; CI no usa internet; los documentos quedan como
  enlaces o estado explícito.
- **Fuera de alcance:** descarga documental, actualización incremental, login, ofertas, trámites,
  scraping agresivo y producción.

## Microfase 17 - Descarga controlada de documentos públicos y actualización incremental - completada

Inventario incremental SECOP I/II, snapshots, eventos, cola PostgreSQL, descarga publica opt-in con proteccion SSRF, hashing, deduplicacion, versiones inmutables, integracion explicita con `ProcessDocument` y UI del proceso. La limitacion de descarga live queda documentada sin simular exito.

## Microfase 18 - Bandeja priorizada de oportunidades compatibles - completada

Discovery SECOP, screening determinístico contra snapshot publicado, política versionada, doce componentes explicables, outcomes conservadores, histórico, revisiones, worker PostgreSQL, API, permisos, auditoría y UI `/opportunities`. Compatibilidad, urgencia y completitud permanecen separadas. No incorpora ML, monitoreo periódico, alertas ni presentación de ofertas.

## Microfase 22 - Preparación para despliegue institucional restringido - completada

- **Objetivo:** entregar un paquete reproducible `RESTRICTED_SINGLE_HOST` con HTTPS, configuración externa, operación reversible y gate conservador.
- **Entregable:** Compose, imágenes multi-stage, Nginx, secretos por archivo, preflight, deploy/validate/status, backup/restore verification, retención, rollback, stop, runbooks, checklists, evals y simulación equivalente local.
- **Resultado:** `PACKAGE_READY_WITH_CONDITIONS`; no existe evidencia de servidor, dominio, certificado, SSO/MFA ni usuarios institucionales reales.
- **Fuera de alcance:** ejecutar la Microfase 23, producción pública, HA, Kubernetes o identidad corporativa.

Siguiente: Microfase 23 — Despliegue institucional restringido y validación con usuarios autorizados.

## Despues del MVP

Evaluadores restantes a profundidad, busqueda semantica si un caso la justifica, alertas de nuevos
procesos por perfil y analisis de competencia.
