# Modelo de dominio — PliegoCheck-SECOP

Entidades conceptuales iniciales de la plataforma. Este documento define **conceptos**, no tablas: el esquema físico (PostgreSQL + Alembic) se derivará de aquí en las microfases de implementación.

Convenciones de este documento, aplicables a toda entidad:

- **Requiere evidencia:** dato que solo puede afirmarse con un documento, registro o fuente verificable asociada.
- **Puede inferirse:** dato que un agente puede derivar, siempre marcado como inferencia y con la fuente del razonamiento.
- **Nunca debe inventarse:** dato que, si no existe evidencia, queda `UNKNOWN` y jamás se rellena con un valor plausible.

---

## Entidades

### Sincronizacion documental externa

`ExternalProcessSyncRun` conserva el estado durable del trabajo; cada ejecucion produce un `ExternalProcessSnapshot`. `ExternalProcessDocument` representa la identidad estable de una fila documental oficial y `ExternalProcessDocumentVersion` conserva cada hash descargado, enlazado al `ProcessDocument` existente. `ExternalProcessChangeEvent` registra diferencias verificables y posibles adendas. `ExternalDocumentDownloadJob` separa la descarga de la sincronizacion y de la extraccion. Ninguna de estas entidades participa directamente en la decision deterministica.

### Organization
**Propósito:** tenant de la plataforma; agrupa usuarios, empresas y procesos con aislamiento completo entre organizaciones.

- **Campos conceptuales:** nombre, identificador, estado, configuración.
- **Relaciones:** tiene `User`s, `CompanyProfile`s, `Process`es.
- **Requiere evidencia:** ninguno (dato administrativo).
- **Puede inferirse:** ninguno.
- **Nunca debe inventarse:** n/a.

### User
**Propósito:** persona que opera la plataforma dentro de una organización.

- **Campos conceptuales:** identidad, correo, rol (p. ej. administrador, analista, revisor), estado.
- **Relaciones:** pertenece a una `Organization`; realiza `HumanReview`s; genera `AuditEvent`s.
- **Requiere evidencia:** ninguno.
- **Puede inferirse:** ninguno.
- **Nunca debe inventarse:** n/a.

Implementacion Microfase 10: el usuario operativo se persiste como `AuthUser`, con email
normalizado, hash de password, estado `ACTIVE`/`DISABLED`, roles locales (`ADMIN`, `ANALYST`,
`REVIEWER`, `VIEWER`), sesiones revocables y eventos de login. Esta autenticacion local prepara el
piloto; no implementa SSO ni tenant real.

### CompanyProfile
**Propósito:** perfil de la empresa que evalúa participar: su capacidad jurídica, financiera, técnica y de experiencia.

- **Campos conceptuales:** razón social, NIT, RUP (estado y clasificaciones), códigos UNSPSC inscritos, indicadores financieros por corte (liquidez, endeudamiento, capital de trabajo, patrimonio, etc.), experiencia, personal, certificaciones, capacidades declaradas y fecha de corte de la información.
- **Relaciones:** pertenece a una `Organization`; tiene `CompanyCapability`s, `CompanyEvidenceDocument`s, `CompanyEvidenceLink`s y `CompanyProfileSnapshot`s; es sujeto de `Evaluation`s.
- **Requiere evidencia:** todos los indicadores financieros, el estado del RUP, la experiencia declarada — cada valor debe apuntar a un documento soporte (estados financieros, certificado RUP, certificaciones de experiencia).
- **Puede inferirse:** indicadores derivados aritméticamente de valores con evidencia (p. ej. capital de trabajo = activo corriente − pasivo corriente), marcados como derivados.
- **Nunca debe inventarse:** indicadores financieros, vigencia del RUP, códigos UNSPSC inscritos, montos de experiencia.

### Process
**Propósito:** proceso de contratación de SECOP II bajo análisis.

- **Campos conceptuales:** identificador SECOP, entidad contratante, objeto, modalidad, presupuesto oficial, códigos UNSPSC del proceso, fuente de ingesta (datos abiertos / manual), estado del análisis.
- **Relaciones:** pertenece a una `Organization`; tiene `ProcessVersion`s; es objeto de `Evaluation`s y `Decision`s.
- **Requiere evidencia:** presupuesto, cronograma, modalidad — con referencia al documento o registro de datos abiertos de origen.
- **Puede inferirse:** clasificación temática del objeto, marcada como inferencia.
- **Nunca debe inventarse:** identificador SECOP, presupuesto, fechas del cronograma.

### ProcessVersion
**Propósito:** instantánea versionada del proceso. Las adendas y documentos nuevos crean una versión nueva; los análisis siempre referencian una versión concreta.

- **Campos conceptuales:** número de versión, fecha, causa (publicación inicial, adenda, documento nuevo), resumen de cambios.
- **Relaciones:** pertenece a un `Process`; tiene `ProcessDocument`s y `Requirement`s; las `Decision`s apuntan a una versión.
- **Requiere evidencia:** la causa de la versión (la adenda o documento que la originó).
- **Puede inferirse:** el resumen de cambios entre versiones, marcado como generado.
- **Nunca debe inventarse:** contenido de adendas no recibidas.

### ProcessDocument
**Propósito:** documento del proceso (pliego, anexo, formato, adenda, estudio previo) almacenado de forma inmutable.

- **Campos conceptuales:** nombre, tipo documental, hash del archivo, formato (PDF/DOCX/XLSX/imagen), origen (datos abiertos / carga manual), fecha de incorporación, ruta de almacenamiento.
- **Relaciones:** pertenece a una `ProcessVersion`; tiene `DocumentExtraction`s; es fuente de `Requirement`s y `RequirementEvidence`s.
- **Requiere evidencia:** es en sí mismo evidencia primaria; su integridad se garantiza por hash.
- **Puede inferirse:** el tipo documental (clasificación), marcado como inferencia hasta confirmación.
- **Nunca debe inventarse:** contenido de páginas ilegibles o faltantes (se marcan como no extraíbles).

### DocumentExtraction
**Propósito:** resultado de extraer el contenido de un `ProcessDocument` (texto, tablas, estructura), con calidad medida.

- **Campos conceptuales:** método de extracción (texto nativo, OCR), contenido estructurado por página/sección, métricas de calidad, páginas fallidas, versión del extractor.
- **Relaciones:** pertenece a un `ProcessDocument`; es insumo de `Requirement`s.
- **Requiere evidencia:** n/a (es un derivado técnico del documento).
- **Puede inferirse:** estructura de secciones, marcada con confianza.
- **Nunca debe inventarse:** texto de páginas que no pudieron extraerse — se registran como fallidas.

### Requirement
**Proposito:** requisito normalizado del proceso (habilitante, tecnico, financiero,
juridico, experiencia, personal, documental, tecnico-operativo u otro), unidad
central del analisis posterior. En Microfase 4 no representa cumplimiento ni
decision GO / NO GO; solo captura lo que el pliego exige y la evidencia textual
que soporta esa exigencia. Su contrato operativo esta en
[requirement-normalization.md](requirement-normalization.md).

- **Campos conceptuales:** categoria, alcance, modalidad, descripcion normalizada,
  condicion aplicable, valor esperado, base normativa/procedimental, criticidad,
  subsanabilidad, confianza del extractor, estado de revision humana, llave
  estable y hash de evidencia.
- **Relaciones:** pertenece a un `Process`; proviene de una ejecucion de
  normalizacion; tiene `RequirementEvidence`s; puede tener `RequirementRelation`s
  con duplicados, conflictos o adendas potenciales; sera evaluado en microfases
  posteriores.
- **Requiere evidencia:** su existencia misma; todo requisito aceptado apunta a
  documento, extraccion, segmento, ubicacion y cita exacta verificable.
- **Puede inferirse:** categoria, alcance, modalidad y criticidad propuestas por
  el agente normalizador, siempre con trazabilidad y revision humana pendiente.
- **Nunca debe inventarse:** requisitos que no aparecen en los documentos; valores
  esperados no escritos en el pliego; subsanabilidad no determinable (queda
  `UNKNOWN`); cumplimiento, `GO`, `NO_GO` o valor de empresa.

### RequirementEvidence
**Proposito:** vinculo verificable entre un requisito normalizado y el fragmento
del documento SECOP que lo soporta.

- **Campos conceptuales:** rol, documento, extraccion, segmento, ubicacion,
  cita exacta, offsets, hash de cita, estado de validacion y detalle de error si
  la evidencia fue rechazada.
- **Relaciones:** conecta `Requirement` con `ProcessDocument` y
  `DocumentExtractionSegment`; las evidencias de empresa se modelaran en
  microfases posteriores.
- **Requiere evidencia:** es evidencia por definición; sin documento asociado no existe.
- **Puede inferirse:** nada; el validador solo confirma que la cita existe en el
  segmento indicado.
- **Nunca debe inventarse:** ninguna evidencia; una evidencia sin cita exacta y
  documento verificable es una violacion del modelo.

### CompanyCapability
**Propósito:** capacidad estructurada de la empresa (experiencia por tipo de obra/servicio, equipo disponible, capacidad operativa) usada para contrastar contra requisitos.

- **Campos conceptuales:** tipo de capacidad, descripción, magnitud (monto, cantidad, años), soportes asociados, vigencia.
- **Relaciones:** pertenece a un `CompanyProfile`; se referencia desde `Evaluation`s y `RequirementEvidence`s.
- **Requiere evidencia:** toda magnitud (montos de experiencia, certificaciones, hojas de vida del equipo).
- **Puede inferirse:** agregaciones (p. ej. suma de experiencia por código UNSPSC), marcadas como derivadas.
- **Nunca debe inventarse:** experiencia, certificaciones o equipo no soportados documentalmente.

### CompanyEvidenceDocument
**Proposito:** soporte documental de un perfil de empresa (RUT, RUP, estados financieros, certificado de experiencia, hoja de vida, diploma, certificacion o soporte UNSPSC) almacenado de forma inmutable.

- **Campos conceptuales:** tipo de evidencia, nombre original, hash SHA-256, tamano, content type declarado/detectado, autoridad emisora, fechas de emision/vigencia, estado de revision y estado de extraccion.
- **Relaciones:** pertenece a un `CompanyProfile`; reutiliza un `ProcessDocument` tecnico para pasar por el pipeline de `DocumentExtraction`; puede soportar muchos `CompanyEvidenceLink`s.
- **Requiere evidencia:** es evidencia primaria; su integridad se verifica por hash y no se reemplaza en sitio.
- **Puede inferirse:** tipo documental propuesto por usuario o extractor, siempre revisable.
- **Nunca debe inventarse:** contenido, autoridad, vigencia o texto no extraido.

### CompanyEvidenceLink
**Proposito:** vinculo trazable entre un dato del perfil y una evidencia documental concreta.

- **Campos conceptuales:** sujeto soportado (registro juridico, RUP, UNSPSC, periodo financiero, metrica, experiencia, persona, certificacion o capacidad), documento, extraccion, segmento, cita textual, ubicacion, rol, estado de validacion y estado de revision.
- **Relaciones:** conecta `CompanyProfile` y sus subentidades con `CompanyEvidenceDocument`, `DocumentExtraction` y `ExtractedSegment`.
- **Requiere evidencia:** documento asociado; cuando hay segmento/cita, la cita debe existir en el texto extraido.
- **Puede inferirse:** nada; la validacion solo confirma pertenencia, ubicacion y cita.
- **Nunca debe inventarse:** un soporte sin documento real o una cita no encontrada.

### CompanyProfileSnapshot
**Proposito:** version inmutable del perfil usada como base futura de evaluaciones contra procesos.

- **Campos conceptuales:** version, estado (`DRAFT` o `PUBLISHED`), payload canonico, digest SHA-256, estado de completitud, fecha de creacion y publicacion.
- **Relaciones:** pertenece a un `CompanyProfile`; futuras `Evaluation`s deben referenciar una version especifica, no el perfil editable.
- **Requiere evidencia:** incluye solo referencias a evidencias y metadatos existentes al momento de crearse.
- **Puede inferirse:** estado de completitud calculado deterministicamente.
- **Nunca debe inventarse:** datos faltantes; quedan ausentes o marcados como pendientes.

### FinancialEvaluation
**Proposito:** evaluacion deterministica inicial de requisitos financieros contra un
`CompanyProfileSnapshot` publicado.

- **Campos conceptuales:** job, run, digest de entrada, reglas financieras, formulas versionadas,
  conteos por estado, resultados por requisito, calculos derivados, eventos y revisiones manuales.
- **Relaciones:** referencia `Process`, ejecucion de normalizacion, `CompanyProfile`,
  `CompanyProfileSnapshot`, `Requirement`s financieros y reglas usadas.
- **Requiere evidencia:** cada resultado distinto de `UNKNOWN` debe provenir de metrica soportada o
  verificada en el snapshot; la evidencia conflictiva produce `CONFLICTING_EVIDENCE`.
- **Puede inferirse:** mapeo conservador de metrica, operador y periodo desde el requisito; si no es
  claro queda `AMBIGUOUS`.
- **Nunca debe inventarse:** metricas, periodos, valores exigidos, moneda, soportes ni cumplimiento.
  No produce `GO`, `NO_GO` ni decision final.

### SpecializedEvaluation
**Proposito:** evaluacion deterministica de requisitos juridicos, de experiencia y tecnicos contra
un `CompanyProfileSnapshot` publicado.

- **Campos conceptuales:** job, run, dominio (`LEGAL`, `EXPERIENCE`, `TECHNICAL`), reglas
  especializadas por requisito, manifiesto y digest de entrada, resultados, evidencias, eventos y
  revisiones manuales.
- **Relaciones:** referencia `Process`, ejecucion de normalizacion, `CompanyProfile`,
  `CompanyProfileSnapshot`, `Requirement`s aplicables, reglas usadas y evidencias del perfil.
- **Requiere evidencia:** cada resultado positivo o negativo debe apuntar a registros del snapshot y
  soportes cuando existan; evidencia declarada sin soporte produce `UNKNOWN` o revision.
- **Puede inferirse:** mapeo conservador de tipo de regla, operador y sujeto desde el requisito.
  Cuando el texto no permite mapearlo, queda `UNSUPPORTED` o `AMBIGUOUS`.
- **Nunca debe inventarse:** vigencias, certificaciones, experiencia, personal, equivalencias
  tecnicas, codigos UNSPSC, documentos ni cumplimiento. No produce `GO`, `NO_GO` ni decision final.

### Evaluation
**Propósito:** resultado de un agente evaluador especializado sobre un conjunto de requisitos de una versión del proceso contra un perfil de empresa.

- **Campos conceptuales:** tipo de evaluación (jurídica, financiera, experiencia, técnica, operativa, económica), estado por requisito, hallazgos, `AgentRun` asociado.
- **Relaciones:** referencia `ProcessVersion`, `CompanyProfile`, `Requirement`s; produce `Finding`s; es insumo del motor de decisión.
- **Requiere evidencia:** cada estado de cumplimiento asignado debe referenciar `RequirementEvidence`s.
- **Puede inferirse:** los estados propuestos, siempre con confianza y evidencia citada.
- **Nunca debe inventarse:** cumplimientos sin evidencia (el estado correcto es `UNKNOWN`).

### Finding
**Propósito:** hallazgo puntual y trazable producido durante una evaluación: incumplimiento, riesgo, conflicto de evidencia, dato faltante.

- **Campos conceptuales:** tipo, severidad, descripción, requisito asociado, evidencia citada, recomendación.
- **Relaciones:** pertenece a una `Evaluation`; referencia `Requirement` y `RequirementEvidence`s.
- **Requiere evidencia:** todo hallazgo cita la evidencia que lo motiva.
- **Puede inferirse:** la severidad propuesta, revisable por humanos.
- **Nunca debe inventarse:** hallazgos sin base documental.

### Decision
**Propósito:** decisión final auditable sobre un proceso para una empresa, producida por el motor determinístico.

- **Campos conceptuales:** resultado (`GO`, `GO_CONDICIONADO`, `BUSCAR_ALIADO`, `NO_GO`, `NO_CARGAR`, `PENDIENTE_INFORMACION`), requisitos determinantes, condiciones (si aplica), versión de reglas usada (`DecisionRule`), versiones de prompts y modelos involucrados, fecha, estado de revisión humana.
- **Relaciones:** referencia `ProcessVersion`, `CompanyProfile`, `Evaluation`s, `DecisionRule` y `HumanReview` cuando exista.
- **Requiere evidencia:** cada factor determinante de la decisión apunta a requisitos y evidencia concretos.
- **Puede inferirse:** nada — la decisión es producto determinístico de reglas versionadas.
- **Nunca debe inventarse:** una decisión sin cadena completa requisito → evidencia → evaluación → regla.

Implementacion Microfase 7: la decision persistida es preliminar y se modela como `DecisionRun`.
Referencia un `Process`, una normalizacion completada, un `CompanyProfileSnapshot` publicado, una
evaluacion financiera completada y un `DecisionPolicyVersion`. El resultado automatico queda en
`engine_outcome`; las revisiones humanas usan `reviewed_outcome` y `effective_outcome` sin sobrescribir
el resultado original. Las acciones (`DecisionActionItem`) son tareas abiertas, reconocidas,
resueltas o descartadas; cambiar una accion no recalcula el run historico.

Implementacion Microfase 8: el `DecisionRun` incorpora resultados completados de
`SpecializedEvaluation` para los dominios juridico, experiencia y tecnico cuando coinciden proceso,
normalizacion, empresa y snapshot. Si no existe resultado especializado para un requisito obligatorio
aplicable, el motor conserva `NOT_EVALUATED`.

### DecisionRule
**Propósito:** versión inmutable del conjunto de reglas del motor determinístico usado para producir decisiones.

- **Campos conceptuales:** versión, contenido de reglas, fecha de vigencia, changelog.
- **Relaciones:** referenciada por `Decision`s.
- **Requiere evidencia:** n/a (artefacto del sistema, versionado en el repositorio).
- **Puede inferirse:** nada.
- **Nunca debe inventarse:** n/a; las reglas solo cambian por gestión de cambios documentada.

Implementacion Microfase 7: las reglas estan en codigo tipado y la politica en
`config/decision-policies/v1/policy.json`. Cada ejecucion persiste `DecisionRuleEvaluation` con
hechos, requisitos, hallazgos, prioridad, razon y resultado sugerido.

### AgentRun
**Propósito:** registro de una ejecución concreta de un agente de IA: qué modelo, qué prompt, qué entradas, qué salida, qué costo.

- **Campos conceptuales:** agente, `PromptVersion` usada, modelo y versión, entradas (referencias), salida estructurada, tokens consumidos, duración, errores, resultado de validación de esquema.
- **Relaciones:** referencia `PromptVersion`; es referenciado por `DocumentExtraction`s, `Evaluation`s y `Decision`s.
- **Requiere evidencia:** n/a (es el registro de auditoría técnica).
- **Puede inferirse:** nada.
- **Nunca debe inventarse:** métricas de ejecución; se registran las reales.

### PromptVersion
**Propósito:** versión inmutable de un prompt de agente, para reproducibilidad.

- **Campos conceptuales:** agente al que pertenece, version, contenido,
  esquema de salida asociado, hash SHA-256, estado activo, fecha, changelog.
- **Relaciones:** referenciada por `AgentRun`s y por ejecuciones de
  normalizacion de requisitos.
- **Requiere evidencia:** n/a.
- **Puede inferirse:** nada.
- **Nunca debe inventarse:** n/a.

### HumanReview
**Propósito:** revisión humana de una decisión, evaluación o conflicto de evidencia; requisito obligatorio para decisiones críticas.

- **Campos conceptuales:** revisor, objeto revisado, veredicto (confirma, corrige, rechaza), justificación, fecha.
- **Relaciones:** realizada por un `User`; referencia `Decision`, `Evaluation` o `Finding`.
- **Requiere evidencia:** la justificación del revisor queda registrada.
- **Puede inferirse:** nada.
- **Nunca debe inventarse:** una revisión humana jamás se simula ni se autocompleta.

### DecisionReportPackage
**Proposito:** paquete inmutable de reporte ejecutivo generado desde una decision preliminar completada.

- **Campos conceptuales:** decision referenciada, input digest, package digest, version de motor de
  reporte, version/hash de templates, estado, artefactos, manifest.
- **Relaciones:** pertenece a un `Process`; referencia una `Decision`; contiene
  `DecisionReportArtifact`s.
- **Requiere evidencia:** deriva de una decision persistida y de sus hallazgos, reglas, acciones y
  evidencias.
- **Puede inferirse:** resumenes ejecutivos derivados de campos persistidos, sin reglas nuevas.
- **Nunca debe inventarse:** resultados GO / NO GO, acciones, evidencias, revisiones humanas o
  cumplimiento no presente en la decision original.

### AuditEvent
**Propósito:** evento inmutable de auditoría de toda acción relevante (ingesta, extracción, evaluación, decisión, revisión, cambios de perfil).

- **Campos conceptuales:** actor (usuario o agente), acción, objeto, timestamp, detalle.
- **Relaciones:** referencia cualquier entidad del sistema.
- **Requiere evidencia:** n/a (es el mecanismo de evidencia del sistema).
- **Puede inferirse:** nada.
- **Nunca debe inventarse:** n/a; los eventos no se editan ni se eliminan.

Implementacion Microfase 10: los eventos operacionales de autenticacion, administracion y acceso se
persisten en `operational_audit_events`, separados de los eventos de decision para no mezclar
controles de plataforma con trazabilidad requisito-evidencia-decision.

---

## Diagrama de relaciones principales

```mermaid
erDiagram
    Organization ||--o{ User : tiene
    Organization ||--o{ CompanyProfile : tiene
    Organization ||--o{ Process : tiene
    Process ||--o{ ProcessVersion : versiona
    ProcessVersion ||--o{ ProcessDocument : contiene
    ProcessDocument ||--o{ DocumentExtraction : produce
    ProcessVersion ||--o{ Requirement : define
    Requirement ||--o{ RequirementEvidence : "se acredita con"
    CompanyProfile ||--o{ CompanyCapability : declara
    CompanyProfile ||--o{ CompanyEvidenceDocument : soporta
    CompanyEvidenceDocument ||--o{ CompanyEvidenceLink : vincula
    CompanyProfile ||--o{ CompanyProfileSnapshot : versiona
    ProcessVersion ||--o{ Evaluation : "es evaluada en"
    CompanyProfile ||--o{ Evaluation : "es sujeto de"
    Evaluation ||--o{ Finding : produce
    Evaluation }o--|| AgentRun : "registrada por"
    AgentRun }o--|| PromptVersion : usa
    ProcessVersion ||--o{ Decision : recibe
    Decision }o--|| DecisionRule : aplica
    Decision ||--o| HumanReview : "puede requerir"
```

---

## Categorías iniciales de requisitos

| Categoría | Ejemplos típicos |
| --- | --- |
| Jurídicos | Existencia y representación legal, inhabilidades e incompatibilidades, paz y salvos, sanciones. |
| Financieros | Índice de liquidez, nivel de endeudamiento, razón de cobertura de intereses, capital de trabajo, patrimonio. |
| Organizacionales | Indicadores de capacidad organizacional (rentabilidad del patrimonio y del activo). |
| Experiencia | Contratos acreditables, montos en SMMLV, códigos UNSPSC, experiencia específica y general. |
| Técnicos | Especificaciones del bien/servicio, normas técnicas, metodologías, certificaciones de calidad. |
| Equipo de trabajo | Perfiles, formación, experiencia y dedicación del personal mínimo exigido. |
| Garantías | Seriedad de la oferta, cumplimiento, calidad, salarios, responsabilidad civil. |
| Cronograma | Fechas de cierre, audiencias, subsanación, adjudicación; plazos de ejecución. |
| Económicos | Presupuesto oficial, forma de pago, anticipos, estructura de precios, AIU. |
| Operativos | Capacidad instalada, cobertura geográfica, logística, disponibilidad de equipos. |
| Documentales | Formatos exigidos, cartas, anexos diligenciados, certificaciones a presentar. |
| Riesgos e inhabilidades | Matriz de riesgos del proceso, causales de rechazo, conflictos de interés. |

> **Aclaración obligatoria:** los umbrales (p. ej. índice de liquidez mínimo), los documentos exigidos y las causales de rechazo o subsanabilidad **dependen de cada proceso concreto y de su pliego**. Ningún valor observado en un caso específico debe convertirse en regla universal del sistema. Las reglas del motor determinístico operan sobre los valores extraídos de cada pliego, no sobre umbrales fijos codificados.
