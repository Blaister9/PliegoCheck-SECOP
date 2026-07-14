# ADR-017 — Sincronización incremental y documentos públicos SECOP

- **Estado:** aceptada
- **Fecha:** 2026-07-13
- **Alcance:** Microfase 17

## Contexto

La Microfase 16 conserva un vínculo oficial al proceso, pero no refresca metadatos ni inventaría
documentos. Las fuentes documentales publican referencias útiles, aunque no garantizan que cada URL
sea una descarga directa estable. Tratar una página HTML, un enlace HTTP o un error del portal como
archivo sería una pérdida de integridad y un riesgo SSRF.

## Decisión

Agregar una cola PostgreSQL de sincronización y otra de descarga. Cada sincronización vuelve a
consultar el dataset de proceso por su identificador estable, guarda un snapshot reducido, compara
campos y descubre documentos mediante providers separados para SECOP I y SECOP II. Los documentos
externos y sus versiones forman un histórico inmutable; una desaparición crea un evento, no un
borrado.

La descarga está deshabilitada por defecto. Cuando se solicita explícitamente, un cliente sin
cookies valida HTTPS, host, DNS público y cada redirect; transmite a temporal con límite estricto,
rechaza HTML y tipos no permitidos, calcula SHA-256, valida bytes con el pipeline existente y crea
un `ProcessDocument`. Si la transacción falla, elimina el objeto compensatoriamente.

La identidad documental combina fuente, id externo y URL normalizada. Un hash idéntico conserva la
versión; un hash nuevo crea otra versión vinculada. La extracción se encola mediante una acción API
separada. No se encolan normalización, evaluación, decisión ni reporte.

Una adenda solo es `CONFIRMED_ADDENDUM` cuando la fuente la clasifica expresamente. Palabras en el
título producen `POTENTIAL_ADDENDUM` y `requires_human_review=true`.

## Alternativas descartadas

- Scraping del HTML del expediente: frágil, innecesario y fuera del alcance autorizado.
- Reutilizar cookies del navegador: amplía privilegios y viola la frontera pública.
- Descargar durante el mapper o el sync: mezcla responsabilidades y dificulta compensación.
- Sobrescribir `ProcessDocument`: destruye el histórico y rompe reproducibilidad.
- Ejecutar análisis tras descargar: una acción de ingesta no autoriza una nueva decisión.

## Consecuencias

El sistema puede refrescar metadatos e inventariar ambas fuentes aunque una descarga no sea
soportable. La disponibilidad real depende de CCE y puede terminar honestamente en `UNSUPPORTED` o
`FAILED`. El almacenamiento sigue siendo local/no productivo y el monitoreo periódico queda fuera
de alcance.
