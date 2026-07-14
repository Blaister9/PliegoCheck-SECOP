# Documentos publicos SECOP

PliegoCheck descubre documentos a partir de datasets oficiales de Datos Abiertos, conserva su identidad externa y distingue metadata, enlace y archivo validado. SECOP II usa los datasets documentales `dmgg-8hin`, `nbae-kzan`, `3skv-9na7`, `kgcd-kt7i` y `f8va-cf4m`; SECOP I usa `ps88-5e3v` y `8kpz-m6cc`. Los detalles de correlacion y las limitaciones observadas estan en [secop-document-source-discovery.md](secop-document-source-discovery.md).

Solo `.pdf`, `.docx`, `.xlsx`, `.txt` y `.csv` pueden avanzar a descarga controlada. Enlaces a `.rar`, `.zip`, `.7z`, ejecutables u otros formatos quedan inventariados como `LINK_AVAILABLE` + `UNSUPPORTED`; no habilitan descarga ni se interpretan como archivos incorporados al pipeline.

Un inventario puede quedar `METADATA_ONLY`, `LINK_AVAILABLE` o `UNSUPPORTED` sin que eso implique una descarga. Solo bytes validados y almacenados producen `DOWNLOADED`. Cada version descargada se enlaza con `ProcessDocument`; la extraccion se solicita despues y de forma explicita.

Los nombres y descripciones no son hechos juridicos. Un termino de adenda en texto libre produce `POTENTIAL_ADDENDUM`; solo una categoria/tipo explicito de la fuente produce `CONFIRMED_ADDENDUM`. Ambos estados quedan trazables y no recalculan decisiones.
# Estado documental en oportunidades

El screening solo refleja el estado documental público; la ausencia no bloquea metadatos ni se interpreta como cumplimiento. El análisis profundo exige proceso interno y comprueba inventario, extracción y normalización. La descarga y sincronización se mantienen en las colas de Microfase 17 y no se duplican en el motor de compatibilidad.
