# Runbook

1. Evaluar readiness y preparar `.env.pilot` no versionado.
2. Ejecutar `pnpm pilot:supervised:deploy`, `validate` y `status`.
3. Seguir el checklist y registrar solo métricas agregadas.
4. Generar `pnpm pilot:supervised:report`.
5. Ejecutar `stop`; usar `reset -- --Confirm` solo cuando corresponda.
