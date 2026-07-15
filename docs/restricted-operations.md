# Operación restringida

Comandos: `restricted:preflight|deploy|validate|status|backup|backup:verify|restore:verify|retention:dry-run|retention:run|rollback|stop`. Deploy conserva datos; validate no crea usuarios ni procesos; stop conserva volumen DB, storage, configuración y backups.

Worker coordina extracción, discovery, assessment, sync/descarga explícita, monitores, notificaciones y digests. Cada capacidad respeta sus flags. Scheduler es un proceso separado, deshabilitado por defecto y protegido por el lock transaccional existente. Health checks prueban proxy, web, API, DB y heartbeat.

Logs JSON de contenedor rotan por tamaño/cantidad. No registrar cuerpos, cookies, firmas, contraseñas, claves ni payloads completos. `status` presenta versión, commit, servicios, health, flags, último backup, disco y certificado sanitizados. La inspección de colas y auditoría se realiza con roles autorizados.
