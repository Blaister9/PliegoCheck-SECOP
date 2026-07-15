param(
  [string]$EnvFile = ".env.pilot",
  [string]$AdminEmail = "",
  [string]$AdminDisplayName = "Controlled Pilot Admin",
  [switch]$CreateAdmin,
  [switch]$SkipWeb
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path ".").Path
$stateDir = Join-Path $repoRoot "var/controlled"
$logDir = Join-Path $stateDir "logs"
New-Item -ItemType Directory -Path $stateDir -Force | Out-Null
New-Item -ItemType Directory -Path $logDir -Force | Out-Null

function Load-EnvFile([string]$Path) {
  if (-not (Test-Path $Path)) {
    throw "No existe $Path. Copia .env.pilot.example a .env.pilot y reemplaza los CHANGEME fuera del repositorio."
  }
  foreach ($line in Get-Content -LiteralPath $Path) {
    $trimmed = $line.Trim()
    if (-not $trimmed -or $trimmed.StartsWith("#")) { continue }
    $parts = $trimmed.Split("=", 2)
    if ($parts.Count -ne 2) { continue }
    [Environment]::SetEnvironmentVariable($parts[0], $parts[1], "Process")
  }
}

function Assert-No-Placeholder([string]$Name) {
  $value = [Environment]::GetEnvironmentVariable($Name, "Process")
  if (-not $value) { throw "$Name es obligatorio para despliegue controlado." }
  if ($value -like "*CHANGEME*") { throw "$Name contiene CHANGEME; usa un valor sintetico local no versionado." }
}

function Wait-HttpOk([string]$Url, [int]$Seconds = 60) {
  $deadline = (Get-Date).AddSeconds($Seconds)
  while ((Get-Date) -lt $deadline) {
    try {
      $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 5
      if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) { return }
    } catch {
      Start-Sleep -Seconds 2
    }
  }
  throw "Timeout esperando $Url"
}

Load-EnvFile $EnvFile
Assert-No-Placeholder "DATABASE_URL"
Assert-No-Placeholder "PLIEGOCHECK_AUTH_SECRET_KEY"

if ($env:PLIEGOCHECK_PILOT_MODE -ne "true") { throw "PLIEGOCHECK_PILOT_MODE debe ser true." }
if ($env:PLIEGOCHECK_AUTH_ENABLED -ne "true") { throw "PLIEGOCHECK_AUTH_ENABLED debe ser true." }
if ($env:PLIEGOCHECK_CORS_ALLOWED_ORIGINS -eq "*") { throw "CORS no puede usar wildcard." }

docker compose -f compose.pilot.yaml up -d postgres controlled-storage
pnpm db:migrate
pnpm db:check

if ($CreateAdmin) {
  if (-not $AdminEmail) { throw "Use -AdminEmail para crear admin." }
  if (-not $env:PLIEGOCHECK_CONTROLLED_ADMIN_PASSWORD) {
    throw "PLIEGOCHECK_CONTROLLED_ADMIN_PASSWORD es obligatorio para -CreateAdmin."
  }
  $env:PLIEGOCHECK_CONTROLLED_ADMIN_PASSWORD | pnpm auth:create-admin -- --email $AdminEmail --display-name $AdminDisplayName --password-stdin
}

pnpm pilot:prepare

$apiLog = Join-Path $logDir "api.log"
$apiErr = Join-Path $logDir "api.err.log"
$apiProcess = Start-Process -FilePath "uv" -ArgumentList @("run", "uvicorn", "pliegocheck_api.main:app", "--port", "8000") -WorkingDirectory $repoRoot -RedirectStandardOutput $apiLog -RedirectStandardError $apiErr -PassThru -WindowStyle Hidden
$apiProcess.Id | Set-Content -LiteralPath (Join-Path $stateDir "api.pid") -Encoding ascii
Wait-HttpOk "http://localhost:8000/health/live" 60
Wait-HttpOk "http://localhost:8000/health/ready" 60

if (-not $SkipWeb) {
  $webLog = Join-Path $logDir "web.log"
  $webErr = Join-Path $logDir "web.err.log"
  $pnpmExecutable = (Get-Command pnpm.cmd -ErrorAction SilentlyContinue).Source
  if (-not $pnpmExecutable) { $pnpmExecutable = (Get-Command pnpm -ErrorAction Stop).Source }
  $webProcess = Start-Process -FilePath $pnpmExecutable -ArgumentList @("--filter", "@pliegocheck/web", "dev", "--hostname", "127.0.0.1", "--port", "3000") -WorkingDirectory $repoRoot -RedirectStandardOutput $webLog -RedirectStandardError $webErr -PassThru -WindowStyle Hidden
  $webProcess.Id | Set-Content -LiteralPath (Join-Path $stateDir "web.pid") -Encoding ascii
  Wait-HttpOk "http://localhost:3000" 90
}

pnpm controlled:validate
Write-Output "Controlled pilot environment ready."
Write-Output "API: http://localhost:8000"
Write-Output "Web: http://localhost:3000"
Write-Output "Next: complete pilot/user-validation/session-plan.md and capture feedback."
