# Guía de desarrollo — PliegoCheck-SECOP

Cómo trabajar en el monorepo tras la Microfase 1. Las decisiones de stack están en [ADR-001](ADR-001-stack-and-architecture.md); las reglas para agentes de programación, en [AGENTS.md](../AGENTS.md).

## Requisitos

| Herramienta | Versión | Cómo se fija |
| --- | --- | --- |
| Node.js | 22 (LTS) | [`.nvmrc`](../.nvmrc) |
| pnpm | 11.6.0 | `packageManager` en [`package.json`](../package.json) (corepack) |
| Python | 3.12 | [`.python-version`](../.python-version) |
| uv | estable | gestiona el workspace Python y puede instalar el propio Python |

## Instalación

```bash
pnpm install            # workspace pnpm: apps/web y packages/schemas
uv sync --all-packages  # workspace uv: apps/api, apps/worker y packages/schemas
```

Ambos comandos son reproducibles: `pnpm-lock.yaml` y `uv.lock` están versionados. En CI se usan `--frozen-lockfile` y `--frozen`.

## Estructura

```text
apps/
├── web/       Next.js + TypeScript (App Router). UI mínima.
├── api/       FastAPI. Endpoints /health/live, /health/ready y /contracts.
└── worker/    CLI Python de diagnóstico. Sin cola real todavía.
packages/
└── schemas/   Contratos compartidos. Modelo canónico Pydantic → JSON Schema → TypeScript.
scripts/       Automatización Node multiplataforma (generación de contratos).
docs/          Documentación fundacional y ADRs.
.github/       CI (GitHub Actions).
```

## Ejecución

- **Frontend:** `pnpm dev:web` → http://localhost:3000
- **API:** `pnpm dev:api` → http://localhost:8000 (OpenAPI interactivo en `/docs`, JSON en `/openapi.json`)
- **Worker:** `pnpm worker:health` — imprime el diagnóstico en JSON por stdout (logs por stderr) y termina. No procesa trabajos: la cola real llega en la Microfase 3.

## Contratos compartidos

La definición canónica de cada contrato es un **modelo Pydantic** en `packages/schemas/src/pliegocheck_schemas/`. De ahí se generan, de forma determinística:

1. `generated/normalized-requirement.schema.json` — JSON Schema (draft 2020-12).
2. `generated/normalized-requirement.ts` — interfaz TypeScript (vía `json-schema-to-typescript`).
3. `generated/normalized-requirement.enums.ts` — constantes de runtime para TypeScript.

Comandos:

```bash
pnpm schemas:generate  # regenera los tres artefactos y los formatea
pnpm schemas:check     # regenera y falla si el repositorio queda con diferencias
```

Los artefactos generados **se versionan** y nunca se editan a mano. La CI ejecuta `schemas:check`: si el modelo canónico y lo generado divergen, el build falla.

Para cambiar un contrato: edita el modelo Pydantic, ejecuta `pnpm schemas:generate`, actualiza los ejemplos de `packages/schemas/examples/` si aplica y confirma todo junto.

## Validación

```bash
pnpm check   # suite integral: formato, lint, typecheck, tests, schemas y build
```

O por partes: `pnpm format:check`, `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build`. Los comandos raíz cubren ambos ecosistemas (Prettier+Ruff, ESLint+Ruff, tsc+mypy, vitest+pytest).

La CI ([.github/workflows/ci.yml](../.github/workflows/ci.yml)) ejecuta lo mismo en un entorno limpio sobre cada PR y sobre `main`, y verifica además que el repositorio quede sin cambios tras regenerar contratos.

Notas:

- El formato Prettier no cubre la documentación fundacional (`docs/`, `README.md`, `AGENTS.md`): es prosa, no código (ver `.prettierignore`).
- `mypy` corre en modo `strict`; `ruff` aplica lint y formato con las reglas del `pyproject.toml` raíz.

## Estado funcional real

Implementado: esqueleto ejecutable, contrato `NormalizedRequirement` v1.0.0 consumido por API (endpoint `/contracts`) y web (página principal), pruebas de los tres servicios y del contrato, CI completa.

No implementado todavía (ver [roadmap](roadmap.md)): carga de procesos y documentos, extracción documental, agentes de IA, integración SECOP II, base de datos, autenticación, motor de decisión ejecutable, contenedores y despliegue.
