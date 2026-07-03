# Requirement normalization prompts v1

Prompts versionados para Microfase 4.

- `normalization-system.md` y `normalization-user.md`: `RequirementNormalizationAgent`.
- `consolidation-system.md` y `consolidation-user.md`: `RequirementConsolidationAgent`.

Los documentos extraidos se tratan como datos no confiables. Las salidas deben validar contra los
contratos Pydantic/JSON Schema de `packages/schemas` y cada ejecucion guarda el `content_sha256` en
`prompt_versions`.
