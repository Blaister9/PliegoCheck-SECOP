# Dataset sintetico del piloto

Descripcion del dataset controlado usado por el piloto end-to-end. Todo es
ficticio y esta marcado como piloto. La fuente autoritativa es el modulo
`apps/worker/src/pliegocheck_worker/pilot/dataset.py`; los archivos en
`pilot/seed/` son copias legibles.

## Usuarios sinteticos

Cuatro usuarios con dominio `@pilot.pliegocheck.local`:

| Rol | Email | Permisos clave |
| --- | --- | --- |
| ADMIN | admin@pilot.pliegocheck.local | usuarios, auditoria, configuracion |
| ANALYST | analyst@pilot.pliegocheck.local | procesos, empresas, evaluaciones, decision, reporte |
| REVIEWER | reviewer@pilot.pliegocheck.local | revision/override de decision, descarga de reporte |
| VIEWER | viewer@pilot.pliegocheck.local | lectura y descarga limitada |

Las contrasenas **no se versionan**. Se pasan por argumento (`--password`) o
variable de entorno; el valor demo local por defecto es
`DemoOnly-ChangeMe-12345` (solo local, cambiar en cualquier entorno compartido).

## Proceso sintetico

- Titulo: *Proceso Piloto Sintetico 001 - Mesa de ayuda*.
- Entidad ficticia: *Entidad Demo de Contratacion*.
- Documentos: un pliego `.txt` y un anexo financiero `.csv`, ambos sinteticos,
  con requisitos financieros, juridicos, de experiencia y tecnicos.

## Requisitos normalizados (fixture controlado)

| Categoria | Criticidad | Resultado esperado |
| --- | --- | --- |
| FINANCIAL (liquidez ≥ 1.2) | HIGH | COMPLIES (revision humana) |
| FINANCIAL (capital de trabajo ≥ 500M) | MEDIUM | DOES_NOT_COMPLY (no bloqueante) |
| FINANCIAL (solidez financiera adecuada) | MEDIUM | UNKNOWN (ambiguo) |
| LEGAL (RUP vigente) | HIGH | COMPLIES (revision humana) |
| EXPERIENCE (contratos similares) | HIGH | COMPLIES (revision humana) |
| TECHNICAL (certificacion ISO 9001) | HIGH | COMPLIES (revision humana) |

La normalizacion del piloto es **controlada** (fixture), no llama a OpenAI. Esto
mantiene el dataset alineado con los evaluadores y el resultado reproducible.

## Empresa sintetica y snapshot

Empresa *Empresa Demo PliegoCheck S.A.S.* (NIT ficticio `900123456`), con un
snapshot **publicado** que incluye: periodos y metricas financieras (liquidez,
activos y pasivos corrientes), RUP, registros juridicos, experiencia, personal,
certificaciones y capacidades. Toda la evidencia es `SUPPORTED` (declarada con
soporte, no verificada), lo que exige revision humana en las evaluaciones.

## Resultado esperado

Ver `pilot/seed/expected-outcomes.json`. La decision preliminar esperada es
**`PENDIENTE_INFORMACION`**: hay un cumplimiento, un incumplimiento no
bloqueante, un `UNKNOWN` y revision humana pendiente. **El piloto no fuerza GO.**

## Reproducibilidad

`pnpm pilot:prepare` es idempotente: reutiliza la empresa piloto y publica una
nueva version de snapshot; crea un proceso y una normalizacion nuevos por
corrida para conservar el historico. `pnpm pilot:reset -- --confirm` elimina
unicamente los datos de piloto (usuarios `@pilot.pliegocheck.local`, el proceso
piloto y la empresa piloto), nunca datos no sinteticos ni `.env`.

## Diferencias con datos reales

- No se llama a OpenAI: la normalizacion es un fixture controlado.
- La evidencia es declarada con soporte sintetico, no verificada por un tercero.
- Los umbrales y textos son ilustrativos; no representan un pliego real.
