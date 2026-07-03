# ADR-005 - Perfil de empresa, evidencias y snapshots

- **Estado:** Aceptado
- **Fecha:** 2026-07-02
- **Decisores:** Equipo PliegoCheck

## Contexto

Microfase 5 necesita capturar datos empresariales reutilizables antes de evaluar requisitos de un
proceso. Esos datos pueden ser juridicos, financieros, de experiencia, personal, certificaciones o
capacidades. Ningun dato debe convertirse en cumplimiento sin evidencia verificable.

## Decision

Se implementa un perfil editable (`CompanyProfile`) con subentidades tipadas y evidencias
documentales propias:

- `CompanyEvidenceDocument` almacena soportes empresariales con SHA-256 y reutiliza el pipeline de
  documentos existente mediante un `Process` tecnico oculto.
- `CompanyEvidenceLink` vincula un dato de empresa con documento, extraccion, segmento, cita y
  ubicacion.
- `CompanyProfileCompleteness` calcula faltantes y cobertura de evidencias sin producir decisiones
  GO / NO GO.
- `CompanyProfileSnapshot` captura una version canonica e inmutable del perfil, con digest SHA-256.

## Consecuencias

- Los evaluadores futuros pueden operar contra snapshots estables, no contra datos editables.
- La extraccion documental no se duplica para soportes empresariales.
- La UI muestra completitud y advertencias, pero no afirma cumplimiento de procesos.
- Identificadores tributarios y personales se normalizan para unicidad y se enmascaran al mostrar.

## Fuera de alcance

- Evaluar si la empresa cumple un requisito concreto.
- Inferir datos financieros o juridicos con IA.
- Autenticacion multiempresa y permisos granulares por usuario.
