# Seguridad de descargas documentales SECOP

La descarga esta deshabilitada por defecto y exige confirmacion, permiso y host exacto en allowlist. Antes de cada GET y redireccion se valida HTTPS/443 y se resuelve DNS; se bloquean localhost, redes privadas, link-local, multicast, reservadas, no especificadas y endpoints de metadata. No se envian cookies ni headers sensibles.

Los content types y extensiones forman una allowlist cerrada: PDF, DOCX, XLSX, TXT y CSV. Archivos comprimidos arbitrarios (`.rar`, `.zip`, `.7z`) y ejecutables permanecen `UNSUPPORTED`, aunque la fuente publique un enlace.

`CORSMiddleware` envuelve la autenticacion para que 401/403 mantengan el envelope sanitizado y el `request_id` cuando el origen esta permitido. Se usan origenes explicitos con credenciales; un origen no permitido no recibe `Access-Control-Allow-Origin` y nunca se habilita `*` con cookies.

La respuesta se procesa en streaming con timeout, limite de redirecciones, `Content-Length` preventivo y corte por bytes reales. Solo se aceptan PDF, DOCX, XLSX, TXT y CSV; se valida MIME, extension, firma/contenedor, macros y HTML inesperado. SHA-256 se calcula durante el streaming. El temporal solo se mueve tras validar, y se elimina el objeto final si falla la transaccion de base de datos.

Estos controles deben complementarse con una politica de salida de red del despliegue. Detalles operativos: [secop-document-sync.md](secop-document-sync.md).
