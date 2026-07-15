# Reintentos de notificaciones

Timeout, conexión, 408, 425, 429 y 5xx son temporales. Otros 4xx son permanentes. El backoff es exponencial, acotado y con jitter determinístico; un `Retry-After` entero válido tiene prioridad. Al agotar intentos el mensaje queda `FAILED_PERMANENT`. Retry manual conserva intentos y la identidad original; cancelación es explícita y auditada.
