# Criterios de no produccion

El MVP controlado no debe usarse en produccion mientras exista cualquiera de
estas condiciones:

- no hay validacion real con usuarios piloto;
- aparecen datos reales sin autorizacion y sin controles de tratamiento;
- falta SSO, MFA o gobierno productivo de identidades;
- falta almacenamiento productivo y politica de retencion;
- no existe aprobacion juridica y de seguridad;
- los backups no se verifican en entorno objetivo;
- la validacion manual de navegador no esta completa;
- los runbooks no han sido ejecutados por responsables reales;
- hay hallazgos `BLOCKER` o `HIGH` abiertos sin aceptacion formal;
- el data scan detecta secretos o datos reales no permitidos.

Si una condicion se cumple, la decision de despliegue productivo es `NO GO`.
