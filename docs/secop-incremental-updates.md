# Actualizaciones incrementales SECOP

Cada ejecucion crea un snapshot inmutable del proceso y compara estado externo, publicacion, cierre, cuantia, moneda, entidad, titulo, descripcion, inventario, fecha de actualizacion y hash del payload reducido. Un valor que desaparece genera `SOURCE_FIELD_NOW_MISSING`: el snapshot nuevo conserva `null` y el proceso corriente no reemplaza un dato conocido por uno inventado.

Los cambios de estado, cierre y cuantia generan eventos tipados. Los documentos nuevos, actualizados o ausentes de la fuente generan eventos sin borrar historico. Un hash documental igual queda `UNCHANGED`; uno nuevo crea una version enlazada a la anterior. Ningun sync modifica reportes historicos ni encola evaluacion o decision.
