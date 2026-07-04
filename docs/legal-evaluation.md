# Evaluacion juridica

El evaluador juridico cubre requisitos `LEGAL`, `DOCUMENTARY`, `GUARANTEE` y
`RISK_AND_INELIGIBILITY`.

## Reglas iniciales

- RUP o registro vigente: busca registros soportados y vigencia no expirada a la fecha efectiva.
- RUT, camara de comercio o representacion legal: exige dato existente con soporte verificable o
  soportado.
- Garantias y documentos habilitantes: exige documento o evidencia asociada al requisito.
- Inhabilidades o declaraciones de riesgo: si no existe soporte explicito, el resultado queda
  `UNKNOWN`.

## Criterio conservador

Un registro vencido produce `DOES_NOT_COMPLY`. Un registro declarado sin soporte, un documento
faltante o una declaracion no encontrada produce `UNKNOWN`, no cumplimiento.
