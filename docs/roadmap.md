# Roadmap incremental — PliegoCheck-SECOP

Fases pequeñas, cada una con entregable verificable. Cada microfase termina integrada en `main` mediante Pull Request, siguiendo [AGENTS.md](../AGENTS.md).

```text
Microfase 0: fundación documental
Microfase 1: esqueleto del monorepo
Microfase 2: importación manual de proceso y documentos
Microfase 3: inventario y extracción documental
Microfase 4: normalización de requisitos
Microfase 5: perfil de empresa y evidencias
Microfase 6: evaluador financiero inicial
Microfase 7: motor determinístico de decisión
Microfase 8: explicación y reporte auditable
Microfase 9: integración con datos abiertos SECOP II
Microfase 10: autenticación, multiempresa y operación
```

---

## Microfase 0 — Fundación documental ✅ (este trabajo)

- **Objetivo:** fijar visión, arquitectura, dominio, contratos y gobernanza antes de escribir código.
- **Entregable:** README, AGENTS.md, ADR-001, modelo de dominio, motor de decisión, contratos de agentes, estándar de prompting, seguridad y este roadmap.
- **Dependencias:** ninguna.
- **Criterios de aceptación:** documentos completos, consistentes entre sí, en UTF-8, integrados en `main` vía PR.
- **Riesgos:** sobre-especificar antes de aprender de la implementación (mitigado: los documentos son revisables por ADR).
- **Fuera de alcance:** cualquier código funcional.

## Microfase 1 — Esqueleto del monorepo ⬅ siguiente

- **Objetivo:** materializar la estructura del ADR-001 con tooling mínimo funcionando.
- **Entregable:** monorepo con `apps/web` (Next.js), `apps/api` (FastAPI con healthcheck), `apps/worker` (proceso Python mínimo), `packages/schemas` (primer esquema compartido: el requisito normalizado), lint y formateo configurados, CI que compila y valida en cada PR, contenedores de desarrollo.
- **Dependencias:** Microfase 0.
- **Criterios de aceptación:** `web` arranca y llama al healthcheck de `api`; CI verde en PR; esquema del requisito validado desde Python y TypeScript; sin lógica de negocio.
- **Riesgos:** parálisis por tooling (mitigar: configuración mínima, sin optimizaciones prematuras).
- **Fuera de alcance:** base de datos, agentes, UI real, autenticación.

## Microfase 2 — Importación manual de proceso y documentos

- **Objetivo:** poder crear un proceso manualmente y adjuntarle documentos de forma inmutable.
- **Entregable:** entidades `Process`, `ProcessVersion`, `ProcessDocument` en PostgreSQL (Alembic), almacenamiento S3-compatible con hash de integridad, UI mínima de creación y carga, `AuditEvent`s básicos.
- **Dependencias:** Microfase 1.
- **Criterios de aceptación:** un usuario crea un proceso, sube PDF/DOCX/XLSX, los archivos quedan almacenados con hash y versión; migraciones reproducibles.
- **Riesgos:** modelar de más (mitigar: solo las entidades de esta fase).
- **Fuera de alcance:** extracción de contenido, datos abiertos, análisis.

## Microfase 3 — Inventario y extracción documental

- **Objetivo:** extraer contenido de los documentos con calidad medida.
- **Entregable:** `DocumentInventoryAgent` y `DocumentExtractionAgent` operativos sobre la cola de trabajos (primera incorporación de la cola), `DocumentExtraction` persistida por página/sección, métricas de calidad y páginas fallidas, primeros `AgentRun`/`PromptVersion` registrados.
- **Dependencias:** Microfase 2.
- **Criterios de aceptación:** un pliego PDF real produce extracción navegable con origen por página; documentos ilegibles quedan marcados, no inventados; cada ejecución registra modelo, prompt y consumo.
- **Riesgos:** calidad de OCR en escaneados (aceptado: se registra como limitación y escala).
- **Fuera de alcance:** normalización de requisitos, evaluaciones.

## Microfase 4 — Normalización de requisitos

- **Objetivo:** convertir extracciones en requisitos normalizados trazables.
- **Entregable:** `RequirementNormalizationAgent` con el esquema del [motor de decisión](decision-engine.md), Structured Outputs validadas, detección de conflictos pliego/adendas, UI de revisión de requisitos.
- **Dependencias:** Microfase 3.
- **Criterios de aceptación:** de un proceso real se obtiene la lista de requisitos con documento/página/sección verificables manualmente; `status` siempre `UNKNOWN`; salidas inválidas se rechazan y quedan registradas.
- **Riesgos:** cobertura incompleta de requisitos (mitigar: revisión humana en UI y métricas de cobertura).
- **Fuera de alcance:** evaluación de cumplimiento.

## Microfase 5 — Perfil de empresa y evidencias

- **Objetivo:** capturar la capacidad real de la empresa con soporte documental.
- **Entregable:** `CompanyProfile`, `CompanyCapability`, `RequirementEvidence` persistidas; carga de soportes (RUP, estados financieros, certificaciones) con vigencias; UI de perfil.
- **Dependencias:** Microfase 2 (almacenamiento); independiente de 3–4 en lo esencial.
- **Criterios de aceptación:** todo indicador o capacidad guardado apunta a su documento soporte; datos sin soporte quedan marcados como no acreditados.
- **Riesgos:** perfiles inflados sin soporte (mitigado por el modelo: sin documento no hay evidencia).
- **Fuera de alcance:** evaluación automática de los soportes.

## Microfase 6 — Evaluador financiero inicial

- **Objetivo:** primer evaluador vertical completo: requisitos financieros vs. perfil.
- **Entregable:** `FinancialEvaluationAgent` conforme a su contrato, comparaciones aritméticas deterministas de indicadores, `Evaluation` y `Finding`s persistidos con evidencia citada, `EvidenceVerificationAgent` en su primera versión verificando esta vertical.
- **Dependencias:** Microfases 4 y 5.
- **Criterios de aceptación:** para un proceso real, cada requisito financiero recibe `status` con evidencia o `UNKNOWN`; un `COMPLIES` sin evidencia es imposible de persistir; conflictos marcan revisión humana.
- **Riesgos:** interpretación errónea de indicadores atípicos (mitigar: escala a revisión humana).
- **Fuera de alcance:** los demás evaluadores; decisión final.

## Microfase 7 — Motor determinístico de decisión

- **Objetivo:** implementar el motor de [decision-engine.md](decision-engine.md).
- **Entregable:** servicio determinístico con reglas versionadas (`DecisionRule`), `Decision` persistida con trazabilidad completa, suspensión por revisión humana pendiente, tests exhaustivos de las reglas R1–R9.
- **Dependencias:** Microfase 6 (al menos una vertical alimentando el motor).
- **Criterios de aceptación:** misma entrada + misma versión de reglas ⇒ misma decisión (test); sin evidencia crítica jamás emite `GO` (test); toda decisión registra versiones de reglas y prompts.
- **Riesgos:** reglas demasiado rígidas para la variedad de pliegos (mitigar: versionado y gestión de cambios).
- **Fuera de alcance:** cobertura de todas las categorías de requisitos.

## Microfase 8 — Explicación y reporte auditable

- **Objetivo:** comunicar la decisión con evidencia navegable.
- **Entregable:** `DecisionExplanationAgent`, reporte con factores determinantes y citas, flujo de `HumanReview` (confirmar/corregir/rechazar) operativo, exportación del reporte.
- **Dependencias:** Microfase 7.
- **Criterios de aceptación:** el reporte cita documento/página/sección verificables; la explicación no puede alterar la decisión (test); las revisiones humanas quedan auditadas.
- **Riesgos:** explicaciones que suenen a certeza jurídica (mitigar: lenguaje calibrado obligatorio y advertencia fija).
- **Fuera de alcance:** métricas de negocio, comparativos entre procesos.

## Microfase 9 — Integración con datos abiertos SECOP II

- **Objetivo:** ingesta automática desde datos abiertos de Colombia Compra Eficiente.
- **Entregable:** `SecopIngestionAgent` contra la API de datos abiertos (datos.gov.co), búsqueda y registro de procesos por identificador, descarga de documentos disponibles, detección de adendas que crean `ProcessVersion` nueva y disparan reanálisis.
- **Dependencias:** Microfases 2 y 3.
- **Criterios de aceptación:** un proceso real se registra por su identificador SECOP con metadatos y documentos disponibles; los faltantes se completan por carga manual; las adendas generan nueva versión.
- **Riesgos:** datos abiertos incompletos o con rezago (aceptado: carga manual sigue siendo vía de primera clase).
- **Fuera de alcance:** scraping de la plataforma transaccional.

## Microfase 10 — Autenticación, multiempresa y operación

- **Objetivo:** operación multiusuario y multiorganización segura.
- **Entregable:** autenticación, roles (administrador, analista, revisor), aislamiento por `Organization` verificado con pruebas, límites de costo por tenant, observabilidad completa ([security-and-governance.md](security-and-governance.md)), despliegue en contenedores documentado.
- **Dependencias:** Microfases 1–8 (9 deseable).
- **Criterios de aceptación:** pruebas de aislamiento entre tenants en verde; acciones críticas restringidas por rol; telemetría de costos operativa; despliegue reproducible.
- **Riesgos:** endurecer seguridad tarde (mitigado: los principios aplican desde la Microfase 2; aquí se completan y verifican).
- **Fuera de alcance:** alta disponibilidad multi-región, facturación.

---

## Después del MVP (no comprometido)

Evaluadores restantes a profundidad, búsqueda semántica si un caso la justifica, alertas de nuevos procesos por perfil, y análisis de competencia. Ninguno condiciona la arquitectura actual.
