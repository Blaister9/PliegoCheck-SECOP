# Respuesta a incidentes del modo restringido

1. Detectar y clasificar: secreto/dato expuesto, auth, certificado, disponibilidad, corrupción, SSRF o entrega externa.
2. Contener: deshabilitar entrega/scheduler/SECOP según el caso, restringir red, revocar sesiones y detener servicios sin borrar volúmenes.
3. Preservar evidencia sanitizada: request/event IDs, timestamps, hashes y estados; nunca copiar secretos o payloads completos.
4. Erradicar/recuperar: rotar fuera de Git, parchear, validar backup, restore aislado, deploy/rollback y `restricted:validate`.
5. Comunicar al responsable institucional y documentar impacto, causa, decisión y verificación.

Secreto expuesto, pérdida de datos o corrupción irrecuperable detienen la operación. Para spam/destino incorrecto activar kill switch y seguir el runbook de notificaciones. Cerrar solo tras validar integridad, permisos, TLS, colas y retención.
