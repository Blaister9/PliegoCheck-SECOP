# Snapshots de perfil de empresa

Un snapshot congela el estado de un perfil para que una evaluacion futura sea reproducible.

## Ciclo

1. `POST /companies/{company_id}/snapshots` crea una version `DRAFT`.
2. El payload se serializa en JSON canonico con orden estable.
3. Se calcula un digest SHA-256 del payload.
4. `POST /companies/{company_id}/snapshots/{snapshot_id}/publish` valida que el digest no haya
   cambiado y publica la version.
5. Al publicar, cualquier snapshot previamente publicado del mismo perfil queda `SUPERSEDED`.

## Contenido

El payload incluye datos del perfil, subentidades, metadatos de evidencias, enlaces dato-evidencia y
completitud calculada. No incluye rutas fisicas de almacenamiento.

## Reglas

- Un snapshot publicado es inmutable.
- Si el perfil editable cambia, se crea otro snapshot.
- La publicacion puede requerir completitud; para pruebas o preparacion se permite crear drafts
  incompletos con `allow_incomplete=true`.
- Las evaluaciones de Microfase 6 y posteriores deben referenciar `company_snapshot_id` o version
  equivalente, nunca datos editables sin version.
- La decision preliminar de Microfase 7 referencia siempre un snapshot publicado. El digest de ese
  snapshot participa en el manifiesto de entrada e idempotencia del `DecisionRun`; cambios posteriores
  del perfil no recalculan historicos.
