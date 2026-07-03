# Inventario y extraccion documental

La Microfase 3 procesa documentos ya cargados por importacion manual. El objetivo es obtener un
inventario de estado y segmentos de texto trazables. No evalua requisitos, no consulta SECOP II y no
emite decisiones GO / NO GO.

## Flujo

1. `POST /processes/{process_id}/documents` guarda el documento original y encola extraccion.
2. El worker reclama trabajos pendientes con bloqueo transaccional.
3. El worker verifica SHA-256 contra el archivo almacenado.
4. El extractor deterministico produce metadata, advertencias y segmentos.
5. La API expone inventario, detalle y segmentos paginados.
6. El usuario puede reintentar extraccion cuando no hay un trabajo activo.

## Endpoints

| Endpoint | Uso |
| --- | --- |
| `GET /processes/{process_id}/inventory` | Inventario documental con estado de procesamiento y ultimo resultado. |
| `POST /processes/{process_id}/extractions` | Encola documentos pendientes o fallidos del proceso. |
| `POST /processes/{process_id}/documents/{document_id}/extractions` | Encola o fuerza reintento de un documento. |
| `GET /processes/{process_id}/documents/{document_id}/extraction` | Detalle del ultimo resultado y preview de segmentos. |
| `GET /processes/{process_id}/documents/{document_id}/extraction/segments` | Segmentos paginados con filtros por tipo, pagina u hoja. |

## Estados

| Estado | Significado |
| --- | --- |
| `QUEUED` | El documento tiene trabajo pendiente. |
| `PROCESSING` | Un worker reclamo el trabajo. |
| `COMPLETED` | Extraccion terminada sin advertencias relevantes. |
| `COMPLETED_WITH_WARNINGS` | Extraccion terminada con advertencias registradas. |
| `NEEDS_OCR` | No hay texto digital suficiente o el formato es imagen. |
| `UNSUPPORTED` | El formato se conserva pero no se extrae en esta fase. |
| `ENCRYPTED` | El documento requiere clave o esta cifrado. |
| `FAILED` | Error tecnico no recuperado dentro de los reintentos. |

## Comandos

```bash
pnpm worker:health
pnpm worker:run-once
pnpm worker:drain -- --max-jobs 10
pnpm extraction:test
```

## Variables

```text
PLIEGOCHECK_EXTRACTION_MAX_SECONDS=10
PLIEGOCHECK_EXTRACTION_MAX_CHARACTERS=2000000
PLIEGOCHECK_EXTRACTION_MAX_PAGES=500
PLIEGOCHECK_EXTRACTION_MAX_SHEETS=50
PLIEGOCHECK_EXTRACTION_MAX_ROWS_PER_SHEET=10000
PLIEGOCHECK_EXTRACTION_MAX_ZIP_ENTRIES=5000
PLIEGOCHECK_EXTRACTION_MAX_UNCOMPRESSED_MB=200
PLIEGOCHECK_EXTRACTION_MAX_COMPRESSION_RATIO=100
PLIEGOCHECK_WORKER_MAX_ATTEMPTS=3
```

## Seguridad

- Los archivos Office se inspeccionan como ZIP antes de abrirlos.
- Se rechazan macros, rutas peligrosas, excesos de entradas, tamanos descomprimidos y ratios de
  compresion anormales.
- La extraccion corre con timeout en un proceso hijo.
- Los segmentos se guardan como texto y la web los renderiza en texto plano.
- Un extractor nunca inventa contenido para llenar vacios.

## Relacion con normalizacion

Desde la Microfase 4, las extracciones `COMPLETED` y `COMPLETED_WITH_WARNINGS` son elegibles para
normalizacion de requisitos. La extraccion sigue siendo deterministica: no decide que es un
requisito, no llama IA y no produce GO / NO GO. Ver [requirement-normalization.md](requirement-normalization.md).

## Limitaciones

OCR, clasificacion juridica, evaluacion de cumplimiento y decisiones quedan para microfases
posteriores.
