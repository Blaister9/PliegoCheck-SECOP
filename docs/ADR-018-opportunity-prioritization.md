# ADR-018 — Priorización determinística de oportunidades

## Estado

Aceptado el 13 de julio de 2026.

## Decisión

La bandeja compara cada registro público SECOP con un `CompanyProfileSnapshot` publicado mediante un motor puro, una política JSON versionada y una fecha efectiva explícita en `America/Bogota`. Compatibilidad, urgencia y completitud son magnitudes independientes. El resultado orienta la revisión humana y no modifica el motor GO / NO GO.

Discovery y assessment se persisten como historial inmutable. Un digest incorpora snapshot, hash de política, identidad y hash del proceso, nivel y fecha efectiva. La cola PostgreSQL usa `FOR UPDATE SKIP LOCKED`; `force=true` conserva la versión anterior.

El nivel de metadatos no afirma cumplimiento. `UNKNOWN` aporta cero, la ausencia se registra como información faltante y los procesos cerrados o vencidos se descartan. El análisis profundo solo resume y reutiliza documentos, requisitos, evaluaciones y decisiones existentes.

## Consecuencias

- La política puede auditarse y reproducirse sin red, IA ni embeddings.
- Los outcomes son categorías de conveniencia para revisión, no decisiones de participación.
- El sistema no presenta ofertas ni ejecuta acciones transaccionales en SECOP.
- Monitoreo programado y alertas quedan fuera de esta decisión.
