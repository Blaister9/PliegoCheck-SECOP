# Limitaciones conocidas

Los monitores dependen de disponibilidad y calidad de SECOP. No hay frecuencias inferiores a una hora, entrega por correo/SMS/WhatsApp/push ni webhooks externos. Las posibles adendas requieren revisión humana.

## Fuentes documentales SECOP

- La correlacion SECOP II depende de `id_del_portafolio` a `proceso`; SECOP I depende de `numero_de_constancia`. Si la fuente omite la clave, el resultado queda con advertencia y sin documentos inventados.
- En la validacion del 13 de julio de 2026, una URL de `community.secop.gov.co` respondio 403/HTML y los enlaces actuales SECOP I observados eran HTTP. Por ello el inventario funciona, pero una descarga live no se promete y SECOP I se marca `UNSUPPORTED` bajo la politica HTTPS.
- La deteccion de texto como “adenda” solo produce `POTENTIAL_ADDENDUM` y revision humana; no confirma efectos juridicos.
- La proteccion DNS se revalida antes de cada salto. El transporte HTTP conserva la resolucion del sistema, por lo que el despliegue debe aplicar tambien controles de salida de red como defensa en profundidad.
- No hay scheduler automatico: la sincronizacion se encola explicitamente y los workers deben estar operativos.

- No se recibió retroalimentación real de usuarios piloto en esta microfase.
- La evidencia disponible es sintetica y no representa contratos reales.
- El MVP no acredita cumplimiento legal ni reemplaza revision humana.
- El almacenamiento local no sustituye una arquitectura productiva con S3 o
  equivalente.
- No hay SSO, MFA ni gobierno de identidades productivo.
- La validacion manual de navegador debe ejecutarse antes de otra sesion real.
- Los flujos con IA permanecen fuera del cierre operativo controlado.
- La búsqueda e importación pública SECOP está disponible desde Microfase 16; la descarga de
  documentos, actualización incremental, OCR, firma digital y notificaciones continúa fuera de
  alcance.

Las limitaciones específicas de fuente, filtros, payload, documentos y rate limit se detallan en
[secop-limitations.md](secop-limitations.md).

## Bandeja de oportunidades

- El screening de metadatos depende de campos públicos y del snapshot; los faltantes quedan `UNKNOWN`.
- La necesidad de aliado es preliminar hasta revisar el pliego y su régimen de participación plural.
- El score ordena compatibilidad, no adjudicación ni éxito comercial.
- El análisis profundo se bloquea cuando no hay proceso, documentos o normalización; no inventa evaluaciones.
- No existen monitoreo periódico, alertas ni presentación automática de ofertas.
- Las reglas particulares de cada pliego no deben hardcodearse como reglas
  universales.
