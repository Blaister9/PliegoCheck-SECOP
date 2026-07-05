# Criterios de aceptacion del MVP controlado

El MVP controlado se acepta solamente si:

- `pnpm pilot:eval` pasa.
- `pnpm controlled:eval` pasa.
- `pnpm controlled:data-scan` pasa.
- `pnpm mvp:eval` pasa.
- `pnpm mvp:data-scan` pasa.
- CI queda verde.
- No hay hallazgos `BLOCKER` abiertos en `docs/mvp-final-findings.md`.
- La documentacion identifica alcance, limitaciones, demo, no produccion y
  checklist de cierre.
- La decision final sigue delegada al motor deterministico.
- Los riesgos sin evidencia real quedan marcados como diferidos o pendientes,
  no como resueltos.

La aceptacion no equivale a aprobacion productiva.
