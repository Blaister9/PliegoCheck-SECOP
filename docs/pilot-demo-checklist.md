# Checklist de demo del piloto

Marca cada item durante una demo o validacion del piloto controlado. Solo datos
sinteticos.

## Preparacion

- [ ] `pnpm infra:up` levanta PostgreSQL local.
- [ ] `pnpm db:migrate` aplica migraciones desde base vacia.
- [ ] `pnpm db:check` confirma que Alembic esta actualizado.
- [ ] `pnpm pilot:readiness` reporta entorno local y dataset disponible.
- [ ] `pnpm pilot:prepare` crea usuarios, proceso, documentos, empresa y snapshot.

## Autenticacion y roles

- [ ] Login como admin funciona.
- [ ] Admin ve usuarios y auditoria.
- [ ] Login como analyst funciona.
- [ ] Analyst puede crear/ejecutar el flujo.
- [ ] Viewer solo lee (crear devuelve 403).
- [ ] Reviewer puede confirmar/override la decision.
- [ ] Logout invalida la sesion (acceso posterior falla).

## Flujo end-to-end

- [ ] Proceso piloto visible con documentos cargados.
- [ ] Extraccion documental completada.
- [ ] Normalizacion controlada con requisitos financiero/juridico/experiencia/tecnico.
- [ ] Empresa piloto y snapshot publicado visibles.
- [ ] Evaluacion financiera completada (cumple + no cumple + UNKNOWN).
- [ ] Evaluaciones especializadas (LEGAL, EXPERIENCE, TECHNICAL) completadas.
- [ ] Decision preliminar = `PENDIENTE_INFORMACION` (no forzada a GO).
- [ ] Reglas disparadas, cobertura y hallazgos visibles.
- [ ] Acciones requeridas generadas.
- [ ] Reporte ejecutivo generado.
- [ ] Paquete ZIP descargable (9 artefactos, sin `.env`, sin rutas fisicas).

## Auditoria, backup y limpieza

- [ ] Eventos de auditoria registran login, evaluaciones, decision y descarga.
- [ ] `pnpm ops:backup` produce manifest con hashes y excluye `.env`.
- [ ] `pnpm pilot:reset -- --confirm` elimina SOLO datos de piloto.
- [ ] Un usuario/proceso no-piloto permanece tras el reset.
- [ ] `pnpm infra:down` detiene la infraestructura.

## Verificacion automatizada

- [ ] `pnpm pilot:eval` pasa (flujo completo con auth, sin OpenAI).
- [ ] `pnpm check` incluye `pilot:eval` y pasa.
