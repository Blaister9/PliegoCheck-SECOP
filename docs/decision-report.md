# Reporte ejecutivo de decision

El reporte ejecutivo resume una decision preliminar ya emitida por el motor deterministico. Su
objetivo es apoyar la revision del comite de licitaciones con evidencia, riesgos y acciones
pendientes en un formato navegable.

## Regla principal

El reporte no decide. No recalcula requisitos, no cambia hallazgos, no modifica acciones y no emite
recomendaciones nuevas. Si falta evidencia critica, el resultado reportado sigue siendo
`PENDIENTE_INFORMACION`.

## Flujo

1. La API valida que el proceso tenga una `DecisionRun` completada con resultado.
2. Se construye un input manifest con decision, reviews, acciones, hallazgos, reglas, evaluadores y
   hash de templates.
3. Si ya existe un paquete completado con el mismo input digest y `force=false`, la API reutiliza el
   paquete existente.
4. Si no existe, se encola `DecisionReportJob`.
5. El worker genera los artefactos desde el snapshot persistido y los guarda en storage.
6. La UI permite crear, listar, previsualizar y descargar artefactos o ZIP.

## Avisos obligatorios

Todo reporte muestra estas restricciones:

- Este reporte no constituye concepto juridico ni recomendacion oficial de participacion.
- El paquete resume una decision preliminar existente; no recalcula evaluaciones ni modifica el
  resultado del motor.
- Los artefactos deben revisarse antes de cualquier uso externo.

## Comandos

```bash
pnpm report:run-once
pnpm report:drain -- --max-jobs 10
pnpm report:test
pnpm report:eval
```

## API

En Microfase 10 estos endpoints requieren sesion valida cuando `PLIEGOCHECK_AUTH_ENABLED=true`.
La autorizacion se evalua por permisos de rol; los errores incluyen `request_id` y se auditan cuando
corresponde.

- `POST /processes/{process_id}/decision-reports`
- `GET /processes/{process_id}/decision-reports`
- `GET /processes/{process_id}/decision-reports/{package_id}`
- `GET /processes/{process_id}/decision-reports/{package_id}/preview`
- `GET /processes/{process_id}/decision-reports/{package_id}/artifacts/{artifact_id}/download`
- `GET /processes/{process_id}/decision-reports/{package_id}/download`
- `POST /processes/{process_id}/decision-reports/{package_id}/retry`

## Estados

Los jobs usan `PENDING`, `RUNNING`, `COMPLETED`, `COMPLETED_WITH_WARNINGS`, `FAILED` y
`CANCELLED`. Los paquetes usan los mismos estados de ciclo de vida, con `DRAFT` mientras el job aun
no ha materializado los artefactos.
