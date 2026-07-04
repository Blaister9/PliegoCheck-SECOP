# Elimina UNICAMENTE datos de piloto. Requiere -Confirm explicito.
# Wrapper de: pnpm pilot:reset -- --confirm. No toca datos no sinteticos ni .env.
param(
  [switch]$Confirm
)
$ErrorActionPreference = "Stop"
if (-not $Confirm) {
  Write-Output '{"status":"aborted","reason":"reset requiere -Confirm para eliminar datos de piloto"}'
  exit 1
}
uv run pliegocheck-worker pilot-reset --confirm
