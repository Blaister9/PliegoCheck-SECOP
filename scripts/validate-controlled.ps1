param(
  [switch]$SkipWeb,
  [string]$AdminEmail = "",
  [string]$AdminPassword = ""
)

$ErrorActionPreference = "Stop"
$summary = [ordered]@{}

function Assert-HttpOk([string]$Name, [string]$Url) {
  $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 10
  if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 300) {
    throw "$Name fallo con HTTP $($response.StatusCode)"
  }
  $summary[$Name] = "ok"
}

Assert-HttpOk "api_live" "http://localhost:8000/health/live"
Assert-HttpOk "api_ready" "http://localhost:8000/health/ready"
if (-not $SkipWeb) {
  Assert-HttpOk "web" "http://localhost:3000"
}

$worker = pnpm worker:health | Select-Object -Last 1 | ConvertFrom-Json
if ($worker.status -ne "ok") { throw "worker health no es ok" }
$summary["worker"] = "ok"

$dbCheck = pnpm db:check
$summary["database"] = "ok"

$storagePath = if ($env:PLIEGOCHECK_STORAGE_PATH) { $env:PLIEGOCHECK_STORAGE_PATH } else { "var/documents" }
New-Item -ItemType Directory -Path $storagePath -Force | Out-Null
$probe = Join-Path $storagePath ".controlled-probe"
"ok" | Set-Content -LiteralPath $probe -Encoding ascii
Remove-Item -LiteralPath $probe
$summary["storage"] = "ok"

if ($AdminEmail -and $AdminPassword) {
  $session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
  $login = Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:8000/auth/login" -Method Post -WebSession $session -ContentType "application/json" -Body (@{ email = $AdminEmail; password = $AdminPassword } | ConvertTo-Json)
  if ($login.StatusCode -ne 200) { throw "login admin fallo" }
  $me = Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:8000/auth/me" -WebSession $session -TimeoutSec 10
  if ($me.StatusCode -ne 200) { throw "auth/me admin fallo" }
  $summary["admin_login"] = "ok"
}

pnpm pilot:readiness | Out-Null
pnpm pilot:eval | Out-Null
pnpm deployment:backup-check | Out-Null
$summary["pilot_readiness"] = "ok"
$summary["pilot_eval"] = "ok"
$summary["backup_check"] = "ok"

$summary | ConvertTo-Json -Depth 4
