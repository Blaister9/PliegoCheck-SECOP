# Descubrimiento de fuentes documentales SECOP

Verificación controlada realizada el **13 de julio de 2026** contra el catálogo oficial de Datos
Abiertos Colombia, las APIs Socrata publicadas por Colombia Compra Eficiente (CCE) y una muestra de
un registro por fuente. No se usaron credenciales, cookies, scraping del portal ni endpoints
inferidos.

## Resultado verificable

| Campo | SECOP I | SECOP II |
| --- | --- | --- |
| `source_system` | `SECOP_I` | `SECOP_II` |
| `dataset_id` del proceso | `f789-7hwg` | `p6dx-8zbt` |
| `process_identifier` | `numero_de_proceso`; la unión documental requiere además `numero_de_constancia` | `id_del_proceso`; la unión documental requiere además `id_del_portafolio` |
| `process_public_url` | `ruta_proceso_en_secop_i` | `urlproceso` |
| `documents_reference_available` | Sí, por `numero_de_constancia` | Sí, por `id_del_portafolio` en la columna documental `proceso` |
| `documents_api_available` | Sí: `ps88-5e3v` desde 2019 y `8kpz-m6cc` hasta 2018 | Sí: `dmgg-8hin` desde 2025; históricos `nbae-kzan` (2024), `3skv-9na7` (2023), `kgcd-kt7i` (2022) y `f8va-cf4m` (hasta 2021) |
| `direct_download_available` | La API publica `ruta_descarga`, pero la muestra fue HTTP sobre una IP; la política HTTPS la rechaza | La API publica `url_descarga_documento` HTTPS; la muestra respondió `403 text/html`, por lo que no se afirma descargabilidad estable |
| `authentication_required` | La consulta Socrata no; el comportamiento de descarga no se fuerza ni se elude | La consulta Socrata no; no se enviaron cookies y el `403` se conserva como evidencia de fallo |
| `redirect_behavior` | No se siguió porque la URL no superó la política HTTPS | La muestra no redirigió; devolvió `403` |
| `known_content_types` | Metadatos de extensión/tipo; bytes no verificados por la muestra | PDF reportado en la muestra; la respuesta real fue HTML y se rechaza |
| `known_limitations` | URLs HTTP, cobertura dividida en dos datasets y dependencia de `numero_de_constancia` | Cobertura dividida por años, descripción inconsistente del catálogo 2024 y descarga susceptible a controles del portal |
| `verification_date` | 2026-07-13 | 2026-07-13 |

## Fuentes oficiales

- Catálogo SECOP: `https://www.colombiacompra.gov.co/secop`.
- Búsqueda pública SECOP II:
  `https://www.colombiacompra.gov.co/secop/secop-ii/busqueda-publica`.
- SECOP II archivos desde 2025:
  `https://www.datos.gov.co/Estad-sticas-Nacionales/SECOP-II-Archivos-Descarga-Desde-2025/dmgg-8hin`.
- SECOP I archivos desde 2019:
  `https://www.datos.gov.co/Estad-sticas-Nacionales/SECOP-I-Archivos-Descarga/ps88-5e3v`.
- Metadatos oficiales: `https://www.datos.gov.co/api/views/{dataset_id}`.
- API pública: `https://www.datos.gov.co/resource/{dataset_id}.json`.

Los datasets documentales exponen metadatos y rutas de descarga, pero una ruta publicada no basta
para declarar un archivo descargable. PliegoCheck solo marca `DOWNLOADED` después de validar URL,
DNS, redirects, estado HTTP, tamaño, tipo declarado, firma de bytes, hash y almacenamiento final.

## Decisión de alcance

Se implementa inventario real para ambas fuentes y descarga genérica únicamente cuando la URL
descubierta supera la política cerrada y entrega bytes permitidos. Para la evidencia live observada:

- SECOP I queda `LINK_AVAILABLE` + `UNSUPPORTED` porque el enlace es HTTP.
- SECOP II queda inventariado; un `403`/HTML produce `FAILED`, nunca `DOWNLOADED`.

El smoke live es discovery-only por defecto. No se versionan payloads, HTML, documentos, cookies,
tokens ni resultados de muestras.
