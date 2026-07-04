# Resultados de decision

La decision es preliminar, generada por reglas deterministicas y requiere revision humana. No
constituye concepto juridico ni garantiza habilitacion o adjudicacion.

| Resultado | Significado |
| --- | --- |
| `GO` | Cobertura obligatoria completa y todos los requisitos obligatorios aplicables cumplen. |
| `GO_CONDICIONADO` | Hay brechas remediables explicitas con condiciones concretas y acciones. |
| `BUSCAR_ALIADO` | Hay brecha obligatoria explicitamente marcada como resoluble mediante aliado. |
| `NO_GO` | Hay incumplimiento obligatorio bloqueante o no subsanable confirmado. |
| `NO_CARGAR` | Hay bloqueo explicito para presentar la oferta (`submission_blocker=true`). |
| `PENDIENTE_INFORMACION` | Falta informacion, evaluacion, cobertura, revision humana o hay conflicto. |

La ausencia de evaluacion en una dimension nunca se interpreta como cumplimiento. En Microfase 7 el
unico adaptador especializado disponible es `FINANCIAL`; los demas requisitos obligatorios quedan
`NOT_EVALUATED` y bloquean `GO`.
