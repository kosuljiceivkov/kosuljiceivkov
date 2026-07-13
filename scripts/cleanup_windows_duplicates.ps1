# Removes accidental Windows duplicate files like "models (1).py" or "__init__ (1).cpython-313.pyc"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$dupes = Get-ChildItem -Path $ProjectRoot -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match ' \(\d+\)\.' }

if (-not $dupes.Count) {
    Write-Host "No Windows duplicate filenames found."
    exit 0
}

Write-Host "Removing $($dupes.Count) duplicate files..."
$dupes | Remove-Item -Force -ErrorAction SilentlyContinue

$max = (Get-ChildItem -Path $ProjectRoot -Recurse -ErrorAction SilentlyContinue |
    ForEach-Object { $_.FullName.Length } |
    Measure-Object -Maximum).Maximum

Write-Host "Done. Longest path is now $max characters."
