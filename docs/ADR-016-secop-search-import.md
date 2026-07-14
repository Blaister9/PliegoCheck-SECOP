# ADR-016 — Búsqueda e importación controlada desde SECOP

- **Estado:** aceptada
- **Fecha:** 2026-07-13
- **Alcance:** Microfase 16

## Contexto

El MVP admitía carga manual, pero no una ruta trazable para descubrir procesos públicos. La fuente
externa es imperfecta y no debe mezclarse con evaluación, documentos internos ni decisión GO/NO GO.

## Decisión

Se integra la API pública Socrata de Datos Abiertos Colombia con un catálogo cerrado de datasets
verificados para SECOP II y SECOP I. El flujo síncrono persiste fuente, búsqueda y resultados
normalizados. La importación crea un `Process` con fuente `SECOP_IMPORT` y tablas separadas para el
vínculo, el intento y la evidencia externa.

La identidad estable es `(source_system, source_dataset, source_process_id)`. Una restricción única
y la consulta previa impiden procesos duplicados; un intento repetido queda auditado como
`SKIPPED_DUPLICATE`. Importar no crea `DecisionJob`, no ejecuta evaluadores y no descarga documentos.

Se usan contratos Pydantic generados a JSON Schema y TypeScript. `ADMIN` posee todos los permisos;
`ANALYST` puede buscar e importar; `REVIEWER` y `VIEWER` solo leen. La UI no muestra el payload crudo.

## Alternativas descartadas

- Scraping del portal: frágil, innecesario y de mayor riesgo operativo.
- Copiar todos los campos de la fuente: aumenta exposición de datos personales y acoplamiento.
- Importar y analizar en una sola acción: viola la separación ingesta/decisión y oculta falta de
  evidencia documental.
- Worker asíncrono inicial: la consulta paginada acotada cabe en el presupuesto de timeout actual.

## Consecuencias

Hay trazabilidad y operación offline verificable, pero la disponibilidad y actualidad siguen
dependiendo de terceros. Los enlaces a documentos son informativos y requieren revisión humana.
Una futura descarga pública controlada exige límites de tamaño, tipo, hash y almacenamiento; no se
autoriza por esta ADR.
