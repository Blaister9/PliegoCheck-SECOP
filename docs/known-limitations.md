# Limitaciones conocidas

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
- Las reglas particulares de cada pliego no deben hardcodearse como reglas
  universales.
