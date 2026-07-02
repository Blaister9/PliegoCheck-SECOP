# ADR-002 — Persistencia e importación manual

- **Estado:** Aceptado
- **Fecha:** 2026-07-02
- **Decisores:** Equipo PliegoCheck

## Contexto

La Microfase 2 necesita crear procesos manualmente, adjuntar documentos originales y conservar
metadata auditable sin extraer ni analizar contenido. La decisión GO / NO GO sigue fuera de alcance:
esta fase solo deja el proceso listo para inventario documental.

## Decisión

Implementar persistencia con PostgreSQL, SQLAlchemy 2 y Alembic. Los documentos originales se
almacenan fuera de PostgreSQL mediante una abstracción `DocumentStorage`; la primera implementación
es `LocalDocumentStorage` sobre `PLIEGOCHECK_STORAGE_PATH`.

Tablas iniciales:

- `processes`: metadata del proceso manual, referencia interna generada por servidor, estado
  operativo y timestamps.
- `process_documents`: metadata del archivo original, SHA-256, tamaño, tipos declarados/detectados
  y `storage_key` relativa.
- `import_events`: eventos básicos de importación y descarga, sin contenido documental.

La migración inicial debe aplicar desde base vacía. La aplicación normal no usa
`metadata.create_all()`.

## Reglas

- `internal_reference` se genera en servidor y no se edita.
- `estimated_value` usa decimal, no float.
- `process_id + sha256` es único; el mismo archivo puede existir en procesos distintos.
- `storage_key` es relativa y generada por servidor.
- El nombre original se conserva solo como metadata.
- Los documentos rechazados no quedan almacenados físicamente.
- Si falla la base después de guardar, la API intenta borrar el archivo y registra el error si la
  compensación falla.
- `READY_FOR_INVENTORY` solo significa que hay al menos un documento almacenado; no es una decisión
  de participación.

## Consecuencias

PostgreSQL pasa a ser dependencia local y de CI. El almacenamiento local es suficiente para desarrollo
y pruebas, pero la abstracción permite reemplazarlo por S3-compatible en una fase posterior sin
cambiar los contratos web/API.

## Fuera de Alcance

Extracción documental, OCR, clasificación automática, SECOP II automático, agentes de IA,
autenticación, S3 real, colas y motor GO / NO GO.
