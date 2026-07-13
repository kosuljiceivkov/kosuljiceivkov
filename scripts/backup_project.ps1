# Backup project source — skips regenerable folders to avoid Windows long-path errors.
# Usage:
#   .\scripts\backup_project.ps1 -Destination "D:\Backup\cementnekosuljiceivkov"
param(
    [Parameter(Mandatory = $true)]
    [string]$Destination
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Destination = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Destination)

if (-not (Test-Path $Destination)) {
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
}

Write-Host "Backing up from:"
Write-Host "  $ProjectRoot"
Write-Host "To:"
Write-Host "  $Destination"
Write-Host ""
Write-Host "Skipping: .venv, node_modules, __pycache__, staticfiles, media, test_media, .git"
Write-Host ""

$excludeDirs = @(
    ".venv",
    "venv",
    "env",
    ".git",
    "node_modules",
    "__pycache__",
    "staticfiles",
    "media",
    "test_media",
    "htmlcov",
    ".pytest_cache"
)

$excludeArgs = $excludeDirs | ForEach-Object { "/XD"; $_ }

robocopy $ProjectRoot $Destination /E /Z /FFT /R:2 /W:2 /NFL /NDL /NJH /NJS /NP @excludeArgs /XF "db.sqlite3" "db (1).sqlite3"

if ($LASTEXITCODE -ge 8) {
    throw "Robocopy failed with exit code $LASTEXITCODE"
}

Write-Host ""
Write-Host "Backup finished."
Write-Host "Restore dev environment in the copy with:"
Write-Host "  python -m venv .venv"
Write-Host "  .\.venv\Scripts\pip install -r requirements.txt"
