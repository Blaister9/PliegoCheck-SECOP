# Guia de desarrollo - PliegoCheck-SECOP

Como trabajar en el monorepo tras la Microfase 3. Las decisiones de stack estan en
[ADR-001](ADR-001-stack-and-architecture.md); la extraccion documental esta en
[ADR-003](ADR-003-document-extraction.md); las reglas para agentes de programacion, en
[AGENTS.md](../AGENTS.md).

## Requisitos

| Herramienta | Version | Como se fija |
| --- | --- | --- |
| Node.js | 22 (LTS) | [`.nvmrc`](../.nvmrc) |
| pnpm | 11.6.0 | `packageManager` en [`package.json`](../package.json) |
| Python | 3.12 | [`.python-version`](../.python-version) |
| uv | estable | gestiona el workspace Python y puede instalar Python |

## Instalacion

```bash
pnpm install
uv sync --all-packages
```

Ambos comandos son reproducibles: `pnpm-lock.yaml` y `uv.lock` estan versionados. En CI se usan
`--frozen-lockfile` y `--frozen`.

## Estructura

```text
apps/
  web/       Next.js + TypeScript. UI de importacion, inventario y preview de segmentos.
  api/       FastAPI. Procesos, documentos, inventario, extracciones, salud y contratos.
  worker/    CLI Python. Reclama trabajos y ejecuta extractores deterministas.
packages/
  schemas/   Contratos compartidos. Pydantic -> JSON Schema -> TypeScript.
scripts/     Automatizacion Node multiplataforma.
docs/        Documentacion fundacional, guias y ADRs.
.github/     CI (GitHub Actions).
```

## Ejecucion

- **Frontend:** `pnpm dev:web` -> http://localhost:3000
- **API:** `pnpm dev:api` -> http://localhost:8000 (`/docs`, `/openapi.json`)
- **Worker health:** `pnpm worker:health`
- **Procesar un trabajo:** `pnpm worker:run-once`
- **Drenar cola:** `pnpm worker:drain -- --max-jobs 10`
- **PostgreSQL:** `pnpm infra:up` publica PostgreSQL en `localhost:56543`
- **Migraciones:** `pnpm db:migrate`; `pnpm db:check`

Variables locales minimas en `.env.example`:

```text
DATABASE_URL
PLIEGOCHECK_STORAGE_PATH
PLIEGOCHECK_MAX_FILE_SIZE_MB
PLIEGOCHECK_EXTRACTION_MAX_SECONDS
PLIEGOCHECK_EXTRACTION_MAX_CHARACTERS
PLIEGOCHECK_EXTRACTION_MAX_PAGES
PLIEGOCHECK_EXTRACTION_MAX_SHEETS
PLIEGOCHECK_EXTRACTION_MAX_ROWS_PER_SHEET
PLIEGOCHECK_EXTRACTION_MAX_ZIP_ENTRIES
PLIEGOCHECK_EXTRACTION_MAX_UNCOMPRESSED_MB
PLIEGOCHECK_EXTRACTION_MAX_COMPRESSION_RATIO
PLIEGOCHECK_WORKER_MAX_ATTEMPTS
PLIEGOCHECK_ALLOWED_WEB_ORIGINS
NEXT_PUBLIC_API_BASE_URL
```

## Contratos compartidos

La definicion canonica de cada contrato es un modelo Pydantic en
`packages/schemas/src/pliegocheck_schemas/`. De ahi se generan:

1. `generated/*.schema.json` - JSON Schema.
2. `generated/*.ts` - interfaces TypeScript.
3. `generated/*.enums.ts` - constantes de runtime para TypeScript.

```bash
pnpm schemas:generate
pnpm schemas:check
```

Los artefactos generados se versionan y nunca se editan a mano.

## Validacion

```bash
pnpm check
```

O por partes:

```bash
pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
pnpm extraction:test
pnpm schemas:check
pnpm build
```

La CI ejecuta instalacion reproducible, migraciones, `db:check`, contratos sincronizados, formato,
lint, typecheck, pruebas, pruebas dedicadas de extraccion, build web y verificacion de repositorio
sin cambios tras generar.

## Estado funcional real

Implementado:

- importacion manual de procesos;
- carga documental segura;
- almacenamiento local con SHA-256;
- duplicados por proceso;
- descarga del original;
- cola transaccional inicial en PostgreSQL;
- extractores deterministas para PDF con texto, DOCX, XLSX, CSV y TXT;
- estados explicitos para imagenes sin OCR, documentos cifrados y formatos no soportados;
- inventario y preview de segmentos en API y web.

No implementado todavia: OCR, normalizacion de requisitos, agentes de IA, integracion automatica con
SECOP II, autenticacion, S3 real y motor GO / NO GO ejecutable.
