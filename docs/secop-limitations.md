# Limitaciones del conector SECOP

- La fuente es externa: puede estar incompleta, desactualizada, temporalmente caída o cambiar de
  esquema sin aviso. Los estados y warnings informan la incertidumbre; no la ocultan.
- La búsqueda opera sobre dos datasets de procesos verificados el 2026-07-13. No agrega contratos,
  proveedores, ofertas, adendas ni notificaciones.
- SECOP I no soporta filtro de cierre con el dataset seleccionado.
- SECOP II no publica la moneda de `precio_base`; se conserva como desconocida y debe verificarse
  antes de usar la cuantía en una evaluación financiera.
- La búsqueda de texto de Socrata y la normalización de estados/modalidades no equivalen a una
  clasificación jurídica. Los valores externos se conservan como datos de fuente.
- El payload crudo es una selección permitida, no una copia íntegra del registro original. El hash
  permite verificar esa selección, no reconstruir campos omitidos.
- Los documentos no se descargan. El enlace oficial puede requerir navegación manual y su
  disponibilidad no está garantizada.
- Rate limit y caché son locales a cada proceso de API; no coordinan múltiples réplicas.
- No hay actualización incremental ni reconciliación automática de procesos ya importados.
- No se automatizan login, captchas, firma, radicación, presentación de ofertas ni trámites SECOP.
- Esta capacidad no habilita producción ni elimina los criterios de no producción existentes.

Antes de usar un proceso importado en una decisión, una persona debe verificar vigencia, documentos,
adendas y evidencia crítica. Falta de evidencia debe mantenerse como `PENDIENTE_INFORMACION`.
