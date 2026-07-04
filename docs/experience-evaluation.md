# Evaluacion de experiencia

El evaluador de experiencia cubre requisitos `EXPERIENCE` contra contratos y certificaciones del
snapshot publicado.

## Reglas iniciales

- Existencia de experiencia ejecutada: solo cuentan registros `COMPLETED`.
- Conteo minimo: compara el numero de experiencias completadas soportadas.
- Valor minimo: suma valores comparables en la misma moneda del requisito.
- UNSPSC: exige coincidencia exacta del codigo esperado.
- Actividad u objeto: exige coincidencia textual conservadora; no inventa equivalencias.

## Criterio conservador

Contratos en ejecucion, monedas incompatibles, porcentajes de consorcio ausentes o actividades no
comparables producen `UNKNOWN`. El sistema no asume que una experiencia parcial o declarada satisface
el requisito.
