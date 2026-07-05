# Guion de demo end-to-end (piloto controlado)

Demostracion del flujo completo de PliegoCheck-SECOP con **datos sinteticos**.
No usa OpenAI ni datos reales. Ver tambien [pilot-demo-checklist.md](pilot-demo-checklist.md).

## 0. Requisitos

- PostgreSQL local (`pnpm infra:up`), migraciones aplicadas (`pnpm db:migrate`).
- Variables locales en `.env` (ver `.env.example`). Para el piloto con auth se
  necesita `PLIEGOCHECK_AUTH_SECRET_KEY` (sintetico, solo local).

## 1. Levantar infraestructura y migrar

```powershell
pnpm infra:up
pnpm db:migrate
pnpm db:check
```

## 2. Crear un admin real (una vez)

```powershell
$env:PLIEGOCHECK_AUTH_ENABLED = "true"
"MiClaveLocalSintetica-123456" | uv run pliegocheck-api users create-admin --email admin@pilot.pliegocheck.local --display-name "Admin" --password-stdin
```

> El comando de piloto (`pnpm pilot:prepare`) tambien crea los cuatro usuarios
> sinteticos (admin/analyst/reviewer/viewer) con la contrasena demo.

## 3. Preparar el dataset sintetico

```powershell
pnpm pilot:readiness       # diagnostico
pnpm pilot:prepare         # usuarios, proceso, documentos, extraccion, empresa, snapshot
```

## 4. Iniciar API y web

```powershell
pnpm dev:api               # http://localhost:8000  (/docs, /openapi.json)
pnpm dev:web               # http://localhost:3000
```

## 5. Recorrido en la web

1. `/login` como `admin@pilot.pliegocheck.local` → ver usuarios y auditoria.
2. Login como `analyst@pilot.pliegocheck.local`.
3. Abrir el **Proceso Piloto Sintetico 001** → ver documentos y segmentos extraidos.
4. Ver la **empresa Empresa Demo PliegoCheck S.A.S.** y su snapshot publicado.
5. Ejecutar (o revisar) evaluacion financiera y evaluaciones especializadas.
6. Abrir el panel de **Decision preliminar** → resultado `PENDIENTE_INFORMACION`,
   reglas disparadas, cobertura, hallazgos (cumple / no cumple / UNKNOWN) y acciones.
7. Ver el **reporte ejecutivo** y **descargar el paquete ZIP**.
8. Login como `reviewer@pilot.pliegocheck.local` → confirmar u override (el
   resultado del motor no cambia; se registra la revision).
9. Login como `viewer@pilot.pliegocheck.local` → confirmar solo lectura.
10. Login como admin → ver eventos de auditoria del recorrido.

## 6. Ejecucion automatizada equivalente

Sin navegador, el flujo completo se ejecuta y valida con:

```powershell
pnpm pilot:run     # imprime un PilotRunSummary JSON
pnpm pilot:eval    # eval end-to-end con auth (usado por CI)
```

## 7. Backup y cierre

```powershell
pnpm ops:backup    # backup local con manifest y hashes (excluye .env)
pnpm pilot:reset --confirm   # elimina SOLO datos de piloto
pnpm infra:down
```

## Advertencias de la demo

- El resultado es una **decision preliminar deterministica** que requiere
  revision humana; no es un concepto juridico ni garantiza habilitacion.
- La ausencia de evaluacion en una dimension nunca se interpreta como cumplimiento.
- Todo el dataset es sintetico; no representa entidades, empresas ni personas reales.
