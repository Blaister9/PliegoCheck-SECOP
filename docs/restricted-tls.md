# TLS restringido

Nginx termina TLS 1.2/1.3 con certificado/cadena y clave proporcionados externamente. Los archivos se montan read-only. Preflight comprueba formato, fechas, hostname, días restantes y que la clave corresponde, sin mostrarla. HSTS, CSP, `nosniff`, frame denial, referrer y permissions policy se agregan en el proxy.

El certificado sintético local solo sirve para simulación y debe eliminarse. No constituye certificado institucional. Renovación: instalar archivos nuevos fuera de Git, ejecutar preflight, reiniciar proxy, validate y registrar fecha/issuer/expiry sin clave. Certificado vencido, discordante o sin hostname bloquea despliegue.
