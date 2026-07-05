# Hallazgos post-piloto

Fuente primaria: [pilot-feedback-log.md](pilot-feedback-log.md) y
`evals/pilot-end-to-end`.

| id | fecha | area | observacion | severidad | impacto | decision | estado | PR/fix asociado | fase futura |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PPF-001 | 2026-07-04 | UX web | Falta validacion manual de navegador real para paneles de decision, reporte y ZIP. | HIGH | Puede bloquear una demo si hay friccion visual o error de navegador no cubierto por TestClient. | Crear checklist ejecutable y smoke web existente; exigir ejecucion antes de despliegue controlado. | RESUELTO_DOCUMENTADO | Microfase 12 | Microfase 13 ejecuta con usuarios piloto |
| PPF-002 | 2026-07-04 | Deployment | No existia eval dedicado de deployment readiness. | HIGH | Un entorno piloto podria arrancar con CORS, auth o storage incompletos. | Agregar `pnpm deployment:eval` y CI. | RESUELTO | Microfase 12 | n/a |
| PPF-003 | 2026-07-04 | Backup | Backup documentado, pero sin comando especifico de verificacion pre-despliegue. | HIGH | Riesgo de demo sin restore path ni manifest verificado. | Agregar `pnpm deployment:backup-check` y checklist. | RESUELTO | Microfase 12 | n/a |
| PPF-004 | 2026-07-04 | Normalizacion | El piloto usa fixture controlado y no OpenAI real. | MEDIUM | No valida calidad de prompts con corpus real. | Diferir; no usar datos reales en esta microfase. | DEFERRED | n/a | Microfase futura de corpus real |
| PPF-005 | 2026-07-04 | Juridico | El resultado no constituye concepto juridico. | HIGH | Uso externo sin revision humana seria riesgoso. | Mantener avisos y revision humana obligatoria. | RESUELTO_DOCUMENTADO | Microfases 9-12 | Microfase 13 validar con usuarios |
| PPF-006 | 2026-07-04 | Seguridad | SSO/MFA quedan fuera de alcance. | LOW | Auth local es suficiente para demo, no para adopcion institucional amplia. | Documentar limitacion. | DEFERRED | n/a | Posterior a piloto controlado |
| PPF-007 | 2026-07-04 | Storage | S3 real y PDF siguen fuera de alcance. | LOW | El piloto controlado depende de storage local y artefactos HTML/ZIP. | Documentar limitacion y rollback local. | DEFERRED | n/a | Microfase futura de despliegue productivo |

No hay hallazgos `CRITICAL` abiertos. Los `HIGH` que bloqueaban demo/piloto
controlado quedan cubiertos por checklist, eval y backup check.
