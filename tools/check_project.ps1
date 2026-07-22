[CmdletBinding()]
param(
    [ValidateSet("quick", "full")]
    [string]$Profile = "quick",
    [string]$Python = "python",
    [string]$TypeScriptVersion = "6.0.3",
    [string]$RuffVersion = "0.15.22"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$originalLocation = (Get-Location).Path
$pythonCommand = if (Test-Path -LiteralPath $Python) {
    (Resolve-Path -LiteralPath $Python -ErrorAction Stop).ProviderPath
} else {
    (Get-Command $Python -ErrorAction Stop).Source
}

try {
    Set-Location -LiteralPath $repoRoot

    Write-Host "== EasyUse Anima project check =="
    Write-Host "Profile: $Profile"
    Write-Host "Python:  $pythonCommand"

    Write-Host "`n== Python compile =="
    & $pythonCommand -m compileall -q .
    if ($LASTEXITCODE -ne 0) {
        throw "Python compile failed with exit code $LASTEXITCODE."
    }

    Write-Host "`n== Python quality report =="
    & (Join-Path $PSScriptRoot "check_python_quality.ps1") -RuffVersion $RuffVersion

    if ($Profile -eq "full") {
        Write-Host "`n== Python unittest =="
        & $pythonCommand -m unittest discover -s tests
        if ($LASTEXITCODE -ne 0) {
            throw "Python unittest failed with exit code $LASTEXITCODE."
        }
    }

    Write-Host "`n== Frontend =="
    & (Join-Path $PSScriptRoot "check_frontend.ps1") -TypeScriptVersion $TypeScriptVersion

    Write-Host "`n== Git diff check =="
    & git diff --check
    if ($LASTEXITCODE -ne 0) {
        throw "Working-tree diff check failed with exit code $LASTEXITCODE."
    }
    & git diff --cached --check
    if ($LASTEXITCODE -ne 0) {
        throw "Staged diff check failed with exit code $LASTEXITCODE."
    }

    Write-Host "`nProject checks passed ($Profile)."
}
finally {
    Set-Location -LiteralPath $originalLocation
}
