# Tareas VIEWER

Datos: usar `viewer@pilot.pliegocheck.local`.

| paso | tarea                         | resultado esperado                                         |
| ---- | ----------------------------- | ---------------------------------------------------------- |
| 1    | Login                         | Acceso exitoso con rol VIEWER.                             |
| 2    | Navegar procesos              | Solo lectura permitida.                                    |
| 3    | Navegar empresa piloto        | Solo lectura permitida.                                    |
| 4    | Revisar decision/reporte      | Lectura permitida.                                         |
| 5    | Intentar crear proceso        | Accion denegada con 403 comprensible.                      |
| 6    | Intentar administrar usuarios | Accion denegada.                                           |
| 7    | Descargar ZIP si aplica       | Descarga permitida si el rol conserva permiso de descarga. |
| 8    | Logout                        | Sesion cerrada.                                            |

Registrar si la UI sugiere acciones que el backend deniega.
