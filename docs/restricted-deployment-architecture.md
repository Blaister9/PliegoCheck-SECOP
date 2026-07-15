# Arquitectura de despliegue restringido

Modelo: `RESTRICTED_SINGLE_HOST`.

```text
VPN/red autorizada -> Nginx HTTPS -> web
                              \-> API -> PostgreSQL
                                     -> storage persistente
                         worker ------^
              scheduler opt-in ------^
```

`frontend` conecta proxy, web y API. `backend`, marcada interna, conecta API, worker, scheduler y PostgreSQL. Solo el proxy publica puertos y por defecto enlaza `127.0.0.1`; exponer otra interfaz requiere firewall/VPN/allowlist externos ya verificados. No hay Kubernetes, Redis, Celery, RabbitMQ o Kafka.

Paquete de despliegue institucional: preparado y validado localmente.

Despliegue en servidor institucional real: no ejecutado.

La evidencia local usa certificados, secretos y datos sintéticos temporales; no acredita servidor, red, dominio, certificado ni autorización institucional.
