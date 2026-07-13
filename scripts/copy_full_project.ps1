# Copy the ENTIRE project folder (including .venv) — avoids Explorer path limits.
#
# Usage:
#   .\scripts\copy_full_project.ps1 -Destination "X:\b\cementnekosuljiceivkov"
#
# Tips:
#   - Use the SHORTEST destination path you can (e.g. X:\b\ivkov).
#   - Do not copy via Recycle Bin; use this script or Shift+Delete.
param(
    [Parameter(Mandatory = $true)]
    [string]$Destination
)

$ErrorActionPreference = "Stop"
$Source = Split-Path -Parent $PSScriptRoot
$Destination = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Destination)

function To-ExtendedPath([string]$Path) {
    if ($Path -match '^\\\\\?\\') {
        return $Path
    }
    if ($Path -match '^\\\\[^\\]') {
        return "\\?\UNC$($Path.Substring(1))"
    }
    return "\\?\$($Path.TrimEnd('\'))"
}

$src = To-ExtendedPath $Source
$dst = To-ExtendedPath $Destination

if (Test-Path -LiteralPath $Destination) {
    Write-Host "Destination already exists:"
    Write-Host "  $Destination"
    $answer = Read-Host "Merge/overwrite into it? (y/N)"
    if ($answer -notmatch '^[yY]') {
        exit 1
    }
} else {
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
}

Write-Host "Copying entire project (including .venv)..."
Write-Host "From: $Source"
Write-Host "To:   $Destination"
Write-Host ""

# /E = all subfolders, /COPYALL = data+attrs, /XJ = skip junctions that confuse copies
robocopy $src $dst /E /COPY:DAT /DCOPY:DAT /XJ /R:2 /W:2 /MT:8 /NFL /NDL /NJH /NJS /NP

# Robocopy: 0-7 = success with various meanings
if ($LASTEXITCODE -ge 8) {
    throw "Robocopy failed with exit code $LASTEXITCODE"
}

Write-Host ""
Write-Host "Full copy finished."
Write-Host "If it still fails, enable long paths in Windows and use a shorter destination, e.g. X:\b\ivkov"
