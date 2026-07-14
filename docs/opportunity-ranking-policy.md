# Política de priorización de oportunidades

La versión `1.0.0` vive en `config/opportunity-policies/v1/policy.json`; términos y sinónimos están en `terms.json`. El cargador rechaza claves inesperadas, componentes desconocidos, pesos que no sumen exactamente uno, umbrales inválidos, outcomes incompletos y reason codes duplicados.

Pesos: relevancia 0.22; UNSPSC y experiencia 0.14 cada uno; financiero, técnico y cuantía 0.08; ubicación 0.06; jurídico y documentos 0.05; completitud 0.10. Urgencia y necesidad de aliado pesan cero: informan prioridad temporal y acción, pero no inflan compatibilidad.

Umbrales: baja compatibilidad bajo 35, potencial desde 55 y revisar primero desde 75, con información mínima 45. Las reglas duras y la precedencia se aplican antes del orden de score. El `policy_hash` es SHA-256 del JSON canónico.
