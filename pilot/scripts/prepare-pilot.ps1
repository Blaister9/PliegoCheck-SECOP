# Prepara el dataset sintetico de piloto (usuarios, proceso, documentos, empresa, snapshot).
# Wrapper de: pnpm pilot:prepare. Solo entorno local.
param(
  [string]$Password = $env:PLIEGOCHECK_PILOT_PASSWORD
)
$ErrorActionPreference = "Stop"
if ($Password) {
  uv run pliegocheck-worker pilot-prepare --password $Password
} else {
  uv run pliegocheck-worker pilot-prepare
}
