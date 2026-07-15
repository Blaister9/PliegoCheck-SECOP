# Webhooks firmados

Solo se permite HTTPS y hosts exactos autorizados; HTTP local requiere flag de desarrollo. Se bloquean credenciales URL, loopback, privadas, link-local y resoluciones no globales. No se siguen redirects.

Firma `v1=<hex_hmac_sha256>` sobre `timestamp + "." + raw_body`. Headers: `X-PliegoCheck-Delivery-Id`, `X-PliegoCheck-Timestamp`, `X-PliegoCheck-Signature`, `X-PliegoCheck-Event` y `X-PliegoCheck-Idempotency-Key`. El secreto procede de la variable nombrada por `secret_reference`, nunca de PostgreSQL.
