# ADR-003 - Inventario y extraccion documental

- **Estado:** Aceptado
- **Fecha:** 2026-07-02
- **Decisores:** Equipo PliegoCheck

## Contexto

La Microfase 3 debe convertir documentos cargados manualmente en un inventario navegable y contenido
extraido, sin normalizar requisitos ni emitir decisiones GO / NO GO. La extraccion debe conservar
trazabilidad al documento original y registrar incertidumbre de forma explicita.

## Decision

Implementar una cola transaccional inicial en PostgreSQL con `document_processing_jobs` y un runner
deterministico en `apps/worker`. La API encola extraccion al almacenar un documento y expone endpoints
para inventario, reintentos y consulta de segmentos.

Tablas nuevas:

- `document_processing_jobs`: trabajos de extraccion con estado, reintentos, bloqueo y errores.
- `document_extractions`: resultado agregado por documento, formato detectado, conteos, advertencias
  y estado terminal.
- `extracted_segments`: segmentos trazables por pagina, parrafo, tabla, hoja, fila o linea.

Formatos soportados para extraccion inicial:

- PDF con texto digital (`.pdf`), sin OCR.
- Word moderno (`.docx`) con parrafos y tablas.
- Excel moderno (`.xlsx`) con filas y formulas preservadas como texto.
- CSV y TXT con deteccion de charset.

Formatos conservados pero no extraidos:

- Imagenes (`.png`, `.jpg`, `.jpeg`) quedan `NEEDS_OCR`.
- Office heredado (`.doc`, `.xls`) queda `UNSUPPORTED`.
- Documentos cifrados quedan `ENCRYPTED`.

## Reglas

- La extraccion es deterministica y no usa LLM.
- La ausencia de texto digital no se interpreta; se marca `NEEDS_OCR`.
- Un error controlado produce estado explicito, no contenido inventado.
- Los bytes originales se verifican con SHA-256 antes de extraer.
- Los limites de paginas, caracteres, hojas, filas y ZIP se configuran por entorno.
- Los ZIP Office se inspeccionan antes de leerlos para mitigar zip bombs, rutas peligrosas y macros.
- La UI muestra segmentos como texto plano, sin HTML inyectado.

## Consecuencias

El worker deja de ser solo diagnostico: puede reclamar trabajos, procesar uno o drenar la cola. La
cola inicial usa PostgreSQL con `FOR UPDATE SKIP LOCKED`, suficiente para esta microfase y reemplazable
por una cola dedicada si la carga lo exige.

## Fuera de alcance

OCR, normalizacion de requisitos, evaluadores LLM, `AgentRun`, `PromptVersion`, decisiones GO / NO GO,
busqueda semantica, autenticacion y almacenamiento S3 real.
