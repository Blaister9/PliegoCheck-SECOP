# Artefactos de reporte

Los artefactos de reporte son archivos generados por el worker de reportes a partir de datos ya
persistidos. No contienen secretos ni rutas fisicas internas.

## Reglas de seguridad

- HTML se genera con escape explicito de campos dinamicos.
- La previsualizacion web muestra texto plano; no usa `dangerouslySetInnerHTML`.
- Los nombres de archivo pertenecen a una lista controlada.
- El ZIP no permite rutas, `..`, unidades de Windows ni entradas absolutas.
- Cada archivo guarda SHA-256 y tamano.

## Storage local

En desarrollo se usa `PLIEGOCHECK_STORAGE_PATH` con prefijo `reports/`. El almacenamiento concreto
queda encapsulado por `ReportArtifactStorage` para permitir backend S3-compatible en una fase
operativa posterior.

## Templates

La version inicial vive en:

```text
config/report-templates/v1/
```

Los templates son de sustitucion simple `{{campo}}`; no ejecutan codigo ni expresiones.

## Evals

Los evals deterministas de `evals/decision-report` verifican:

- escape HTML y no invencion de `GO`;
- entradas ZIP seguras;
- estabilidad de digests y cambio cuando cambian acciones.
