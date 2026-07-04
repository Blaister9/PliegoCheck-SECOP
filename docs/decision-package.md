# Paquete de decision

El paquete de decision es el conjunto descargable de artefactos producidos para una decision
preliminar completada.

## Contenido

| Artefacto | Proposito |
| --- | --- |
| `executive-report.html` | Reporte visual para revision humana. |
| `executive-report.md` | Version portable en Markdown. |
| `decision-summary.json` | Snapshot estructurado del resultado, hallazgos, acciones y metadatos. |
| `requirement-evidence-matrix.csv` | Matriz requisito-evidencia-decision. |
| `pending-actions.csv` | Acciones abiertas, responsables, fechas y estado. |
| `risk-summary.csv` | Riesgos y hallazgos determinantes. |
| `package-manifest.json` | Manifest con digests SHA-256, versiones y artefactos. |
| `decision-package.zip` | ZIP plano con los artefactos descargables. |

## Manifest y digest

El manifest registra:

- version del motor de reporte;
- version y hash de templates;
- id del proceso, decision y paquete;
- input digest;
- package digest;
- artefactos fisicos con nombre, tipo, content type, tamano y SHA-256.

El ZIP se genera con entradas planas, sin directorios ni rutas absolutas. El digest del paquete se
calcula sobre los artefactos logicos previos al ZIP para evitar circularidad.

## Idempotencia

`POST /decision-reports` reutiliza un paquete `COMPLETED` o `COMPLETED_WITH_WARNINGS` cuando el
input digest coincide y `force=false`. Con `force=true` se crea una nueva ejecucion y un nuevo
paquete.

## Trazabilidad

Cada paquete conserva la relacion:

```text
Proceso -> DecisionRun -> input manifest -> DecisionReportJob -> DecisionReportPackage -> Artifact
```

La matriz CSV mantiene filas con requisito, estado, criticidad, fuente del hallazgo, evidencia,
reglas y accion asociada cuando exista.
