# ADR-011 — Piloto controlado end-to-end con datos sinteticos

- **Estado:** Aceptado
- **Fecha:** 2026-07-04
- **Decisores:** Equipo PliegoCheck

## Contexto

Tras la Microfase 10 (endurecimiento operativo y autenticacion), el producto
tiene todas las capacidades para un flujo GO / NO GO auditable. La Microfase 11
no agrega capacidades grandes: valida que el producto **se pueda demostrar y usar
de punta a punta** con datos completamente sinteticos, de forma reproducible, y
documenta la retroalimentacion para fases futuras.

## Decision

1. **Dataset sintetico autoritativo en Python.** La fuente del dataset es
   `apps/worker/src/pliegocheck_worker/pilot/dataset.py`; `pilot/seed/*.json` son
   copias legibles. Todo el dato es ficticio y esta marcado como piloto.
2. **Orquestador de piloto en el worker.** El piloto necesita coordinar la API
   (creacion de proceso, carga de documentos, evaluaciones, decision, reporte) y
   los orquestadores del worker (extraccion, financiera, especializada, decision,
   reporte). Como el worker depende de la API (y no al reves), el orquestador vive
   en `pliegocheck_worker.pilot`. Impulsa la API con `TestClient` in-process
   escribiendo en la base de datos configurada, sin necesidad de un servidor vivo.
3. **Normalizacion controlada (fixture), sin OpenAI.** Los requisitos se siembran
   directamente para mantenerlos alineados con los evaluadores y garantizar un
   resultado reproducible. Los documentos sinteticos si pasan por extraccion real.
4. **Comandos de piloto en el CLI del worker.** `pliegocheck-worker pilot-prepare
   | pilot-run | pilot-reset | pilot-readiness`, expuestos como `pnpm pilot:*`.
5. **Readiness por CLI, sin endpoint nuevo.** Se prefiere scripts/evals sobre
   endpoints. La preparacion del piloto se consulta con `pnpm pilot:readiness`;
   no se agrega `/admin/pilot-readiness` para no ampliar la superficie de la API.
6. **Eval end-to-end con auth activo.** `evals/pilot-end-to-end` ejecuta el flujo
   completo con autenticacion habilitada y valida roles, decision, reporte, ZIP,
   auditoria, logout y coincidencia con `expected-outcomes`. Corre en CI.
7. **Resultado honesto, no forzado.** El dataset produce `PENDIENTE_INFORMACION`
   (un cumplimiento, un incumplimiento, un `UNKNOWN`, revision humana pendiente).
   No se maquilla el dataset para forzar `GO`.

## Alternativas consideradas

- **Impulsar el flujo por HTTP contra un servidor vivo.** Descartada para CI:
  fragil y lenta. `TestClient` in-process escribe en la misma base de datos y es
  reproducible. La demo manual si usa la API/web reales.
- **Endpoint `/admin/pilot-readiness`.** Descartada por ahora: el CLI cubre la
  necesidad sin ampliar la API (seccion 21 del alcance lo permite).
- **Sembrar la empresa por la API de empresa.** Descartada por robustez: el
  snapshot se siembra con un payload sintetico que satisface a la vez al
  evaluador financiero y a los especializados; la demo manual si recorre la UI.
- **Usar el proveedor fake de normalizacion.** Descartada: no permite controlar
  con precision los requisitos por dominio; el fixture directo si.

## Consecuencias

- El flujo end-to-end queda cubierto por un eval de regresion en CI.
- El piloto es reproducible en local sin servicios externos ni OpenAI.
- `httpx` pasa a ser dependencia explicita del worker (TestClient en runtime).
- La demo manual sigue siendo necesaria para validar UX en un navegador real
  (registrado en el log de retroalimentacion).

## Fuera de alcance (registrado)

Datos reales, SSO, MFA, S3 real, integracion SECOP, OCR, firma digital, PDF,
envio por correo, notificaciones, scoring/ranking, nuevos evaluadores, nuevas
reglas de decision, y despliegue productivo. Se abordan en fases posteriores.

## Criterios de no salida a piloto real

No promover a un piloto con datos reales hasta que exista: validacion UX manual
en navegador, verificacion de evidencia por terceros (no solo `SUPPORTED`),
revision juridica humana del flujo, y endurecimiento de despliegue (Microfase 12).
