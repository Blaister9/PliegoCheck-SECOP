# Checklist de despliegue

- [ ] Commit/imagen aprobados y preflight sin FAIL.
- [ ] Configuración y secretos externos; modo `restricted`.
- [ ] Migraciones aplicadas; DB/API sin publicación.
- [ ] Web únicamente por proxy HTTPS.
- [ ] Deploy idempotente y readiness estable.
- [ ] Bootstrap deshabilitado después del primer ADMIN.
- [ ] Validate/status y evidencia sanitizada archivados.
