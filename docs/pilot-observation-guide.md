# Guia de observacion de sesion piloto

Usar solo con datos sinteticos. No capturar documentos reales, credenciales, cookies, tokens ni
pantallas con informacion personal real.

## Logs a mirar

- API: `var/controlled/logs/api.log` y `var/controlled/logs/api.err.log`.
- Web: `var/controlled/logs/web.log` y `var/controlled/logs/web.err.log`.
- Worker: salida de `pnpm worker:health` y comandos `pilot:*`.
- CI/evals: salida de `pnpm controlled:eval`, `pnpm controlled:data-scan`, `pnpm mvp:eval`,
  `pnpm mvp:data-scan` y `pnpm pilot:eval`.

## Request ID

La API retorna `X-Request-ID`. Copiar ese valor cuando haya 4xx/5xx o un error visible en navegador.
Relacionarlo con el rol, tarea y hora aproximada.

## Auditoria

ADMIN debe revisar `/admin/audit` o el endpoint `/admin/audit-events` para confirmar login, logout,
permisos denegados, revisiones y descargas. No copiar tokens ni cookies.

## Registro de bug

Cada bug debe incluir escenario, rol, tarea, resultado esperado, resultado observado, severidad,
evidencia, decision de producto, fase destino y estado. Usar `pilot/user-validation/feedback-form.md`
y `pilot/user-validation/findings-matrix.csv`.

## Capturas permitidas

- Pantallas con datos sinteticos del piloto.
- Mensajes de error sin secretos.
- ZIP manifest y nombres de artefactos.
- Audit events sanitizados.

## Capturas prohibidas

- Passwords, cookies, headers `Authorization`, tokens de sesion o `.env`.
- Datos reales de personas, empresas, entidades, procesos o documentos.
- Rutas absolutas locales si identifican una maquina personal.

## Reporte ZIP y evidencia

Descargar el ZIP desde el panel de reporte. Conservar solo el paquete sintetico y su `manifest.json`
como evidencia de la sesion. Registrar hash o nombre del artefacto, no rutas fisicas locales.
