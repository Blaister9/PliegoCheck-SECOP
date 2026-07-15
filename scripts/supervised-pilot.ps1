param(
  [Parameter(Mandatory = $true)]
  [ValidateSet("deploy", "validate", "status", "stop", "reset", "report", "opportunity-worker-once")]
  [string]$Action,
  [string]$EnvFile = ".env.pilot",
  [switch]$Confirm,
  [switch]$SkipWeb
)
$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path ".").Path
$manifestPath = Join-Path $repoRoot "config/pilot/supervised-pilot-v1.json"
$stateDir = Join-Path $repoRoot "var/supervised-pilot"
function Read-Manifest {
  if (-not (Test-Path -LiteralPath $manifestPath)) { throw "Falta el manifiesto sanitizado del piloto." }
  $value = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
  if ($value.mode -ne "SUPERVISED_TECHNICAL_PILOT" -or -not $value.dry_run) { throw "Modo o dry-run inseguros." }
  if ($value.max_search_results -gt 100 -or $value.max_pages -gt 2 -or $value.max_imported_processes -gt 3 -or $value.max_document_downloads -gt 2 -or $value.max_monitors -gt 2 -or $value.max_alerts -gt 20) { throw "Los limites exceden el maximo permitido." }
  if ($value.start_conditions -notcontains "PUBLISHED_SNAPSHOT_REQUIRED") { throw "PUBLISHED_SNAPSHOT_REQUIRED es obligatorio." }
  return $value
}
function Get-Listener([int]$Port) { return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) }
function Get-PnpmExecutable {
  $names = if ($IsWindows -or $env:OS -eq "Windows_NT") { @("pnpm.cmd", "pnpm") } else { @("pnpm", "pnpm.cmd") }
  foreach ($name in $names) {
    $command = Get-Command $name -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
  }
  throw "No se encontro pnpm en PATH."
}
function Set-SafeOpportunityWorkerEnvironment {
  # El opt-in aplica al proceso worker; no se cambian defaults globales ni archivos .env.
  $env:PLIEGOCHECK_SECOP_ENABLED = "true"
  $env:PLIEGOCHECK_SECOP_DOCUMENT_DOWNLOAD_ENABLED = "false"
  $env:PLIEGOCHECK_EXTERNAL_DELIVERY_ENABLED = "false"
  $env:PLIEGOCHECK_NOTIFICATION_DRY_RUN = "true"
  $env:PLIEGOCHECK_EMAIL_ENABLED = "false"
  $env:PLIEGOCHECK_WEBHOOK_ENABLED = "false"
  $env:PLIEGOCHECK_SECOP_MAX_PAGE_SIZE = [string]$manifest.max_search_results
  $env:PLIEGOCHECK_OPPORTUNITIES_MAX_CANDIDATES = [string]$manifest.max_search_results
}
$manifest = Read-Manifest
switch ($Action) {
  "validate" {
    $required = @("docs/pilot-readiness-assessment.md", "docs/pilot-go-no-go.md", "pilot/user-validation/pilot-session-minutes.md")
    $missing = @($required | Where-Object { -not (Test-Path -LiteralPath (Join-Path $repoRoot $_)) })
    if ($missing.Count -gt 0) { throw "Faltan artefactos obligatorios: $($missing -join ', ')" }
    [ordered]@{ status = "VERIFIED"; pilot_id = $manifest.pilot_id; dry_run = $manifest.dry_run; snapshot_policy = "PUBLISHED_SNAPSHOT_REQUIRED"; api_listener = Get-Listener 8000; web_listener = Get-Listener 3000 } | ConvertTo-Json
  }
  "deploy" {
    & (Join-Path $repoRoot "scripts/deploy-controlled.ps1") -EnvFile $EnvFile -SkipWeb:$SkipWeb
    New-Item -ItemType Directory -Path $stateDir -Force | Out-Null
    [ordered]@{ pilot_id = $manifest.pilot_id; started_at = (Get-Date).ToUniversalTime().ToString("o"); mode = $manifest.mode; dry_run = $true } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $stateDir "state.json") -Encoding UTF8
  }
  "status" {
    [ordered]@{ pilot_id = $manifest.pilot_id; deployed_state_present = (Test-Path (Join-Path $stateDir "state.json")); api_listener = Get-Listener 8000; web_listener = Get-Listener 3000; dry_run = $true; report_directory = "var/pilot-reports/$($manifest.pilot_id)" } | ConvertTo-Json
  }
  "stop" { & (Join-Path $repoRoot "scripts/stop-controlled.ps1") }
  "reset" { if (-not $Confirm) { throw "Reset supervisado requiere -- --Confirm." }; & (Join-Path $repoRoot "scripts/reset-controlled.ps1") -Confirm }
  "opportunity-worker-once" {
    Set-SafeOpportunityWorkerEnvironment
    & (Get-PnpmExecutable) "opportunities:discovery-run-once"
    if ($LASTEXITCODE -ne 0) { throw "El worker de oportunidades termino con error." }
  }
  "report" {
    $output = Join-Path $repoRoot "var/pilot-reports/$($manifest.pilot_id)"
    New-Item -ItemType Directory -Path $output -Force | Out-Null
    $evidencePath = Join-Path $stateDir "evidence.json"
    $evidence = if (Test-Path -LiteralPath $evidencePath) { Get-Content -Raw -LiteralPath $evidencePath | ConvertFrom-Json } else { $null }
    $technicalValidation = if ($evidence) { $evidence.technical_validation } else { "EVIDENCE_REQUIRED" }
    $summary = [ordered]@{ pilot_id = $manifest.pilot_id; generated_at = (Get-Date).ToUniversalTime().ToString("o"); mode = $manifest.mode; technical_validation = $technicalValidation; user_validation = "USER_VALIDATION_PENDING"; external_delivery = "LOCAL_OR_DRY_RUN"; production_approval = $false }
    $metrics = if ($evidence) { $evidence.metrics } else { [ordered]@{ system = @{}; secop = @{}; opportunities = @{}; documents = @{}; monitoring = @{}; delivery = @{ dry_run = $true }; operations = @{} } }
    $validation = if ($evidence) { $evidence.validation } else { [ordered]@{ readiness = "SEE_VERSIONED_ASSESSMENT"; snapshot_policy = "PUBLISHED_SNAPSHOT_REQUIRED"; live_payloads_versioned = $false; human_feedback_claimed = $false } }
    $incidents = [ordered]@{ status = "SEE_VERSIONED_INCIDENT_LOG"; count = if ($evidence) { $evidence.incident_count } else { $null } }
    $summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $output "summary.json") -Encoding UTF8
    $metrics | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $output "metrics.json") -Encoding UTF8
    $validation | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $output "validation-results.json") -Encoding UTF8
    $incidents | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $output "incident-summary.json") -Encoding UTF8
    @("# Reporte local sanitizado", "", "- Piloto: $($manifest.pilot_id)", "- Validacion tecnica: $technicalValidation", "- Validacion humana: USER_VALIDATION_PENDING", "- Entrega externa: LOCAL_OR_DRY_RUN", "- Aprobacion de produccion: no") | Set-Content -LiteralPath (Join-Path $output "summary.md") -Encoding UTF8
    Write-Output $output
  }
}
