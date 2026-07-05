# Checklist de readiness para usuarios piloto

Este checklist aplica solo a validacion piloto con datos sinteticos. No autoriza uso productivo.

- [ ] Entorno controlado levantado con `pnpm controlled:deploy` o flujo equivalente documentado.
- [ ] `pnpm controlled:validate` pasa.
- [ ] `pnpm controlled:eval` pasa.
- [ ] `pnpm controlled:data-scan` pasa.
- [ ] `pnpm mvp:eval` pasa.
- [ ] `pnpm mvp:data-scan` pasa.
- [ ] Migraciones aplicadas con `pnpm db:migrate` y verificadas con `pnpm db:check`.
- [ ] Usuarios sinteticos `ADMIN`, `ANALYST`, `REVIEWER` y `VIEWER` disponibles.
- [ ] Dataset sintetico preparado con `pnpm pilot:prepare`.
- [ ] Auth funciona y logout invalida sesion.
- [ ] Demo corre con `pnpm pilot:run` o recorrido web equivalente.
- [ ] Reporte y ZIP descargan sin secretos ni rutas fisicas.
- [ ] Auditoria registra login, acciones, permisos denegados y descargas.
- [ ] Backup previo ejecutado y manifest revisado.
- [ ] Limites explicados: no produccion, no datos reales, no concepto juridico, no SSO/MFA.
- [ ] Formulario `pilot/user-validation/feedback-form.md` listo.
- [ ] Matriz `pilot/user-validation/findings-matrix.csv` lista.
- [ ] Plan de rollback revisado y responsable tecnico asignado.

Para una nueva sesion posterior al cierre MVP, usar release candidate
`0.14.0-mvp-controlled` y declarar al inicio: No se recibió retroalimentación real de usuarios
piloto en esta microfase.
