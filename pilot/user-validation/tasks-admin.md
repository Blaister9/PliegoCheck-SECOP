# Tareas ADMIN

Datos: usar `admin@pilot.pliegocheck.local` o el admin sintetico creado para la sesion.

| paso | tarea                                       | resultado esperado                                             |
| ---- | ------------------------------------------- | -------------------------------------------------------------- |
| 1    | Login                                       | Acceso exitoso y rol ADMIN visible.                            |
| 2    | Revisar usuarios                            | Usuarios sinteticos admin, analyst, reviewer y viewer existen. |
| 3    | Revisar auditoria                           | Eventos de login y acciones previas aparecen sanitizados.      |
| 4    | Revisar system config                       | Configuracion no revela secretos ni rutas fisicas sensibles.   |
| 5    | Crear o deshabilitar usuario demo si aplica | Accion permitida solo para ADMIN y auditada.                   |
| 6    | Intentar navegar a proceso piloto           | Lectura permitida.                                             |
| 7    | Logout                                      | Sesion invalidada; `/auth/me` deja de responder con usuario.   |

Registrar cualquier error, texto confuso o dato sensible expuesto.
