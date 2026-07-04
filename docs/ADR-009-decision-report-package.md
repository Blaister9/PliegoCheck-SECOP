# ADR-009 - Reporte ejecutivo y paquete de decision

- **Estado:** Aceptado
- **Fecha:** 2026-07-04
- **Decisores:** Equipo PliegoCheck

## Contexto

La Microfase 7 produce una decision preliminar deterministica y la Microfase 8 amplia sus insumos
con evaluadores juridico, tecnico y de experiencia. El siguiente problema no es recalcular la
decision, sino empaquetarla para revision ejecutiva con trazabilidad, artefactos descargables y
digests reproducibles.

El paquete debe ser util para comite de licitaciones, pero no puede convertirse en concepto
juridico, recomendacion oficial ni sustituto de revision humana.

## Decision

Implementar un modulo `reports` que genera un paquete inmutable a partir de una `DecisionRun`
completada:

| Area | Decision |
| --- | --- |
| Fuente | Ultima decision preliminar completada de un proceso. |
| Recalculo | Prohibido: el reporte lee el snapshot de decision existente y no ejecuta el motor. |
| Contratos | Modelos Pydantic canonicos en `packages/schemas`, generados a JSON Schema y TypeScript. |
| Persistencia | Tablas `decision_report_*` con job, paquete, artefactos, secciones y eventos. |
| Worker | Cola PostgreSQL `decision_report_jobs` con `FOR UPDATE SKIP LOCKED`. |
| Templates | Templates versionados bajo `config/report-templates/v1`. |
| Artefactos | HTML, Markdown, JSON, CSV, manifest y ZIP. |
| Storage | `LocalDocumentStorage` bajo `reports/`, reemplazable por S3-compatible. |
| Seguridad | Escape HTML explicito, nombres de archivo controlados y ZIP sin rutas. |

## Consecuencias

Positivas:

- El reporte es reproducible: mismo input digest y misma version de templates producen los mismos
  artefactos logicos.
- La API puede ser idempotente cuando ya existe un paquete completado para el mismo input.
- El comite recibe resumen ejecutivo, matriz requisito-evidencia-decision, acciones pendientes,
  riesgos, manifest y ZIP.

Costos:

- Hay una cola y un conjunto de tablas adicionales que deben migrarse y monitorearse.
- El manifest excluye el ZIP de su propio digest para evitar una referencia circular.
- El almacenamiento local sigue siendo un backend de desarrollo; S3 real queda para endurecimiento
  operativo.

## Limites

- No genera nuevas evaluaciones ni acciones.
- No llama modelos de IA.
- No resuelve conflictos juridicos.
- No convierte `PENDIENTE_INFORMACION` en `GO`.
- No firma digitalmente artefactos.
