# Runbook de incidentes de notificaciones

Ante spam, destinatario incorrecto, fuga potencial o tasa anormal: activar kill switch, pausar destino, cancelar pendientes, conservar eventos y revisar configuración sin copiar payloads ni secretos. Rotar el secreto fuera del repositorio cuando aplique. Para 429/5xx revisar backoff; para 4xx permanente corregir destino y usar retry manual controlado. Nunca borrar la alerta interna.
