# ADR-007 - Motor deterministico de decision preliminar

## Estado

Aceptada. Microfase 7.

## Contexto

La plataforma ya cuenta con requisitos normalizados, snapshots publicados de empresa y evaluacion
financiera deterministica. Faltaba combinar esos insumos en una decision preliminar auditable sin
delegar el resultado a IA.

## Decision

Implementar el motor en `apps/api/src/pliegocheck_api/decision` como codigo puro y tipado:

- contratos compartidos en Pydantic, JSON Schema y TypeScript;
- politica versionada en `config/decision-policies/v1`;
- snapshot persistido de politica en `decision_policy_versions`;
- hallazgo canonico `DecisionInputFinding`;
- adaptador real inicial solo para `FINANCIAL`;
- cobertura por requisito y categoria;
- reglas deterministicas con precedencia unica;
- cola PostgreSQL `decision_jobs` y worker `decision-run-once` / `decision-drain`;
- API y UI de decision preliminar;
- review, override, acciones y eventos auditados.

## Reglas

- El motor no usa IA, no llama OpenAI, no accede a base de datos y no usa reloj global.
- El worker inyecta `effective_at`, carga los inputs y persiste el resultado.
- Requisitos obligatorios sin adaptador quedan `NOT_EVALUATED`.
- `GO` exige cobertura obligatoria completa y cumplimiento de todos los obligatorios aplicables.
- `NO_CARGAR` exige `submission_blocker=true` explicito.
- `BUSCAR_ALIADO` exige `partner_solvable=true` explicito.
- `GO_CONDICIONADO` exige brecha remediable y codigos de condicion.
- Los overrides humanos preservan `engine_outcome` y solo cambian `effective_outcome`.

## Consecuencias

La decision ya es ejecutable, reproducible y trazable, pero sigue siendo preliminar. Mientras solo
exista el adaptador financiero, los dominios juridico, tecnico, experiencia y demas quedan como
brechas de cobertura y normalmente producen `PENDIENTE_INFORMACION`.

## Fuera de alcance

Evaluadores juridico, tecnico, experiencia, personal, garantias, cronograma, economico,
operacional, documental y riesgos. Tambien quedan fuera scoring, ranking, concepto juridico,
autenticacion y uso de IA dentro del motor.
