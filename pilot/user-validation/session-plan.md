# Plan de sesion de validacion piloto

## Objetivo

Validar que usuarios piloto puedan recorrer PliegoCheck con datos sinteticos, por rol, y registrar
retroalimentacion estructurada para decidir ajustes de Microfase 14.

## Duracion sugerida

90 a 120 minutos.

## Roles

- ADMIN: operacion, usuarios, auditoria y configuracion.
- ANALYST: flujo proceso, empresa, evaluaciones, decision y reporte.
- REVIEWER: revision de resultados y override sintetico.
- VIEWER: navegacion solo lectura y permisos denegados controlados.

## Prerrequisitos

- `pnpm controlled:deploy` completado.
- `pnpm controlled:validate` completado.
- `pnpm controlled:data-scan` completado.
- Usuarios sinteticos disponibles.
- Backup previo ejecutado.
- Facilitador y observador asignados.

## Agenda

1. Presentar alcance: piloto sintetico, no produccion.
2. Confirmar entorno, commit y release candidate.
3. Ejecutar tareas ADMIN.
4. Ejecutar tareas ANALYST.
5. Ejecutar tareas REVIEWER.
6. Ejecutar tareas VIEWER.
7. Descargar ZIP y revisar evidencia.
8. Completar feedback y matriz de hallazgos.
9. Revisar bloqueos y decision de siguiente fase.

## Criterios de exito

- Cada rol completa sus tareas principales.
- No hay errores 500 no explicados.
- Viewer recibe 403 al intentar modificar.
- Reporte y ZIP descargan.
- Auditoria registra acciones relevantes.
- Todos los hallazgos quedan clasificados.

## Criterios de interrupcion

- Aparece dato real.
- Se revela secreto, cookie o token.
- Falla login para mas de un rol.
- No descarga el ZIP.
- Health/readiness queda en error.
- Error 500 bloquea el flujo principal.

## Registro de hallazgos

Usar `feedback-form.md` para entrevistas y `findings-matrix.csv` para consolidar decisiones.
