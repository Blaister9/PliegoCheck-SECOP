# Scorecard del piloto supervisado

Estados: `PASS`, `PASS_WITH_CONDITIONS`, `FAIL`, `NOT_VERIFIED`. No es una puntuación numérica.

| Dimensión | Estado | Evidencia / condición |
| --- | --- | --- |
| functional | PASS | Discovery, importación idempotente, sync conservador y análisis explícito verificados. |
| usability | PASS_WITH_CONDITIONS | Recorrido técnico completo; `USER_VALIDATION_PENDING` requiere participante. |
| data quality | PASS_WITH_CONDITIONS | Warnings y ausencias permanecen explícitos; la fuente pública no siempre informa cierre, moneda o documentos. |
| explainability | PASS | Componentes, brechas, faltantes y disclaimer visibles; no hay probabilidad de adjudicación. |
| security | PASS | Opt-in por proceso, límites, dry-run, permisos y escaneo; no producción. |
| operations | PASS | Reinicio parcial y completo, migraciones, backup, restore aislado y apagado definidos/verificados. |
| reliability | PASS | Baseline, segunda corrida, cambio material y repetición sin duplicado verificados. |
| notification usefulness | PASS_WITH_CONDITIONS | Funcionamiento técnico dry-run verificado; utilidad requiere feedback humano. |
| recovery | PASS | Outbox abandonado, retries/fallos por fixture y restore aislado verificados. |
| documentation | PASS | Runbooks, checklist, métricas y paquete versionados. |
