# Registro de retroalimentacion del piloto

Bitacora de hallazgos del piloto controlado. Formato por entrada:

```text
Fecha | Escenario | Observacion | Severidad | Evidencia | Decision | Estado
```

Severidad: `critica`, `alta`, `media`, `baja`. Estado: `abierto`, `en curso`,
`cerrado`, `fuera-de-alcance`.

## Entradas iniciales (Microfase 11)

| Fecha | Escenario | Observacion | Severidad | Evidencia | Decision | Estado |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07-04 | Flujo e2e | El flujo completo (proceso→decision→reporte→ZIP) se ejecuta con datos sinteticos y auth activo. | baja | `evals/pilot-end-to-end` | Mantener como eval de regresion. | cerrado |
| 2026-07-04 | Decision | El resultado honesto del dataset es `PENDIENTE_INFORMACION`; la evidencia SUPPORTED (no verificada) exige revision humana. | media | `pilot/seed/expected-outcomes.json` | No forzar GO; documentar que se requiere verificacion de evidencia. | cerrado |
| 2026-07-04 | UX | Validar manualmente el recorrido en un navegador real (paneles de decision y reporte). | media | `docs/pilot-demo-checklist.md` | Ejecutar la checklist manual antes de cualquier piloto real. | abierto |
| 2026-07-04 | Normalizacion | El piloto usa normalizacion controlada (fixture), no OpenAI. Ajustar prompts con corpus real queda pendiente. | media | `docs/requirement-normalization.md` | Ajustar prompts con corpus real en una fase futura. | fuera-de-alcance |
| 2026-07-04 | Juridico | El resultado no constituye concepto juridico; se requiere revision juridica humana. | alta | `docs/security-and-governance.md` | Mantener aviso obligatorio y revision humana. | cerrado |
| 2026-07-04 | Autenticacion | SSO y MFA quedan fuera del piloto; auth local con roles es suficiente para la demo. | baja | `docs/authentication.md` | SSO/MFA en fase posterior. | fuera-de-alcance |
| 2026-07-04 | Almacenamiento | S3 real, PDF y firma digital quedan fuera del piloto. | baja | `docs/ADR-011-controlled-pilot.md` | Evaluar en despliegue controlado. | fuera-de-alcance |

## Cierre MVP controlado (Microfase 14)

| Fecha | Escenario | Observacion | Severidad | Evidencia | Decision | Estado |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07-04 | Usuarios piloto | No se recibió retroalimentación real de usuarios piloto en esta microfase. | media | `docs/mvp-final-findings.md` | Diferir validacion real a Microfase 15; no usar como evidencia de aceptacion de usuarios. | fuera-de-alcance |
| 2026-07-04 | Datos | Data scan controlado sigue como bloqueo obligatorio ante datos reales o secretos. | alta | `pnpm controlled:data-scan`, `pnpm mvp:data-scan` | Mantener como criterio de aceptacion del MVP controlado. | cerrado |

## Como agregar retroalimentacion

Durante una demo o validacion, agrega una fila por observacion. Referencia
evidencia con rutas del repositorio o identificadores de auditoria (no
identificadores locales de datos sinteticos que puedan variar por corrida).
