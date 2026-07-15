# Correo SMTP

El proveedor genera texto y HTML escapado, sin adjuntos, scripts, formularios, píxeles ni HTML SECOP. Rechaza CR/LF, direcciones inválidas y dominios fuera de allowlist. TLS o STARTTLS es obligatorio salvo Mailpit local con `PLIEGOCHECK_SMTP_ALLOW_LOCAL_INSECURE=true` en desarrollo. Un 4xx SMTP se trata como temporal; 5xx como permanente. Aceptación SMTP no significa lectura.
