param(
  [string]$OutputDir = "var/backups"
)

$ErrorActionPreference = "Stop"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupRoot = Join-Path $OutputDir "pliegocheck-$timestamp"
New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null

$dbFile = Join-Path $backupRoot "database.dump"
$storageZip = Join-Path $backupRoot "storage.zip"
$manifestFile = Join-Path $backupRoot "manifest.json"

$databaseUrl = $env:DATABASE_URL
if (-not $databaseUrl) {
  $databaseUrl = "postgresql://pliegocheck:pliegocheck@localhost:56543/pliegocheck"
}
$storagePath = $env:PLIEGOCHECK_STORAGE_PATH
if (-not $storagePath) {
  $storagePath = "var/documents"
}

pg_dump --format=custom --file=$dbFile $databaseUrl
if (Test-Path $storagePath) {
  Compress-Archive -Path (Join-Path $storagePath "*") -DestinationPath $storageZip -Force
} else {
  New-Item -ItemType File -Path $storageZip -Force | Out-Null
}

$manifest = [ordered]@{
  created_at = (Get-Date).ToUniversalTime().ToString("o")
  database_dump = Split-Path $dbFile -Leaf
  database_sha256 = (Get-FileHash -Algorithm SHA256 $dbFile).Hash.ToLowerInvariant()
  storage_archive = Split-Path $storageZip -Leaf
  storage_sha256 = (Get-FileHash -Algorithm SHA256 $storageZip).Hash.ToLowerInvariant()
  excludes = @(".env", "secrets", "logs")
}
$manifest | ConvertTo-Json -Depth 4 | Set-Content -Path $manifestFile -Encoding UTF8
Write-Output $backupRoot
