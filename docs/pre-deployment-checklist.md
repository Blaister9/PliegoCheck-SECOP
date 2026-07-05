# Checklist pre-despliegue controlado

- [ ] `git status --short` limpio.
- [ ] CI verde en el PR/release candidate.
- [ ] Migraciones verificadas con `pnpm db:migrate` y `pnpm db:check`.
- [ ] `.env` completo y basado en `.env.pilot.example`.
- [ ] `PLIEGOCHECK_AUTH_SECRET_KEY` presente fuera del repositorio.
- [ ] CORS no usa wildcard.
- [ ] Cookie `Secure=true` si hay HTTPS.
- [ ] Storage local escribible.
- [ ] Backup previo ejecutado y manifest revisado.
- [ ] Admin inicial creado con password no versionado.
- [ ] OpenAI configurado solo si se usara; por defecto deshabilitado.
- [ ] Fake provider deshabilitado fuera de test/piloto controlado.
- [ ] `pnpm pilot:eval` pasando.
- [ ] `pnpm deployment:eval` pasando.
- [ ] `pnpm deployment:backup-check` pasando.
- [ ] Documentacion operativa revisada.
