# Politica de decision v1 (pliegocheck-default 1.0.0)

Parametros validados de la politica de decision. El codigo del motor contiene
las reglas tipadas (`apps/api/src/pliegocheck_api/decision/rules.py`); este
archivo contiene unicamente parametros. No es un lenguaje de expresiones:
no se evalua con `eval`, `exec` ni SQL dinamico.

Reglas de gestion:

- Cambiar cualquier parametro exige crear una nueva carpeta de version
  (`v2/`, ...) con un nuevo `semantic_version`. Las versiones publicadas son
  inmutables: si el hash del contenido cambia sin cambiar la version, la API
  rechaza la politica con `DECISION_POLICY_INVALID`.
- Cada `DecisionRun` referencia el snapshot exacto de la politica usada
  (tabla `decision_policy_versions`), de modo que las decisiones historicas
  son reproducibles aunque el repositorio avance.

Semantica principal (ver `docs/decision-policy.md`):

- `precedence`: orden inequivoco de resultados; el primero que aplique gana.
- `blocking_criticalities`: criticidades que convierten un incumplimiento
  obligatorio confirmado y no remediable en `NO_GO`.
- `unknown_behavior` / `conflict_behavior` / `partial_behavior`: la ausencia
  de informacion nunca es cumplimiento; estas entradas producen
  `PENDIENTE_INFORMACION`.
- `no_cargar_requirements`: `NO_CARGAR` exige un bloqueo operativo explicito
  (`submission_blocker=true`); nunca se infiere.
- `partner_requirements`: `BUSCAR_ALIADO` exige `partner_solvable=true`
  establecido explicitamente por un evaluador especializado o revision humana.
