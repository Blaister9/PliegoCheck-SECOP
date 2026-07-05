# Alcance del MVP controlado

## Incluido

- Flujo end-to-end con datos sinteticos de piloto.
- API local con autenticacion configurable y roles `ADMIN`, `ANALYST`,
  `REVIEWER` y `VIEWER`.
- Aplicacion web para operar procesos, evidencias, evaluaciones, decision y
  reporte.
- Motor deterministico de decision con trazabilidad requisito -> evidencia ->
  decision.
- Reporte y ZIP sin secretos ni rutas fisicas.
- Runbooks de despliegue controlado, rollback, backup y validacion.
- Evals de piloto, despliegue controlado, cierre MVP y data scan.

## Excluido

- Produccion.
- Datos reales de procesos o empresas.
- SSO, MFA y gestion empresarial de identidades.
- SECOP en linea, OCR, firma digital, notificaciones y correo.
- S3 obligatorio u otro almacenamiento productivo.
- Garantias juridicas, comerciales o de cumplimiento normativo.

## Supuesto operativo

El modo esperado del MVP controlado usa datos sinteticos y `PLIEGOCHECK_AI_ENABLED=false`.
