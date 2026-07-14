# Conector SECOP / Datos Abiertos

El conector busca procesos públicos de SECOP II y SECOP I, normaliza una selección mínima de campos
y permite importarlos al inventario interno. No inicia análisis, no decide participación, no inicia
sesión en SECOP y no presenta ofertas ni trámites.

## Configuración

```dotenv
PLIEGOCHECK_SECOP_ENABLED=false
PLIEGOCHECK_SECOP_PROVIDER=datos_abiertos
PLIEGOCHECK_SECOP_BASE_URL=https://www.datos.gov.co
PLIEGOCHECK_SECOP_APP_TOKEN=
PLIEGOCHECK_SECOP_TIMEOUT_SECONDS=30
PLIEGOCHECK_SECOP_MAX_PAGE_SIZE=100
PLIEGOCHECK_SECOP_RATE_LIMIT_PER_MINUTE=60
PLIEGOCHECK_SECOP_CACHE_TTL_MINUTES=60
PLIEGOCHECK_SECOP_ALLOW_LIVE_TESTS=false
```

`PLIEGOCHECK_SECOP_ENABLED` habilita consultas desde la aplicación. El token es opcional y secreto.
La URL debe ser el origen HTTPS oficial de `datos.gov.co`; el proveedor soportado en esta versión es `datos_abiertos`. CI fuerza el
conector live a `false` y trabaja solo con fixtures.

## Operación

- `pnpm secop:test`: pruebas de cliente, mapper, persistencia, API, web y contratos.
- `pnpm secop:eval`: casos deterministas y offline del conector.
- `pnpm secop:smoke`: consulta live de un registro; se niega salvo que
  `PLIEGOCHECK_SECOP_ALLOW_LIVE_TESTS=true` y el conector esté habilitado.

El smoke informa fuente, latencia, campos presentes, resultado normalizado y warnings. Nunca
importa. No se debe versionar su salida ni habilitarlo en CI.

Cada búsqueda conserva por separado las filas recibidas de la fuente y los resultados válidos
normalizados. La paginación usa el primer conteo, por lo que una fila omitida o duplicada no corta
prematuramente el acceso a la página siguiente.

## Comportamiento y errores

Cada fuente tiene `AVAILABLE`, `PARTIAL`, `STALE`, `ERROR` o `UNSUPPORTED`; cada campo normalizado
registra `PRESENT`, `MISSING`, `NORMALIZED`, `UNMAPPED` o `CONFLICTING`. Los errores externos se
traducen a códigos tipados como `SOURCE_TIMEOUT`, `SOURCE_UNAVAILABLE`, `SOURCE_INVALID_RESPONSE`,
`RATE_LIMITED` y `UNSUPPORTED_FILTER`, sin filtrar cuerpos o credenciales.

La normalización no completa valores por contexto: una moneda que el dataset no publica queda en
`null` y produce `UNKNOWN_CURRENCY`. El valor externo puede conservarse, pero su moneda requiere
verificación humana antes de una evaluación financiera.

La caché es local al proceso y el rate limit no es un mecanismo distribuido. Reiniciar una réplica
vacía ambos. Para operación de varias réplicas se requeriría un coordinador compartido.

## Términos y uso prudente

El operador debe respetar los términos de Datos Abiertos Colombia y CCE, mantener consultas
limitadas e identificables y evitar extracción masiva. El conector no concede autorización para
usar datos personales, automatizar el portal transaccional, evadir controles ni sustituir la fuente
oficial. Consulte [descubrimiento de fuentes](secop-source-discovery.md) y
[limitaciones](secop-limitations.md).
