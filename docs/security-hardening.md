# Security hardening

Controles implementados en Microfase 10:

- Cookie HttpOnly para sesion.
- Hash de token de sesion en DB.
- Hash PBKDF2 para passwords.
- Lockout configurable por intentos fallidos.
- Middleware global de autenticacion.
- Headers `nosniff`, `DENY`, `no-referrer`, CSP y Permissions-Policy.
- CORS con origenes explicitos.
- Request ID en respuestas.
- Errores internos sanitizados.
- Auditoria operacional sin secretos.
- Config de piloto con fail-fast para auth insegura.

Fuera de alcance: SSO, MFA, SAML, Azure AD, S3 obligatorio y despliegue real.
