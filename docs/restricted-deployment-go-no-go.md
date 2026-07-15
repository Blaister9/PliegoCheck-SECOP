# Gate del despliegue restringido

- `DEPLOYMENT_BLOCKED`: secretos versionados, HTTP efectivo, PostgreSQL/API públicos, bypass auth, certificado inseguro, pérdida de datos o rollback inexistente.
- `REMEDIATION_REQUIRED`: preflight, headers, migraciones, readiness, scripts o restore verification fallan.
- `PACKAGE_READY_WITH_CONDITIONS`: paquete completo, simulación local aprobada, sin blocker; SSO/MFA, infraestructura y validación humana pendientes.
- `PACKAGE_READY`: además exige infraestructura/red/certificados reales, usuarios autorizados, validación humana y ningún HIGH abierto.

## Resultado vigente

`PACKAGE_READY_WITH_CONDITIONS`.

El paquete y la simulación equivalente son evidencia técnica local. Servidor institucional, dominio, certificado, firewall/VPN, SSO, MFA y usuarios reales no fueron proporcionados ni verificados. `PACKAGE_READY` no se selecciona sin esa evidencia. Este gate no autoriza producción pública.
