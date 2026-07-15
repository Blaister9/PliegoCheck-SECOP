# Alta y baja de usuarios restringidos

Bootstrap crea solo el primer ADMIN, por password-file y una única vez. Deshabilitarlo y rotar inmediatamente. Después, un ADMIN autorizado crea exactamente las cuentas aprobadas: un ANALYST, REVIEWER y VIEWER iniciales, con identidad nominativa, mínimo privilegio y contraseña temporal transmitida por canal externo seguro. No versionar emails ni credenciales.

Validar matriz de permisos en backend, cambio de contraseña, lockout y auditoría. En salida o cambio de rol: deshabilitar usuario, revocar sesiones, retirar destinos/suscripciones, revisar tokens asociados y registrar aprobación. La autenticación local es una condición temporal del despliegue restringido. No sustituye SSO institucional ni MFA.
