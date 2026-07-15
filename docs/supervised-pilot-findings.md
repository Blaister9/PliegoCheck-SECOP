# Hallazgos del piloto supervisado

Formato obligatorio: `id`, `source`, `category`, `description`, `evidence`, `severity`, `frequency`, `affected flow`, `recommended action`, `status`, `owner`.

| id | source | category | description | evidence | severity | frequency | affected flow | recommended action | status | owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SPF-001 | SECURITY_REVIEW | governance | No existe evidencia de validación con participantes humanos. | Plantillas con `USER_VALIDATION_PENDING`. | MEDIUM | current | usability | Ejecutar sesión autorizada y adjuntar acta/feedback. | OPEN_CONDITION | Product owner |
| SPF-002 | TECHNICAL_PILOT | delivery | La entrega externa real no forma parte de la prueba sin credenciales y allowlist explícitas. | Manifiesto `LOCAL_OR_DRY_RUN`. | OBSERVATION | expected | notifications | Mantener dry-run o proveedor local. | ACCEPTED | Operator |
| SPF-003 | TECHNICAL_PILOT | operations | El arranque web en Windows no resolvía `pnpm.cmd` y pasaba un separador extra a Next.js. | Dos intentos: API lista; web sin listener; regresión y tres despliegues posteriores correctos. | MEDIUM | reproduced | deploy/web | Resolver `pnpm.cmd`, corregir argumentos y cubrir con regresión. | CORRECTED_AND_VERIFIED | Engineering |
| SPF-004 | TECHNICAL_PILOT | configuration | El discovery se encoló, pero el worker inició con el conector SECOP deshabilitado. | Primera ejecución `FAILED` sanitizada; repetición limitada terminó `COMPLETED_WITH_WARNINGS`; controlador cubierto por regresión. | MEDIUM | reproduced once | opportunity discovery | Propagar el opt-in SECOP y los interruptores seguros al proceso worker mediante el controlador. | CORRECTED_AND_VERIFIED | Engineering |

No se asigna fuente `USER_SESSION` porque no existe evidencia de esa sesión.
