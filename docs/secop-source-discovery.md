# Descubrimiento de fuentes SECOP

Verificación realizada el **13 de julio de 2026** contra el catálogo público oficial de Datos
Abiertos Colombia y los recursos publicados por Colombia Compra Eficiente (CCE). La integración no
depende de endpoints recordados ni de scraping HTML.

## Fuentes seleccionadas

| Prioridad | Fuente | Dataset | URL humana | API pública | Campos útiles verificados | Autenticación |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | SECOP II - Procesos de Contratación | `p6dx-8zbt` | `https://www.datos.gov.co/Estad-sticas-Nacionales/SECOP-II-Procesos-de-Contrataci-n/p6dx-8zbt` | `https://www.datos.gov.co/resource/p6dx-8zbt.json` | id, referencia, nombre/descripción, entidad/NIT, modalidad, estado, precio base, publicación, recepción, departamento, ciudad y URL del proceso | Pública; `X-App-Token` opcional |
| 2 | SECOP I - Procesos de Compra Pública | `f789-7hwg` | `https://www.datos.gov.co/Estad-sticas-Nacionales/SECOP-I-Procesos-de-Compra-P-blica/f789-7hwg` | `https://www.datos.gov.co/resource/f789-7hwg.json` | número de proceso, objeto, entidad/NIT, modalidad, estado, cuantía, moneda, fecha de cargue, departamento, municipio y ruta SECOP I | Pública; `X-App-Token` opcional |

El catálogo reportó 59 columnas para SECOP II y 79 para SECOP I, propietario `Datos Abiertos CCE`
y actualización diaria. La API Socrata respondió sin autenticación a una consulta limitada a un
registro. Un `X-App-Token` es opcional y puede mejorar cuotas, pero no se almacena en el repositorio.

Referencias oficiales consultadas:

- Catálogo de datos de CCE: `https://operaciones.colombiacompra.gov.co/datos-abiertos`
- Manual de Datos Abiertos de CCE:
  `https://www.colombiacompra.gov.co/sites/cce_public/files/cce_documentos/cce_manual_datos_abiertos.pdf`
- Metadatos de cada dataset: `https://www.datos.gov.co/api/views/{dataset_id}`

## Límites, paginación y filtros

La API usa `$limit` y `$offset`; PliegoCheck impone un máximo configurable y nunca consulta sin
límite. Se envía `$select` con una lista cerrada de campos necesarios, `$order` por publicación,
`$q` para búsqueda general y `$where` construido únicamente a partir de nombres de columna
verificados. Los valores de texto se escapan antes de formar SoQL.

Ambas fuentes permiten filtros por entidad, modalidad, estado, ubicación, cuantía, publicación y
código. SECOP II también expone fecha de cierre. El dataset seleccionado de SECOP I no la expone;
`closing_from` y `closing_to` se reportan como `UNSUPPORTED_FILTER` y no se simulan.

SECOP II tampoco publica una columna de moneda para `precio_base`. Por integridad, el conector deja
`currency=null`, agrega `UNKNOWN_CURRENCY` y conserva el valor numérico; no infiere `COP`. SECOP I
sí publica `moneda` y solo se normaliza cuando el texto corresponde a un código reconocido.

En SECOP I, `uid` identifica una relación entre proceso y adjudicación y puede repetir el mismo
proceso. Por eso la identidad y deduplicación de importación usan `numero_de_proceso`; filas
repetidas para ese número dentro de una consulta se omiten con un warning explícito.

Socrata aplica cuotas que pueden variar según tráfico y uso de token. Por eso el cliente incorpora
timeout, tres intentos máximos, límite local por minuto y caché TTL. No se afirma una cuota pública
fija que la fuente no garantice.

## Decisión y riesgos

Se implementan primero los datasets de procesos de SECOP II y SECOP I mediante su API JSON. Los
datasets de contratos no sustituyen un proceso y quedan fuera de esta microfase. Los documentos no
aparecen como enlaces descargables estables en las filas seleccionadas: se conserva la URL oficial
del proceso y se marca `DOCUMENT_DOWNLOAD_UNSUPPORTED`.

Los datos públicos pueden ser incompletos, retrasados, cambiar de esquema o contener datos
personales en columnas no necesarias. El mapper usa una lista permitida, omite contratistas y
personas, conserva un payload crudo reducido para auditoría y calcula su SHA-256. Un fallo externo
queda persistido y sanitizado; no tumba la API ni se convierte en un hecho sobre el proceso.
Los enlaces de proceso se conservan solo si usan HTTPS y pertenecen a hosts oficiales conocidos de
SECOP; una moneda desconocida permanece en `null` y puede impedir la importación de una cuantía
hasta revisión humana.
