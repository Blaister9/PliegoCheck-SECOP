# Guia de demo final del MVP controlado

## Objetivo

Mostrar el alcance real del MVP controlado sin prometer produccion ni validar
usuarios reales que no participaron.

## Preparacion

1. Ejecutar `pnpm infra:up`.
2. Ejecutar `pnpm db:migrate`.
3. Ejecutar `pnpm pilot:prepare`.
4. Ejecutar `pnpm controlled:validate`.
5. Ejecutar `pnpm mvp:data-scan`.

## Recorrido sugerido

1. Entrar como `ADMIN` y revisar auditoria, usuarios y estado operativo.
2. Entrar como `ANALYST` y revisar proceso, evidencias y evaluaciones.
3. Entrar como `REVIEWER` y revisar decision deterministica y trazabilidad.
4. Entrar como `VIEWER` y confirmar acceso de solo lectura.
5. Descargar reporte/ZIP y verificar que no expone secretos ni rutas fisicas.
6. Abrir `docs/mvp-final-findings.md` y explicar hallazgos cerrados,
   diferidos y criterios de no produccion.

## Mensaje obligatorio

No se recibió retroalimentación real de usuarios piloto en esta microfase.

## Cierre

La demo concluye con una decision ejecutiva pendiente: evolucionar a piloto
real con controles adicionales o pausar tecnicamente el producto.
