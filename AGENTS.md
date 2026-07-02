# AGENTS.md — Reglas permanentes para agentes de programación

Estas reglas aplican a **cualquier agente de IA o desarrollador asistido por IA** que trabaje en este repositorio. Son permanentes: no dependen de la microfase en curso.

## 1. Proceso de trabajo

1. **Inspecciona antes de modificar.** Lee el código y la documentación afectada antes de cambiar cualquier archivo. No asumas comportamiento que no hayas verificado.
2. **Trabaja siempre en ramas.** Nunca modifiques `main` directamente. Crea una rama descriptiva (`docs/...`, `feat/...`, `fix/...`) y llega a `main` solo vía Pull Request.
3. **Cambios pequeños y verificables.** Prefiere una serie de cambios acotados, cada uno con un objetivo claro, sobre un cambio masivo imposible de revisar.
4. **Ejecuta las validaciones existentes antes de cerrar.** Si el repositorio tiene lint, tests, verificación de tipos o CI, deben pasar antes de dar la tarea por terminada.
5. **Actualiza la documentación cuando cambie la arquitectura.** Un cambio estructural sin actualizar `docs/` está incompleto.
6. **No uses** `git push --force`, `git reset --hard` sobre trabajo compartido, reescritura de historial publicado, commits vacíos ni eliminación de archivos ajenos a tu tarea.

## 2. Integridad de la información

7. **No inventes funcionalidades, clientes, métricas ni cumplimiento legal.** Si algo no existe en el código o en evidencia verificable, no lo afirmes.
8. **No conviertas interpretaciones del LLM en hechos.** Distingue siempre entre texto explícito de una fuente, inferencia razonada y dato desconocido.
9. **Registra la incertidumbre con estados explícitos** (`UNKNOWN`, `PENDIENTE_INFORMACION`, `requires_human_review`), nunca con valores inventados o con silencio.
10. **No hardcodees reglas particulares de un proceso como si fueran reglas universales.** Umbrales financieros, documentos exigidos y causales de rechazo dependen de cada pliego concreto.
11. **No incluyas secretos** (claves de API, tokens, credenciales, cadenas de conexión) en archivos del repositorio, ejemplos, tests ni mensajes de commit.

## 3. Reglas del dominio de decisión

12. **Mantén la trazabilidad requisito → evidencia → decisión.** Toda evaluación debe poder responder: ¿qué requisito?, ¿qué evidencia lo respalda?, ¿qué regla produjo el resultado?
13. **Separa la inferencia de IA de las reglas determinísticas.** Los agentes LLM extraen, normalizan y evalúan; la decisión final la produce exclusivamente el motor determinístico ([docs/decision-engine.md](docs/decision-engine.md)).
14. **Nunca decidas `GO` cuando falte evidencia crítica.** La ausencia de evidencia produce `PENDIENTE_INFORMACION`.
15. **No mezcles extracción documental con decisión final.** El agente que extrae texto no determina cumplimiento; el que evalúa no modifica el texto extraído.
16. **Ningún agente único produce silenciosamente la decisión definitiva.** La decisión pasa por evaluadores especializados, verificación de evidencia y motor determinístico.

## 4. Contratos y salidas

17. **Usa contratos tipados** (Pydantic / JSON Schema / TypeScript) para toda comunicación entre componentes y agentes, según [docs/agent-contracts.md](docs/agent-contracts.md).
18. **Usa salidas estructuradas** (Structured Outputs) en toda llamada a modelos. Una salida que no valide contra su esquema se rechaza y se reintenta o escala; nunca se interpreta libremente.
19. **Cada ejecución de agente registra** versión de prompt, modelo utilizado y entradas, para reproducibilidad y auditoría.

## 5. Formato obligatorio de entrega

Toda tarea futura en este repositorio se reporta con este formato:

```text
Estado:
Cambios:
Archivos:
Validaciones:
Riesgos:
Commit:
Pull Request:
Merge:
```

- **Estado:** completado, parcial o bloqueado (con el bloqueo exacto).
- **Cambios:** resumen de lo realizado.
- **Archivos:** rutas creadas o modificadas.
- **Validaciones:** qué se verificó y su resultado real (no simulado).
- **Riesgos:** deuda o riesgos que quedan pendientes.
- **Commit / Pull Request / Merge:** referencias reales; si algo no ocurrió, se dice explícitamente.
