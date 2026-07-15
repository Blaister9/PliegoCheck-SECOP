# ADR-021 — Piloto técnico supervisado

## Decisión

Operar Microfase 21 como extensión del despliegue controlado: manifiesto conservador, comandos raíz idempotentes, consultas SECOP live opt-in y evidencia agregada sanitizada. Los reportes se generan bajo `var/` y no se versionan. El perfil debe tener snapshot publicado; si no hay uno autorizado se usa el dataset sintético.

La sesión técnica y una sesión humana son evidencias distintas. La navegación automatizada no cuenta como feedback. Sin evidencia humana, el máximo gate posible con flujo técnico completo es `PILOT_READY_WITH_CONDITIONS`.

## Consecuencias

- No se fijan procesos SECOP, payloads, documentos, identidades ni destinos en código.
- `deploy` conserva datos, `validate` es de solo lectura, `stop` conserva volúmenes y `reset` exige confirmación.
- No se habilita producción, envío externo real, transacción SECOP ni probabilidad de adjudicación.
