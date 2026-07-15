# Gate del piloto supervisado

Este gate no equivale a aprobación de producción ni expresa probabilidad de adjudicación o recomendación automática de presentar oferta.

- `PILOT_BLOCKED`: secreto expuesto, pérdida de datos, permisos críticos rotos, acción SECOP no autorizada o riesgo grave no mitigado.
- `REMEDIATION_REQUIRED`: tarea esencial incompleta, duplicación material, scheduler inestable, backup/restore fallido, falso cumplimiento o recuperación fallida.
- `PILOT_READY_WITH_CONDITIONS`: flujo técnico completo, sin blocker, restricciones documentadas y entrega real o validación humana pendientes.
- `PILOT_READY`: además exige usuario real, tareas esenciales completas, feedback aceptable, recuperación verificada y ningún HIGH abierto.

## Resultado vigente

`PILOT_READY_WITH_CONDITIONS`.

La ejecución técnica completó discovery limitado, importación idempotente, sincronización sin descargas, monitor y alertas deduplicadas, entrega dry-run, reinicios, recuperación, backup/restore aislado y retención dry-run. No hay `BLOCKER`, `HIGH` abierto, pérdida de datos, bypass de permisos ni entrega externa real. La condición abierta es `USER_VALIDATION_PENDING`; por ello este gate no autoriza producción y no puede elevarse a `PILOT_READY`.
