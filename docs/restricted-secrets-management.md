# Secretos del despliegue restringido

Session secret, password y URL de DB, password de bootstrap, tokens, SMTP, HMAC y clave TLS se suministran como archivos externos con mínimo privilegio. Compose monta referencias de solo lectura; el entrypoint carga únicamente los valores requeridos y no los imprime. Los archivos no se copian a imágenes ni backups.

El operador crea, rota, revoca y audita secretos con el mecanismo institucional disponible. Tras bootstrap debe deshabilitar el flag y rotar la contraseña. Ante exposición: detener entrega, revocar sesiones/credenciales, rotar fuera de Git, revisar auditoría y tratar cualquier copia como incidente. Readiness/status muestran estados, nunca valores ni URLs completas sensibles.
