# Piloto controlado end-to-end (Microfase 11)

Este directorio contiene el **dataset sintetico** del piloto y los guiones para
prepararlo, ejecutarlo y resetearlo. Todo es ficticio y esta marcado como piloto.

> **Solo datos sinteticos.** No hay NIT reales, nombres reales, identificaciones
> reales ni documentos reales. No se llama a OpenAI en el flujo de piloto.

## Fuente autoritativa

La fuente autoritativa del dataset es el modulo Python
`apps/worker/src/pliegocheck_worker/pilot/dataset.py`. Los archivos JSON en
`seed/` son **copias legibles** que reflejan ese modulo para documentacion.
El orquestador consume el modulo Python, no estos JSON.

## Estructura

```text
pilot/
├── README.md                     este archivo
├── seed/                         copias legibles del dataset sintetico
│   ├── users.json                4 usuarios (admin, analyst, reviewer, viewer)
│   ├── process.json              proceso sintetico
│   ├── company.json              empresa sintetica y snapshot
│   ├── requirements.json         requisitos normalizados controlados
│   ├── evaluations.json          dominios evaluados
│   └── expected-outcomes.json    resultado esperado (sin IA)
├── documents/                    documentos sinteticos del proceso
│   ├── proceso/
│   └── empresa/
├── scripts/                      wrappers PowerShell de los comandos pnpm
│   ├── prepare-pilot.ps1
│   ├── run-pilot.ps1
│   └── reset-pilot.ps1
├── demo-script.md                guion de demo end-to-end
└── last-run-summary.example.json ejemplo sanitizado de resumen de corrida
```

## Comandos

Las contrasenas demo se pasan por variable de entorno o argumento; el valor por
defecto sintetico es `DemoOnly-ChangeMe-12345` (solo local).

```powershell
pnpm infra:up            # PostgreSQL local
pnpm db:migrate          # migraciones
pnpm pilot:readiness     # diagnostico de preparacion
pnpm pilot:prepare       # siembra usuarios, proceso, documentos, empresa, snapshot
pnpm pilot:run           # ejecuta el flujo end-to-end y devuelve un resumen JSON
pnpm pilot:reset --confirm      # elimina SOLO datos de piloto
pnpm pilot:eval          # eval automatizado del flujo completo (auth activo)
```

Detalle en [docs/pilot-dataset.md](../docs/pilot-dataset.md),
[docs/demo-script.md](../docs/demo-script.md) y
[docs/pilot-demo-checklist.md](../docs/pilot-demo-checklist.md).
