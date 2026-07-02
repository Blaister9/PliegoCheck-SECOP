# Importación manual de procesos y documentos

La Microfase 2 permite registrar procesos manualmente y cargar documentos originales. No extrae,
clasifica ni analiza contenido.

## Flujo

1. Crear proceso con título y entidad obligatorios.
2. Consultar listado y detalle.
3. Adjuntar uno o varios documentos.
4. Validar cada archivo de forma independiente.
5. Guardar bytes originales fuera de PostgreSQL.
6. Persistir metadata, tamaño y SHA-256.
7. Rechazar duplicados dentro del mismo proceso.
8. Descargar el archivo original.

## Variables

```text
DATABASE_URL=postgresql+psycopg://pliegocheck:pliegocheck@localhost:56543/pliegocheck
PLIEGOCHECK_STORAGE_PATH=./var/documents
PLIEGOCHECK_MAX_FILE_SIZE_MB=20
PLIEGOCHECK_ALLOWED_WEB_ORIGINS=http://localhost:3000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

`.env` no se versiona. `.env.example` contiene solo valores locales no sensibles.

## Infraestructura Local

```bash
pnpm infra:up
pnpm db:migrate
pnpm db:check
pnpm dev:api
pnpm dev:web
```

PostgreSQL se publica en `localhost:56543` para evitar colisiones con instalaciones locales en
`5432`. Alembic aplica la migración inicial desde base vacía y `db:check` detecta divergencias entre
modelos y migraciones.

## Formatos Permitidos

```text
.pdf .doc .docx .xls .xlsx .csv .txt .png .jpg .jpeg
```

Validaciones aplicadas:

- archivo no vacío;
- tamaño máximo configurable;
- extensión final permitida;
- rechazo de rutas, rutas absolutas, nombres reservados y nombres excesivos;
- rechazo de doble extensión peligrosa;
- `Content-Type` declarado coherente;
- firma mágica básica cuando aplica;
- contenedores Office válidos y sin macros;
- duplicado por SHA-256 dentro del mismo proceso.

No se ejecutan macros, no se descomprime contenido de forma general y no se interpreta el documento.

## Carga Parcial

`POST /processes/{process_id}/documents` procesa cada archivo independientemente:

- `201`: todos almacenados;
- `207`: mezcla de almacenados y rechazados;
- `400`: todos rechazados.

La respuesta siempre incluye un resultado por archivo con `STORED` o `REJECTED` y un error
estructurado cuando aplica.

## Seguridad

Las respuestas no exponen `storage_key`, rutas absolutas ni temporales. La descarga verifica que el
documento pertenezca al proceso solicitado. Los eventos registran metadata mínima, nunca bytes ni
contenido documental.

## Limitaciones

Los documentos todavía no han sido extraídos ni analizados. La siguiente fase implementará inventario
y extracción documental.
