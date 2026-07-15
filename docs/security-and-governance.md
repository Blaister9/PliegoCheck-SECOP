# Seguridad y gobernanza — PliegoCheck-SECOP

Microfase 21 mantiene SECOP live bajo opt-in y límites, exige snapshot publicado y separa datos públicos del perfil sintético o autorizado. Reportes, backups y datos live permanecen ignorados; entrega externa queda local o dry-run. Sin evidencia humana no se afirma validación de usuarios ni producción.

Microfase 20 mantiene entrega externa apagada por defecto. SMTP valida headers/dominios y exige TLS fuera de Mailpit local. Webhooks requieren HTTPS, allowlist, DNS/IP pública, cero redirects y HMAC; PostgreSQL solo conserva `secret_reference`. Payloads minimizan datos y la retención limpia contenido antes que metadatos. Un fallo externo nunca altera `OpportunityAlert`.

Los monitores requieren `monitor:read/write/run`; las alertas, `alert:read/manage`. Analyst administra ambos, Reviewer lee monitores y administra alertas, Viewer solo lee. Backend aplica permisos. Filtros, errores y auditoría excluyen secretos y payloads SECOP completos.

Controles de seguridad, aislamiento y gobernanza de decisiones que la plataforma debe cumplir desde su primera implementación. Este documento define política; los mecanismos concretos se implementarán en las microfases del [roadmap](roadmap.md).

## 1. Aislamiento y control de acceso

- **Separación por organización (tenant):** toda entidad de datos pertenece a una `Organization`. Ninguna consulta, agente ni almacenamiento puede cruzar organizaciones. El aislamiento se aplica en la capa de datos, no solo en la UI.
- **Control de acceso:** usuarios con roles diferenciados (administrador, analista, revisor). Las acciones críticas (aprobar decisiones, modificar perfil de empresa, cambiar reglas) se restringen por rol.
- **Protección de documentos empresariales:** los documentos de perfil de empresa (estados financieros, RUP, certificaciones) son los datos más sensibles del sistema; acceso solo dentro del tenant y con registro de auditoría.

## 2. Secretos y cifrado

- **Secretos únicamente en variables de entorno o gestores de secretos.** Prohibido en código, archivos del repositorio, ejemplos, tests, logs o mensajes de commit.
- **Cifrado en tránsito** (TLS) en toda comunicación: navegador↔API, API↔almacenamiento, API↔proveedores de IA.
- Los archivos `.env` reales nunca se versionan; solo plantillas `.env.example` sin valores.

## 3. Trazabilidad y auditoría

- **Trazabilidad completa:** requisito → evidencia → evaluación → regla → decisión, con `AuditEvent`s inmutables para toda acción relevante.
- **Registro del modelo y versión del prompt:** cada `AgentRun` almacena modelo, versión de prompt (`PromptVersion`), entradas y salida.
- **Reproducibilidad de decisiones:** misma entrada + misma versión de reglas (`DecisionRule`) ⇒ misma decisión. Las versiones de reglas son inmutables.
- **Logs sin contenido sensible innecesario:** los logs operan con identificadores y metadatos; no vuelcan contenido documental ni datos financieros salvo necesidad justificada y controlada.

## 4. Ciclo de vida de documentos y datos

- **Retención y eliminación:** política de retención definida por organización; al eliminar una organización o proceso se eliminan sus documentos del almacenamiento y sus derivados, conservando los `AuditEvent`s mínimos exigibles.
- **Reprocesamiento por adendas:** cuando aparecen adendas o documentos nuevos se crea una `ProcessVersion` nueva y se reanaliza; las decisiones anteriores quedan asociadas a su versión original, nunca se sobrescriben.
- **Carga manual segura (Microfase 2):** los documentos originales se guardan fuera de PostgreSQL, con `storage_key` relativa generada por servidor y SHA-256 calculado sobre los bytes originales. Las respuestas no exponen rutas físicas, temporales ni claves internas.
- **Validación de archivos:** se rechazan rutas, nombres reservados, doble extensión peligrosa, formatos no permitidos, archivos vacíos, tamaños excesivos, `Content-Type` incoherente y firmas mágicas incompatibles cuando aplica. Los documentos todavía no se extraen ni se interpretan.
- **Evidencias de empresa (Microfase 5):** los soportes empresariales reutilizan la misma validacion y almacenamiento inmutable; la API no expone rutas fisicas ni `storage_key`. Los identificadores tributarios y personales se normalizan para unicidad, pero se muestran enmascarados en listados y UI.
- **Snapshots de perfil:** un snapshot publicado es inmutable y se valida por digest SHA-256 canonico. Las evaluaciones futuras deben referenciar una version especifica del perfil para evitar que cambios posteriores alteren resultados historicos.

## 5. Controles de extraccion documental

- **Extraccion deterministica:** la Microfase 3 no usa LLM ni interpreta requisitos; solo produce
  metadata, advertencias y segmentos trazables.
- **Estados explicitos:** imagenes o PDFs sin texto digital quedan `NEEDS_OCR`, documentos cifrados
  quedan `ENCRYPTED` y formatos heredados quedan `UNSUPPORTED`.
- **Verificacion de integridad:** antes de extraer, el worker recalcula SHA-256 y compara contra la
  metadata persistida.
- **Limites operativos:** paginas, caracteres, hojas, filas, entradas ZIP, tamano descomprimido,
  ratio de compresion y timeout se controlan por variables de entorno.
- **Contenedores Office:** se inspeccionan como ZIP para rechazar macros, rutas peligrosas y
  estructuras anormalmente grandes.
- **Render seguro:** la web muestra segmentos como texto plano, sin interpretar HTML contenido en los
  documentos.

## 6. Seguridad frente a los modelos de IA

- **Documentos externos tratados como datos, nunca como instrucciones.** Todo contenido documental se delimita como dato a analizar; los prompts lo declaran explícitamente ([agent-prompting-standard.md](agent-prompting-standard.md)).
- **Resistencia básica a prompt injection documental:** validación de salidas contra esquema (Structured Outputs), verificación de citas por el `EvidenceValidator`, y rechazo de salidas que no validan. Un pliego no puede "ordenar" un `GO`.
- **Herramientas autorizadas por agente:** cada agente solo dispone de las herramientas de su contrato ([agent-contracts.md](agent-contracts.md)); no hay herramientas globales.
- **Límites de costo y tokens:** presupuesto máximo por ejecución y por análisis; al agotarse, el pipeline se detiene y escala, nunca degrada la calidad silenciosamente.
- **Microfase 4 implementada:** la normalizacion usa Responses API con Structured Outputs,
  `tools=[]`, prompts versionados, snapshot inmutable y `EvidenceValidator` deterministico. No se
  suben archivos originales a OpenAI; solo segmentos seleccionados y metadata minima.
- **IA deshabilitada por defecto:** `PLIEGOCHECK_AI_ENABLED=false`; la ausencia de clave produce un
  error controlado cuando se solicita operacion real.
- **Provider falso aislado:** solo se habilita con `PLIEGOCHECK_ALLOW_FAKE_NORMALIZATION_PROVIDER`
  para tests/evals; no es seleccionable publicamente en operacion normal.
- **Microfase 5 sin IA nueva:** la captura de perfil, completitud y vinculacion dato-evidencia son deterministicas. La extraccion de soportes empresariales reutiliza el pipeline documental local y no envia archivos originales a proveedores de IA.
- **Microfase 6 sin IA:** la evaluacion financiera es deterministica. No llama OpenAI, no interpreta
  libremente evidencia y solo usa requisitos normalizados, reglas persistidas y snapshots publicados.
  Los overrides manuales quedan auditados y no cambian el resultado automatico original.
- **Microfase 7 sin IA:** el motor de decision preliminar no llama OpenAI ni ningun modelo. Consume
  hallazgos canonicos, cobertura y una politica versionada; las categorias sin adaptador quedan
  `NOT_EVALUATED` y no se interpretan como cumplimiento.
- **Microfase 8 sin IA:** los evaluadores juridico, experiencia y tecnico tampoco llaman modelos.
  Consumen reglas persistidas y snapshots publicados; dato faltante, declarado sin soporte o no
  comparable produce `UNKNOWN`.
- **Microfase 9 sin IA:** el reporte ejecutivo no llama modelos, no recalcula decision y no ejecuta
  reglas nuevas. Solo renderiza datos persistidos con templates versionados.
- **Microfase 10 sin IA:** autenticacion, autorizacion, sesiones, auditoria operacional, readiness,
  headers y backup/restore son controles deterministas. No usan modelos ni cambian decisiones.
- **Microfase 12 sin IA:** deployment readiness, backup check, rollback, observabilidad local y
  release candidate son controles operativos. No llaman modelos ni agregan reglas de decision.
- **Microfase 13 sin IA:** scripts controlled, data scan, kit de usuarios piloto, acta, matriz de
  hallazgos y evals de validacion son controles operativos. No llaman modelos ni agregan reglas de
  decision.
- **Microfase 14 sin IA:** cierre MVP, hallazgos finales, criterios de aceptacion/no produccion,
  guia de demo, `mvp:eval` y `mvp:data-scan` son controles documentales y operativos. No llaman
  modelos, no agregan reglas de decision y no habilitan produccion.

## 7. Gobernanza de la decisión

- **Revisión humana obligatoria para decisiones críticas:** evidencia contradictoria, ambigüedad jurídica, causales insubsanables y cualquier `requires_human_review` bloquean la decisión definitiva hasta `HumanReview`.
- **Prohibición de afirmar certeza jurídica:** el sistema presenta análisis y evidencia; nunca afirma que una interpretación jurídica es definitiva. El resultado es apoyo a la decisión, no dictamen.
- **Gestión de cambios en reglas:** las reglas del motor determinístico cambian solo mediante nueva versión (`DecisionRule`) con changelog y revisión; los cambios nunca son retroactivos sobre decisiones emitidas.
- **Decision preliminar:** `DecisionRun.engine_outcome` conserva el resultado automatico original.
  `reviewed_outcome` y `effective_outcome` registran confirmaciones u overrides humanos sin
  recalcular historicos.
- **Reporte ejecutivo:** todo paquete debe mostrar avisos de no concepto juridico, no recomendacion
  oficial y necesidad de revision humana antes de uso externo.

## 8. Amenazas específicas y mitigaciones

| Amenaza | Mitigación |
| --- | --- |
| Prompt injection dentro de pliegos (texto que intenta manipular a los agentes) | Documentos como datos, salidas validadas contra esquema, verificación de evidencia independiente, herramientas restringidas por agente. |
| Documentos modificados o incompletos | Hash de integridad por documento, inventario documental con detección de faltantes, páginas fallidas registradas explícitamente. |
| Anexos contradictorios entre sí o con el pliego | Detección de conflictos en normalización, estado `CONFLICTING_EVIDENCE`, revisión humana obligatoria (regla R7 del [motor](decision-engine.md)). |
| Alucinación de requisitos (requisitos que no existen en los documentos) | Origen obligatorio (documento/página/sección) por requisito; el `EvidenceVerificationAgent` verifica que las citas correspondan al contenido real. |
| Uso de información empresarial desactualizada | Fechas de corte y vigencia en perfil y evidencias; evidencia vencida degrada el estado y genera hallazgo. |
| Fuga entre organizaciones | Aislamiento por tenant en la capa de datos, herramientas de agentes limitadas al tenant en ejecución, pruebas de aislamiento. |
| Resultado `GO` con evidencia insuficiente | Regla R3/R6/R8 del motor: sin evidencia suficiente el resultado es `PENDIENTE_INFORMACION`; `COMPLIES` sin evidencia se degrada a `UNKNOWN`. |
| Cambio de condiciones por adendas no procesadas | Versionado de procesos (`ProcessVersion`) y reprocesamiento obligatorio al incorporar adendas; las decisiones citan la versión analizada. |
| Manipulación del perfil de empresa (inflar capacidades) | Toda capacidad exige soporte documental, cambios de perfil auditados (`AuditEvent`), y las decisiones citan las evidencias exactas usadas. |
| ZIP Slip o rutas peligrosas en artefactos de reporte | El ZIP de reporte usa nombres controlados, sin directorios, rutas absolutas ni `..`; cada artefacto tiene SHA-256. |
| XSS en reporte o preview | Campos dinamicos HTML escapados y preview web como texto plano, sin `dangerouslySetInnerHTML`. |
| Acceso no autenticado a API operativa | Sesion persistida por cookie `HttpOnly`, permisos por rol y denegacion con `request_id` auditable. |
| Configuracion insegura para piloto | `PLIEGOCHECK_PILOT_MODE=true` exige autenticacion activa, cookie segura, secreto explicito y CORS cerrado. |
| Perdida local de datos de piloto | Backup local excluye secretos, genera manifest con SHA-256 y restore requiere confirmacion explicita. |

## 9. Observabilidad mínima

Eventos de ejecución con: consumo de tokens y costo por `AgentRun`, tiempos por etapa, errores y reintentos, versiones de prompt y modelo, y estado del pipeline. Sin esta telemetría no se autoriza operación en producción.

## 10. Piloto controlado (Microfase 11)

El piloto controlado opera con **datos exclusivamente sinteticos** y con autenticacion, permisos y
auditoria activos; no desactiva la seguridad para la validacion principal. Reglas:

- Sin datos reales de entidades, empresas, personas, procesos o documentos.
- Sin OpenAI ni servicios externos en el flujo de piloto.
- Las contrasenas demo no se versionan; se pasan por argumento o variable de entorno.
- `pnpm pilot:reset --confirm` elimina unicamente datos marcados como piloto (usuarios
  `@pilot.pliegocheck.local`, el proceso piloto y la empresa piloto); nunca datos ajenos ni `.env`.
- El paquete de reporte descargado no contiene `.env`, secretos ni rutas fisicas (verificado por eval).
- El resultado del piloto es una decision preliminar deterministica que requiere revision humana y no
  constituye concepto juridico.

## 11. Despliegue controlado (Microfase 12)

Controlado/piloto no equivale a produccion. Antes de abrir acceso a usuarios piloto deben pasar
`pnpm deployment:eval`, `pnpm deployment:backup-check`, `pnpm pilot:eval`, CI y checklist manual de
navegador. No se autoriza uso con datos reales sin SSO/MFA o decision explicita de riesgo aceptado.

## 12. Validacion con usuarios piloto (Microfase 13)

Este despliegue controlado es para validacion piloto con datos sinteticos. No es produccion.

- `pnpm controlled:data-scan` debe pasar antes de la sesion.
- Los roles `ADMIN`, `ANALYST`, `REVIEWER` y `VIEWER` deben validarse con acciones permitidas y
  denegadas.
- El feedback se registra con escenario, rol, tarea, severidad, evidencia, decision, fase destino y
  estado.
- Si aparece dato real, secreto, token, cookie o ruta fisica sensible, la sesion se pausa y el
  hallazgo se clasifica como `BLOCKER`.

## 13. Cierre MVP controlado (Microfase 14)

No se recibió retroalimentación real de usuarios piloto en esta microfase. El cierre MVP no autoriza
produccion ni uso con datos reales. Antes de evolucionar a piloto real deben estar aceptados los
criterios de [non-production-criteria.md](non-production-criteria.md), el data scan debe pasar y los
responsables humanos deben decidir continuidad en Microfase 15.

## 14. Fuentes públicas SECOP (Microfase 16)

El conector usa únicamente APIs públicas verificadas de Datos Abiertos Colombia. La consulta tiene
límite, timeout, reintentos acotados, caché, rate limit y User-Agent identificable. El token Socrata
es opcional y nunca se versiona. Una lista permitida excluye campos personales no necesarios; el
payload reducido se almacena para auditoría y no se expone en los listados web/API.

La URL oficial es evidencia de procedencia, no garantía de vigencia o completitud. Importar no
autoriza descarga masiva, scraping, login, presentación de ofertas o trámites, y no ejecuta el motor
de decisión. Los fallos y campos ausentes se registran explícitamente.

## 15. Documentos publicos externos (Microfase 17)

Las URLs SECOP son entrada no confiable. La descarga exige HTTPS, puerto 443, host exacto en allowlist y resolucion DNS exclusivamente a IP publica antes de cada solicitud y redireccion. Se rechazan credenciales embebidas, HTML, tipos fuera de allowlist, firmas inconsistentes, macros Office y archivos que excedan el limite declarado o real. Los bytes se escriben a temporal mientras se calcula SHA-256 y solo se mueven al storage despues de validar. Un fallo de base de datos compensa eliminando el objeto nuevo.

La metadata externa no se trata como instruccion, evidencia de cumplimiento ni decision. Las posibles adendas quedan `requires_human_review`; la ausencia de datos se conserva como ausencia o advertencia. Los contratos publicos nunca exponen claves de almacenamiento.
# Controles de la bandeja de oportunidades

Solo se evalúan snapshots empresariales publicados. Los permisos `opportunity:read|discover|assess|review|import` se aplican en backend y las denegaciones siguen la auditoría operacional. La bandeja no expone payloads crudos, storage keys ni datos empresariales sensibles; eventos guardan metadatos acotados. Discovery público conserva límites, allowlists y controles del conector SECOP.
