param(
  [Parameter(Mandatory = $true)][string]$BackupDir,
  [switch]$Yes
)

$ErrorActionPreference = "Stop"
if (-not $Yes) {
  throw "Restore es destructivo. Reejecuta con -Yes despues de verificar el backup."
}

$dbFile = Join-Path $BackupDir "database.dump"
$storageZip = Join-Path $BackupDir "storage.zip"
if (-not (Test-Path $dbFile)) {
  throw "No existe database.dump en $BackupDir"
}

$databaseUrl = $env:DATABASE_URL
if (-not $databaseUrl) {
  $databaseUrl = "postgresql://pliegocheck:pliegocheck@localhost:56543/pliegocheck"
}
$storagePath = $env:PLIEGOCHECK_STORAGE_PATH
if (-not $storagePath) {
  $storagePath = "var/documents"
}
$repoRoot = (Resolve-Path ".").Path
$safeStorageRoot = [System.IO.Path]::GetFullPath((Join-Path $repoRoot "var"))
$resolvedStoragePath = [System.IO.Path]::GetFullPath($storagePath)
if (-not $resolvedStoragePath.StartsWith($safeStorageRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
  throw "Restore local solo puede reemplazar almacenamiento dentro de $safeStorageRoot. Ruta recibida: $resolvedStoragePath"
}

pg_restore --clean --if-exists --no-owner --dbname=$databaseUrl $dbFile
if (Test-Path $storageZip) {
  if (Test-Path $resolvedStoragePath) {
    Remove-Item -LiteralPath $resolvedStoragePath -Recurse -Force
  }
  New-Item -ItemType Directory -Path $resolvedStoragePath -Force | Out-Null
  Expand-Archive -Path $storageZip -DestinationPath $resolvedStoragePath -Force
}
Write-Output "restore completed"
