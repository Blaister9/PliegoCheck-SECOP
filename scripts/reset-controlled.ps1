param(
  [switch]$Confirm
)

$ErrorActionPreference = "Stop"
if (-not $Confirm) {
  throw "Reset controlado requiere -Confirm. Solo borra datos sinteticos/volumenes del entorno controlado."
}

$repoRoot = (Resolve-Path ".").Path
pnpm controlled:stop
pnpm pilot:reset --confirm
$previousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$dockerOutput = docker compose -f compose.pilot.yaml down -v 2>&1
$dockerExitCode = $LASTEXITCODE
$ErrorActionPreference = $previousErrorActionPreference
if ($dockerExitCode -ne 0) {
  Write-Output "Docker compose no disponible o volumenes ya eliminados; se continua."
} elseif ($dockerOutput) {
  $dockerOutput | Write-Output
}

$controlledVar = Join-Path $repoRoot "var/controlled"
if (Test-Path $controlledVar) {
  Start-Sleep -Seconds 2
  try {
    Remove-Item -LiteralPath $controlledVar -Recurse -Force
  } catch {
    Start-Sleep -Seconds 3
    Remove-Item -LiteralPath $controlledVar -Recurse -Force
  }
}

Write-Output "Controlled pilot environment reset completed."
