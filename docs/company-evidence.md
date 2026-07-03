# Evidencias de empresa

Las evidencias de empresa son documentos originales que soportan datos del perfil. Reutilizan la
validacion, almacenamiento, cola y extraccion documental de procesos.

## Carga

`POST /companies/{company_id}/evidence-documents` acepta carga multiple. Cada archivo se valida por:

- nombre seguro;
- extension y `Content-Type`;
- tamano maximo;
- archivo no vacio;
- firma/mime detectado cuando aplica;
- SHA-256 duplicado por empresa.

La API devuelve metadatos y nunca expone rutas fisicas ni claves internas de almacenamiento.

## Extraccion

Cada soporte crea un `ProcessDocument` tecnico asociado a un proceso oculto del perfil. El worker
procesa el documento con los mismos extractores deterministas de Microfase 3 y publica extracciones y
segmentos consultables internamente.

## Vinculacion dato-evidencia

`POST /companies/{company_id}/evidence-links` vincula un dato con:

- tipo de sujeto (`COMPANY_PROFILE`, `LEGAL_REGISTRATION`, `RUP_SNAPSHOT`, `UNSPSC_CODE`,
  `FINANCIAL_PERIOD`, `FINANCIAL_METRIC`, `EXPERIENCE_RECORD`, `PERSON`, `PERSON_EDUCATION`,
  `PERSON_EXPERIENCE`, `PERSON_CREDENTIAL`, `COMPANY_CERTIFICATION`, `COMPANY_CAPABILITY`);
- documento de evidencia;
- extraccion y segmento opcionales;
- cita textual y ubicacion opcionales;
- rol de evidencia.

El validador rechaza segmentos ajenos al documento, citas inexistentes, ubicaciones incompatibles y
evidencias vencidas. Los enlaces sin segmento son posibles solo como soporte documental de nivel
documento y quedan sujetos a revision.

## Privacidad

Los documentos empresariales pueden incluir datos financieros y personales. La UI y la API exponen
solo metadatos necesarios, enmascaran identificadores y mantienen auditoria de cambios relevantes.
