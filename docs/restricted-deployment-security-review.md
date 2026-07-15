# Revisión de seguridad del despliegue restringido

| Control | Estado | Evidencia/condición |
| --- | --- | --- |
| TLS, cookies, CORS, hosts, proxy y headers | PASS | Preflight, Compose, Nginx y evals |
| API/PostgreSQL no publicados | PASS | Compose renderizado |
| Secretos fuera de Git e imágenes | PASS | referencias `*_FILE`, data scan y `.dockerignore` |
| Roles, lockout, revocación y auditoría | PASS | autenticación/autorización existentes |
| Backup, hashes y restore aislado | PASS | controlador y simulación local |
| SSRF, uploads y downloads | PASS_WITH_CONDITIONS | controles de aplicación; egress institucional pendiente |
| Logs y notificaciones | PASS_WITH_CONDITIONS | rotación/dry-run; revisión humana de plataforma pendiente |
| Dependencias Node | PASS | `pnpm audit --prod --audit-level moderate`: sin vulnerabilidades conocidas; PostCSS fijado en 8.5.10 |
| Dependencias Python | PASS | `uvx pip-audit --local --skip-editable`: sin vulnerabilidades conocidas |
| Imágenes | NOT_VERIFIED | builds válidos; Docker Scout disponible pero exige login no proporcionado |
| SSO y MFA | NOT_VERIFIED | no implementados; auth local temporal |
| Firewall/VPN, host y certificados reales | NOT_VERIFIED | infraestructura no proporcionada |

Riesgos aceptados para preparar el paquete: single-host sin HA, auth local, storage local y observabilidad básica. No se acepta HTTP, secreto versionado, bypass auth, puertos internos, restore fallido ni certificado inseguro. Resultado técnico: `PASS_WITH_CONDITIONS`.
