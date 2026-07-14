# Compatibilidad de oportunidades

El motor evalúa doce componentes: relevancia, UNSPSC, experiencia, ajuste financiero preliminar, capacidad técnica preliminar, preparación jurídica preliminar, ubicación, cuantía, urgencia, documentos, completitud y posible necesidad de aliado.

Cada componente conserva estado, score 0–100, peso, aporte ponderado, `reason_code`, parámetros, referencias de evidencia y advertencias. Las explicaciones salen de plantillas versionadas; no se genera prosa con IA. `UNKNOWN`, `NOT_APPLICABLE`, `CONFLICTING` y `MISMATCH` no generan aporte positivo.

La relevancia usa normalización Unicode, tokens y sinónimos controlados. UNSPSC compara producto, clase, familia y segmento; nunca sustituye experiencia acreditada. Experiencia, cuantía, técnica y jurídica solo usan datos estructurados presentes en el snapshot. Sin requisitos normalizados permanecen preliminares.

La respuesta registra por separado `compatibility_score`, `urgency_score` e `information_completeness`, además de campos, documentos, evaluaciones y datos empresariales faltantes.
