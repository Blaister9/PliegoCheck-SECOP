# Indice de entrega del MVP controlado

- [Entrega de notificaciones](notification-delivery.md)
- [Piloto de notificaciones](notification-pilot-runbook.md)
- [Incidentes de notificaciones](notification-incident-runbook.md)

Microfase 19: [monitores](opportunity-monitors.md), [alertas](opportunity-alerts.md), [scheduler](opportunity-monitor-scheduling.md), [deduplicación](opportunity-alert-deduplication.md) y [operación](opportunity-monitor-operations.md).

## Extension SECOP

- [Conector SECOP](secop-connector.md)
- [Documentos publicos SECOP](secop-documents.md)
- [Actualizaciones incrementales](secop-incremental-updates.md)
- [Seguridad de descargas](secop-document-security.md)

## Decision y cierre

- [ADR-014 - Cierre de MVP controlado](ADR-014-controlled-mvp-closure.md)
- [Hallazgos finales](mvp-final-findings.md)
- [Checklist de cierre](mvp-closure-checklist.md)
- [Release candidate](release-candidate.md)

## Alcance y restricciones

- [Alcance del MVP controlado](mvp-controlled-scope.md)
- [Limitaciones conocidas](known-limitations.md)
- [Criterios de aceptacion](mvp-acceptance-criteria.md)
- [Criterios de no produccion](non-production-criteria.md)

## Operacion y demo

- [Guia de demo final](final-demo-guide.md)
- [Runbook de despliegue controlado](controlled-deployment-runbook.md)
- [Checklist pre-despliegue](pre-deployment-checklist.md)
- [Checklist post-despliegue](post-deployment-checklist.md)
- [Plan de rollback](rollback-plan.md)

## Validacion

- `pnpm pilot:eval`
- `pnpm controlled:eval`
- `pnpm controlled:data-scan`
- `pnpm mvp:eval`
- `pnpm mvp:data-scan`
- `pnpm check`

## Extensión posterior al cierre del MVP — Microfase 16

- [ADR-016 - Búsqueda e importación SECOP](ADR-016-secop-search-import.md)
- [Conector SECOP](secop-connector.md)
- [Descubrimiento de fuentes](secop-source-discovery.md)
- [Flujo de importación](secop-import-workflow.md)
- [Limitaciones del conector](secop-limitations.md)
- `pnpm secop:test`
- `pnpm secop:eval`
- `pnpm secop:smoke` (manual y opt-in; nunca en CI)

## Extensión Microfase 18

- [ADR-018](ADR-018-opportunity-prioritization.md)
- [Discovery](opportunity-discovery.md)
- [Compatibilidad](opportunity-compatibility.md)
- [Política](opportunity-ranking-policy.md)
- [Outcomes](opportunity-outcomes.md)
- [Análisis profundo](opportunity-deep-analysis.md)
- `pnpm opportunities:test`
- `pnpm opportunities:eval`
- `pnpm opportunities:semantic-scan`
