# Alcance del MVP controlado

La extensión de Microfase 22 incluye un paquete técnico para despliegue institucional restringido validable localmente. No amplía el MVP a producción ni acredita infraestructura institucional real; SSO/MFA y validación con usuarios autorizados permanecen fuera de alcance.

Microfase 21 permite un piloto técnico supervisado con procesos públicos SECOP y perfil sintético o autorizado, dentro de límites conservadores. Los payloads/documentos live no se versionan y la validación humana sigue siendo evidencia separada. Esto no amplía el alcance a producción.

- Entrega externa piloto opt-in por SMTP o webhook HMAC, con dry-run, allowlists y datos sintéticos; no producción ni envío masivo.

El alcance controlado incluye alertas internas, digest en aplicación y entrega externa piloto opt-in. Excluye entrega productiva o masiva y automatización de presentación de ofertas. El monitoreo y cada canal externo deben habilitarse explícitamente por entorno.

## Incluido

- Conector SECOP publico e inventario documental incremental opt-in, sin login ni acciones transaccionales.
- Bandeja determinística de oportunidades contra snapshots publicados, con revisión humana e histórico.

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
- La extensión de Microfase 16 permite búsqueda e importación pública SECOP, pero no descarga
  documental, actualización incremental, login, ofertas ni trámites. No cambia el estatus de no
  producción del MVP controlado.
- OCR, firma digital y canales distintos de SMTP o webhook HMAC.
- Presentación de ofertas.
- S3 obligatorio u otro almacenamiento productivo.
- Garantias juridicas, comerciales o de cumplimiento normativo.

## Supuesto operativo

El modo esperado del MVP controlado usa datos sinteticos y `PLIEGOCHECK_AI_ENABLED=false`.
