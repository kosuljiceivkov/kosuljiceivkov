# Deploy: commit + push na GitHub (Render automatski gradi sa main grane).
# Upotreba: .\scripts\deploy.ps1
#           .\scripts\deploy.ps1 -Message "SEO i OG preview ispravke"

param(
    [string]$Message = "update"
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

function Invoke-Git {
    param([string[]]$Args)
    & git @Args
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Args -join ' ') failed (exit $LASTEXITCODE)"
    }
}

Write-Host ">> git add -A"
Invoke-Git @("add", "-A")

$pending = & git status --porcelain
if ($pending) {
    Write-Host ">> git commit -m `"$Message`""
    Invoke-Git @("commit", "-m", $Message)
} else {
    Write-Host "Nema novih izmena za commit."
}

$maxAttempts = 3
for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
    Write-Host ">> git push (pokusaj $attempt/$maxAttempts)"
    & git push
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "OK: Poslato na GitHub. Render ce pokrenuti deploy sa main grane."
        exit 0
    }

    if ($attempt -lt $maxAttempts) {
        Write-Host "Push nije uspeo (cesto zbog USB diska ili zakljucanog .git fajla). Cekam 4s..."
        Start-Sleep -Seconds 4
    }
}

Write-Host ""
Write-Host "Push i dalje ne uspeva. Probaj:"
Write-Host "  1. Zatvori druge Git terminale i sačekaj par sekundi"
Write-Host "  2. Ponovo: .\scripts\deploy.ps1"
Write-Host "  3. Ako se ponavlja: iskljuci antivirus za ovaj folder ili radi git push sa lokalnog C: diska"
exit 1
