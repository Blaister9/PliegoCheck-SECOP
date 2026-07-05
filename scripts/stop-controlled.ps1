$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path ".").Path
$stateDir = Join-Path $repoRoot "var/controlled"

foreach ($name in @("web", "api")) {
  $pidFile = Join-Path $stateDir "$name.pid"
  if (Test-Path $pidFile) {
    $processId = [int](Get-Content -LiteralPath $pidFile)
    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
    if ($process) {
      Stop-Process -Id $processId -Force
      Wait-Process -Id $processId -Timeout 10 -ErrorAction SilentlyContinue
    }
    Remove-Item -LiteralPath $pidFile -Force
  }
}

foreach ($port in @(3000, 8000)) {
  $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  foreach ($connection in $connections) {
    $process = Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue
    if ($process) {
      Stop-Process -Id $connection.OwningProcess -Force
      Wait-Process -Id $connection.OwningProcess -Timeout 10 -ErrorAction SilentlyContinue
    }
  }
}

$previousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$dockerOutput = docker compose -f compose.pilot.yaml stop postgres controlled-storage 2>&1
$dockerExitCode = $LASTEXITCODE
$ErrorActionPreference = $previousErrorActionPreference
if ($dockerExitCode -ne 0) {
  Write-Output "Docker compose no disponible o servicios ya detenidos; se continua sin borrar datos."
} elseif ($dockerOutput) {
  $dockerOutput | Write-Output
}
Write-Output "Controlled pilot services stopped without deleting data."
