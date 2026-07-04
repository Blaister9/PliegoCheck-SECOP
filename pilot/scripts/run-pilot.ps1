# Ejecuta el flujo end-to-end del piloto y devuelve un resumen JSON.
# Wrapper de: pnpm pilot:run. Requiere prepare previo.
param(
  [string]$Password = $env:PLIEGOCHECK_PILOT_PASSWORD
)
$ErrorActionPreference = "Stop"
if ($Password) {
  uv run pliegocheck-worker pilot-run --password $Password
} else {
  uv run pliegocheck-worker pilot-run
}
