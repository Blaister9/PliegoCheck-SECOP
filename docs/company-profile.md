# Perfil de empresa

Microfase 5 agrega perfiles de empresa para capturar capacidad real con soporte documental. El
perfil es editable; las evaluaciones futuras deben usar un snapshot publicado.

## Datos cubiertos

- Identidad: razon social, nombre comercial, NIT/identificador, tipo de empresa, naturaleza
  juridica, ubicacion y contacto.
- Juridico: registros como RUT, camara de comercio, representacion legal y RUP.
- RUP y UNSPSC: snapshots de RUP, vigencias, capacidades declaradas y codigos UNSPSC activos.
- Finanzas: periodos, fuentes, metricas declaradas o calculadas, moneda y formula cuando aplique.
- Experiencia: contratos, valores, participacion de consorcio/UT, codigos UNSPSC y actividades.
- Personal: personas, relacion con la empresa, disponibilidad, educacion, experiencia y credenciales.
- Certificaciones y capacidades: certificaciones empresariales y capacidades operativas, tecnicas o
  territoriales.

## Reglas

- La fecha de constitucion no puede estar en el futuro.
- Los identificadores se normalizan para unicidad y se muestran enmascarados.
- Los estados de datos usan `DECLARED`, `SUPPORTED`, `VERIFIED`, `REJECTED`, `EXPIRED` o
  `NEEDS_REVIEW`.
- Completitud no es cumplimiento. Un perfil completo solo significa que tiene datos y soportes
  suficientes para revision inicial.

## API principal

- `POST /companies`, `GET /companies`, `GET /companies/{company_id}`, `PATCH /companies/{company_id}`.
- Subrecursos bajo `/companies/{company_id}` para registros juridicos, RUP, UNSPSC, finanzas,
  experiencia, personal, certificaciones y capacidades.
- `GET /companies/{company_id}/completeness` para el calculo deterministico de faltantes.

## UI

La web expone `/companies`, `/companies/new` y `/companies/{id}` con secciones por dominio. Las
advertencias visibles indican que la completitud no evalua cumplimiento y que las evaluaciones
futuras usaran una version especifica del perfil.
