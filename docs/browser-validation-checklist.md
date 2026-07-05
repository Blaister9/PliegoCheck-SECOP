# Checklist de validacion en navegador

Ejecutar solo con datos sinteticos. Registrar fecha, navegador, commit y
operador en la bitacora interna del piloto.

## Preparacion

- [ ] `pnpm infra:up`, `pnpm db:migrate`, `pnpm db:check` ejecutados.
- [ ] `.env` deriva de `.env.local.example` o `.env.pilot.example`, sin secretos versionados.
- [ ] `pnpm pilot:prepare` ejecutado.
- [ ] API levantada con `pnpm dev:api`.
- [ ] Web levantada con `pnpm dev:web`.

## Recorrido

- [ ] Login admin funciona.
- [ ] Logout invalida sesion.
- [ ] Admin users lista usuarios sinteticos.
- [ ] Admin audit muestra eventos.
- [ ] Admin system no revela secretos.
- [ ] Processes lista el proceso piloto.
- [ ] Process detail carga sin errores visibles.
- [ ] Documents muestra documentos sinteticos.
- [ ] Extraction state esta completado o explica el pendiente.
- [ ] Requirements normalization muestra requisitos del fixture controlado.
- [ ] Company profile muestra empresa piloto.
- [ ] Evidence no expone rutas fisicas.
- [ ] Financial evaluation muestra resultados.
- [ ] Specialized evaluations muestra LEGAL, EXPERIENCE y TECHNICAL.
- [ ] Decision muestra `PENDIENTE_INFORMACION`, reglas, hallazgos y acciones.
- [ ] Decision report muestra preview.
- [ ] ZIP download descarga paquete plano.
- [ ] Viewer read-only no puede crear proceso ni usuarios.
- [ ] Reviewer review puede confirmar decision.
- [ ] Analyst execution puede ejecutar flujos permitidos.
- [ ] Permission denied muestra 403 comprensible con request id.
- [ ] Error states no muestran stack trace ni secretos.
- [ ] Responsive basic en ancho movil no rompe navegacion principal.
- [ ] Consola del navegador sin errores obvios durante el recorrido.

## Cierre

- [ ] `pnpm ops:backup` ejecutado y manifest revisado.
- [ ] `pnpm pilot:reset -- --confirm` limpia solo datos piloto.
- [ ] `pnpm infra:down` ejecutado si no se continua la demo.
