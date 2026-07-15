param(
  [Parameter(Mandatory = $true)][string]$Command,
  [Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments
)
$ErrorActionPreference = "Stop"
$envFile = $env:PLIEGOCHECK_RESTRICTED_ENV_FILE
if (-not $envFile) { throw "Define PLIEGOCHECK_RESTRICTED_ENV_FILE con la ruta externa de configuracion." }
& python (Join-Path $PSScriptRoot "controller.py") --env-file $envFile $Command @Arguments
exit $LASTEXITCODE
