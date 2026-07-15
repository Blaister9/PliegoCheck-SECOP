& (Join-Path $PSScriptRoot "invoke.ps1") restore-verify @args
exit $LASTEXITCODE
