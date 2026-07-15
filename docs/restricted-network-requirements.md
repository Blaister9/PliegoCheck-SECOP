# Requisitos de red restringida

Entrada permitida: HTTPS desde VPN/red/allowlist autorizada y administración SSH conforme a política externa. HTTP solo puede redirigir a HTTPS. No permitir acceso directo a API, web, workers, scheduler o PostgreSQL.

Salida permitida por necesidad: DNS, Datos Abiertos/SECOP; registro de imágenes durante despliegue; SMTP o webhook únicamente si están aprobados, allowlisted y habilitados. Limitar egreso mitiga el riesgo TOCTOU residual de SSRF además de las validaciones DNS/IP de la aplicación.

El paquete no modifica el firewall. El operador debe verificar segmentación, egress, VPN/allowlist, resolución DNS y registros antes del gate institucional.
