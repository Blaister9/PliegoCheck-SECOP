# Guion de demo del piloto

El guion completo, paso a paso, vive en
[docs/demo-script.md](../docs/demo-script.md). El checklist operativo esta en
[docs/pilot-demo-checklist.md](../docs/pilot-demo-checklist.md).

Resumen rapido (solo datos sinteticos):

```powershell
pnpm infra:up
pnpm db:migrate
pnpm pilot:prepare
pnpm dev:api        # y en otra terminal: pnpm dev:web
# recorrido web: login por rol -> proceso -> empresa -> evaluaciones -> decision -> reporte -> ZIP -> auditoria
pnpm pilot:run      # o el flujo automatizado equivalente
pnpm ops:backup
pnpm pilot:reset --confirm
pnpm infra:down
```
