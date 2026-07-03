# Importacion manual de procesos y documentos

La importacion manual permite registrar procesos y cargar documentos originales. Desde la Microfase
3, cada documento almacenado queda encolado para extraccion deterministica. La carga manual todavia
no clasifica requisitos ni analiza cumplimiento.

## Flujo

1. Crear proceso con titulo y entidad obligatorios.
2. Consultar listado y detalle.
3. Adjuntar uno o varios documentos.
4. Validar cada archivo de forma independiente.
5. Guardar bytes originales fuera de PostgreSQL.
6. Persistir metadata, tamano y SHA-256.
7. Rechazar duplicados dentro del mismo proceso.
8. Encolar extraccion documental inicial con `processing_status=QUEUED`.
9. Descargar el archivo original cuando sea necesario.

## Variables

```text
DATABASE_URL=postgresql+psycopg://pliegocheck:pliegocheck@localhost:56543/pliegocheck
PLIEGOCHECK_STORAGE_PATH=./var/documents
PLIEGOCHECK_MAX_FILE_SIZE_MB=20
PLIEGOCHECK_ALLOWED_WEB_ORIGINS=http://localhost:3000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
PLIEGOCHECK_EXTRACTION_MAX_SECONDS=10
PLIEGOCHECK_WORKER_MAX_ATTEMPTS=3
```

`.env` no se versiona. `.env.example` contiene solo valores locales no sensibles.

## Infraestructura local

```bash
pnpm infra:up
pnpm db:migrate
pnpm db:check
pnpm dev:api
pnpm dev:web
pnpm worker:run-once
```

PostgreSQL se publica en `localhost:56543` para evitar colisiones con instalaciones locales en
`5432`. Alembic aplica migraciones desde base vacia y `db:check` detecta divergencias entre modelos y
migraciones.

## Formatos permitidos

```text
.pdf .doc .docx .xls .xlsx .csv .txt .png .jpg .jpeg
```

Validaciones de carga:

- archivo no vacio;
- tamano maximo configurable;
- extension final permitida;
- rechazo de rutas, rutas absolutas, nombres reservados y nombres excesivos;
- rechazo de doble extension peligrosa;
- `Content-Type` declarado coherente;
- firma magica basica cuando aplica;
- contenedores Office validos y sin macros;
- duplicado por SHA-256 dentro del mismo proceso.

No se ejecutan macros. La extraccion de Microfase 3 inspecciona contenedores Office antes de abrirlos
y aplica limites de ZIP, paginas, hojas, filas y caracteres. Ver
[document-extraction.md](document-extraction.md).

## Carga parcial

`POST /processes/{process_id}/documents` procesa cada archivo independientemente:

- `201`: todos almacenados;
- `207`: mezcla de almacenados y rechazados;
- `400`: todos rechazados.

La respuesta siempre incluye un resultado por archivo con `STORED` o `REJECTED` y un error
estructurado cuando aplica. Los documentos almacenados incluyen `processing_status`.

## Seguridad

Las respuestas no exponen `storage_key`, rutas absolutas ni temporales. La descarga verifica que el
documento pertenezca al proceso solicitado. Los eventos registran metadata minima, nunca bytes ni
contenido documental.

## Relacion con extraccion y normalizacion

La carga manual conserva el original y dispara el trabajo de extraccion. Si el worker no se ejecuta,
el documento queda `QUEUED`. La extraccion produce inventario, metadata, advertencias y segmentos
trazables. Desde la Microfase 4, esos segmentos pueden alimentar una normalizacion asincrona de
requisitos, que tampoco emite `GO`, `NO_GO` ni cumplimiento empresarial.
