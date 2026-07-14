# Flujo de búsqueda e importación SECOP

## Flujo controlado

1. Un usuario con `external:search` elige una fuente y envía filtros acotados.
2. El cliente consulta el dataset oficial, normaliza solo campos permitidos y persiste la búsqueda,
   los resultados, warnings y un hash del payload reducido.
3. La UI presenta el resumen, estado de documentos y enlace oficial; no presenta el payload crudo.
4. Un usuario con `external:import` confirma el identificador externo del resultado.
5. El servicio calcula la clave estable, busca un vínculo previo y crea un intento auditable.
6. Si es nuevo, crea un proceso `DOCUMENTS_PENDING`, su vínculo externo y el evento de importación.
   Si existe, responde `SKIPPED_DUPLICATE` con el proceso interno existente.
7. El usuario puede abrir el proceso, verificar la fuente y cargar documentos mediante el flujo
   existente. El análisis sigue siendo una acción posterior y explícita.

## Trazabilidad

La búsqueda conserva consulta, filtros, fuente, tiempos, conteo y error. El resultado conserva
identificador/referencia de origen, campos normalizados, estados por campo, warnings, payload
reducido y hash. El vínculo conserva URL oficial, estado documental y fecha de importación. Los
eventos operacionales registran éxito, fallo o deduplicación sin volcar contenido externo completo.

Los campos ausentes siguen ausentes. En particular, SECOP II no publica moneda junto a
`precio_base`: el proceso interno conserva el valor y `currency=null`, con warning y estado
`UNKNOWN` en el manifiesto de importación. No se asigna `COP` por contexto.

## Documentos y decisiones

La ausencia de enlaces estables se representa como `DOCUMENT_DOWNLOAD_UNSUPPORTED` y se muestra
como “documentos no importados”. Esta versión no descarga archivos, no navega con credenciales y no
hace scraping. Importar no crea trabajos del motor de decisión ni resultados GO/NO GO. La revisión
humana de la fuente y de los documentos sigue siendo obligatoria.
