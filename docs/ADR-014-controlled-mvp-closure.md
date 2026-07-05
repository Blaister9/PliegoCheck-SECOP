# ADR-014 - Cierre de MVP controlado

## Estado

Aceptada.

## Contexto

La Microfase 13 dejo el repositorio listo para una validacion controlada con
usuarios piloto, datos sinteticos, roles locales, runbooks operativos,
checklists, rollback, data scan y CI. La Microfase 14 cierra ese MVP controlado
sin ampliar el alcance funcional ni declarar aptitud productiva.

No se recibió retroalimentación real de usuarios piloto en esta microfase.

## Decision

Se declara cerrado el MVP controlado como release candidate documental y
operativo, condicionado a:

- mantener datos sinteticos como unico insumo permitido;
- conservar `PLIEGOCHECK_AI_ENABLED=false` como modo esperado del piloto;
- exigir trazabilidad requisito -> evidencia -> decision;
- bloquear cualquier uso productivo hasta completar los criterios de no
  produccion;
- registrar limitaciones y riesgos sin convertir supuestos en hechos.

## Consecuencias

- El cierre no habilita despliegue productivo.
- La decision GO / NO GO sigue siendo deterministica y auditable.
- La siguiente microfase debe decidir si se evoluciona a piloto real o si se
  pausa tecnicamente el producto.
- Los hallazgos sin evidencia real de usuarios quedan diferidos, no resueltos
  por inferencia.

## Alternativas descartadas

- Declarar listo para produccion: descartado por ausencia de validacion real,
  SSO/MFA, almacenamiento productivo y datos reales autorizados.
- Simular feedback de usuarios: descartado por integridad de informacion.
- Ampliar funcionalidades durante el cierre: descartado para mantener un MVP
  controlado revisable.
