# Guia de desarrollo - PliegoCheck-SECOP

Como trabajar en el monorepo tras la Microfase 8. Las decisiones de stack estan en
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
  web/       Next.js + TypeScript. UI de procesos, requisitos, empresas y evidencias.
  api/       FastAPI. Procesos, documentos, extracciones, requisitos, empresas y contratos.
  worker/    CLI Python. Reclama trabajos y ejecuta extractores/normalizadores deterministas.
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
- **Procesar normalizacion:** `pnpm normalization:run-once`
- **Drenar normalizaciones:** `pnpm normalization:drain -- --max-jobs 10`
- **Procesar evaluacion financiera:** `pnpm financial:run-once`
- **Drenar evaluaciones financieras:** `pnpm financial:drain -- --max-jobs 10`
- **Procesar evaluacion especializada:** `pnpm specialized:run-once`
- **Drenar evaluaciones especializadas:** `pnpm specialized:drain -- --max-jobs 10`
- **Procesar decision preliminar:** `pnpm decision:run-once`
- **Drenar decisiones:** `pnpm decision:drain -- --max-jobs 10`
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
PLIEGOCHECK_AI_ENABLED
OPENAI_API_KEY
OPENAI_NORMALIZATION_MODEL
OPENAI_NORMALIZATION_REASONING_EFFORT
OPENAI_NORMALIZATION_BACKGROUND
OPENAI_NORMALIZATION_MAX_OUTPUT_TOKENS
OPENAI_NORMALIZATION_TIMEOUT_SECONDS
OPENAI_NORMALIZATION_POLL_INTERVAL_SECONDS
OPENAI_NORMALIZATION_MAX_CALLS_PER_RUN
OPENAI_NORMALIZATION_MAX_SEGMENTS_PER_BATCH
OPENAI_NORMALIZATION_MAX_CHARACTERS_PER_BATCH
OPENAI_NORMALIZATION_MAX_TOTAL_CHARACTERS
OPENAI_NORMALIZATION_MAX_RETRIES
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
pnpm company:test
pnpm company:snapshot-check
pnpm normalization:test
pnpm normalization:eval
pnpm financial:test
pnpm financial:eval
pnpm specialized:test
pnpm specialized:eval
pnpm decision:policy-check
pnpm decision:test
pnpm decision:eval
pnpm schemas:check
pnpm build
```

La CI ejecuta instalacion reproducible, migraciones, `db:check`, contratos sincronizados, pruebas de
perfil de empresa y snapshot, pruebas y evals de normalizacion, formato, lint, typecheck, pruebas,
pruebas y evals de evaluacion financiera, pruebas y evals de evaluadores especializados,
politica/pruebas/evals de decision, pruebas dedicadas de extraccion, build web y verificacion de
repositorio sin cambios tras generar.

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
- inventario y preview de segmentos en API y web;
- normalizacion de requisitos con OpenAI Responses API configurable;
- prompts versionados;
- snapshot y batching deterministico;
- validacion de evidencia;
- requisitos, evidencias, relaciones y candidatos rechazados;
- UI de revision de requisitos;
- perfiles de empresa con datos juridicos, RUP, UNSPSC, finanzas, experiencia, personal,
  certificaciones y capacidades;
- carga de evidencias empresariales con SHA-256 y extraccion documental reutilizada;
- vinculos dato-evidencia validados contra extracciones y segmentos;
- completitud deterministica del perfil sin decision GO / NO GO;
- snapshots inmutables de perfil para evaluaciones futuras;
- evaluacion financiera deterministica por requisito contra snapshots publicados;
- formulas financieras versionadas;
- cola PostgreSQL y worker financiero;
- revision manual auditada de resultados financieros;
- decision preliminar deterministica con politica versionada `pliegocheck-default` 1.0.0;
- hallazgos canonicos, cobertura por categoria, reglas, acciones y review/override auditados;
- worker `decision-run-once` / `decision-drain`, API y UI de decision preliminar;
- evaluadores juridico, experiencia y tecnico deterministas contra snapshots publicados;
- worker `specialized-run-once` / `specialized-drain`, API, UI, revision auditada y adaptadores de
  decision para resultados especializados.

No implementado todavia: OCR, integracion automatica con SECOP II, autenticacion y S3 real.
Categorias fuera de financiero, juridico, experiencia y tecnico permanecen `NOT_EVALUATED` y
bloquean `GO`.
