# Seguridad y gobernanza — PliegoCheck-SECOP

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

## 5. Seguridad frente a los modelos de IA

- **Documentos externos tratados como datos, nunca como instrucciones.** Todo contenido documental se delimita como dato a analizar; los prompts lo declaran explícitamente ([agent-prompting-standard.md](agent-prompting-standard.md)).
- **Resistencia básica a prompt injection documental:** validación de salidas contra esquema (Structured Outputs), verificación de citas por el `EvidenceVerificationAgent`, y rechazo de salidas que no validan. Un pliego no puede "ordenar" un `GO`.
- **Herramientas autorizadas por agente:** cada agente solo dispone de las herramientas de su contrato ([agent-contracts.md](agent-contracts.md)); no hay herramientas globales.
- **Límites de costo y tokens:** presupuesto máximo por ejecución y por análisis; al agotarse, el pipeline se detiene y escala, nunca degrada la calidad silenciosamente.

## 6. Gobernanza de la decisión

- **Revisión humana obligatoria para decisiones críticas:** evidencia contradictoria, ambigüedad jurídica, causales insubsanables y cualquier `requires_human_review` bloquean la decisión definitiva hasta `HumanReview`.
- **Prohibición de afirmar certeza jurídica:** el sistema presenta análisis y evidencia; nunca afirma que una interpretación jurídica es definitiva. El resultado es apoyo a la decisión, no dictamen.
- **Gestión de cambios en reglas:** las reglas del motor determinístico cambian solo mediante nueva versión (`DecisionRule`) con changelog y revisión; los cambios nunca son retroactivos sobre decisiones emitidas.

## 7. Amenazas específicas y mitigaciones

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

## 8. Observabilidad mínima

Eventos de ejecución con: consumo de tokens y costo por `AgentRun`, tiempos por etapa, errores y reintentos, versiones de prompt y modelo, y estado del pipeline. Sin esta telemetría no se autoriza operación en producción.
