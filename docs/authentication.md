# Autenticacion

La autenticacion local usa email y password. Las contrasenas se almacenan como hash PBKDF2-SHA256
con salt y las sesiones se guardan en PostgreSQL con hash del token.

## Variables

```text
PLIEGOCHECK_AUTH_ENABLED=true
PLIEGOCHECK_AUTH_COOKIE_NAME=pliegocheck_session
PLIEGOCHECK_AUTH_COOKIE_SECURE=false
PLIEGOCHECK_AUTH_COOKIE_SAMESITE=lax
PLIEGOCHECK_AUTH_SESSION_TTL_MINUTES=480
PLIEGOCHECK_AUTH_SECRET_KEY=
PLIEGOCHECK_AUTH_PASSWORD_MIN_LENGTH=12
PLIEGOCHECK_AUTH_MAX_FAILED_ATTEMPTS=10
PLIEGOCHECK_AUTH_LOCKOUT_MINUTES=15
```

En piloto, `PLIEGOCHECK_AUTH_SECRET_KEY` debe existir y `PLIEGOCHECK_AUTH_COOKIE_SECURE=true` si
hay HTTPS.
`.env.pilot.example` documenta el perfil controlado; copiarlo a `.env` local no versionado y
reemplazar todos los `CHANGEME`.
Los scripts `controlled:*` leen `.env.pilot` por defecto y rechazan placeholders `CHANGEME` antes de
levantar una sesion piloto compartida.

## Primer admin

```powershell
Get-Content .\admin-password.txt | pnpm auth:create-admin -- --email admin@example.com --display-name "Admin" --password-stdin
```

No uses passwords en argumentos visibles. El comando imprime metadata del usuario, no el password.

## Endpoints

- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`
- `POST /auth/change-password`

Los tokens no se guardan en `localStorage`; el navegador usa cookie HttpOnly.

## Limites

La autenticacion local es suficiente para demo/piloto controlado. No implementa SSO, MFA ni politicas
corporativas de identidad.
