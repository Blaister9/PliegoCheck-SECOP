# Rollback restringido

Antes: contener writes si aplica, ejecutar/validar backup y confirmar compatibilidad del schema. `pnpm restricted:rollback -- --target-version <tag> --confirm-rollback` exige imágenes locales del target, detiene workers, cambia imágenes, conserva DB/storage y valida. No hace `alembic downgrade` automático.

Cancelar si falta backup, las imágenes no están aprobadas o el schema es incompatible. Si el cambio introdujo migración destructiva, rollback de aplicación no basta: restaurar en entorno aislado, decidir procedimiento con DBA y mantener activo el incidente. Registrar target, commit, resultado y responsables sin secretos.
