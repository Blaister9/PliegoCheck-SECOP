# Formulas financieras

Las formulas de Microfase 6 son deterministicas, versionadas como `1.0.0` y se aplican sin redondear
para comparar. El valor redondeado se persiste como evidencia de calculo.

| Metrica resultante | Formula | Unidad |
| --- | --- | --- |
| `WORKING_CAPITAL` | `CURRENT_ASSETS - CURRENT_LIABILITIES` | moneda del periodo, normalmente `COP` |
| `LIQUIDITY_RATIO` | `CURRENT_ASSETS / CURRENT_LIABILITIES` | `ratio` |
| `DEBT_RATIO` | `TOTAL_LIABILITIES / TOTAL_ASSETS` | `ratio` |
| `INTEREST_COVERAGE` | `OPERATING_PROFIT / INTEREST_EXPENSE` | `ratio` |
| `RETURN_ON_ASSETS` | `NET_PROFIT / TOTAL_ASSETS` | `ratio` |
| `RETURN_ON_EQUITY` | `NET_PROFIT / EQUITY` | `ratio` |

## Reglas de calculo

- Division por cero produce `UNKNOWN` con codigo `DIVISION_BY_ZERO`.
- Insumos faltantes producen `UNKNOWN` con codigo `METRIC_MISSING`.
- Insumos conflictivos producen `CONFLICTING_EVIDENCE`.
- Desajuste de unidad o moneda produce `UNKNOWN`.
- Los porcentajes expresados como `70%` se normalizan a `0.70` cuando el requisito se evalua como
  ratio.

## Versionamiento

La tabla `financial_formula_versions` registra nombre, version semantica, expresion, insumos,
metrica resultante, unidad y politica de redondeo. Cambios futuros de formula deben crear una nueva
version; no deben reescribir resultados historicos.
