[CmdletBinding()]
param(
    [string]$RuffVersion = "0.15.22",
    [string]$PyrightVersion = "1.1.411",
    [string]$Python = "python",
    [string]$Uv = "uvx",
    [string]$Npm = "npm",
    [switch]$Offline
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$originalLocation = (Get-Location).Path
$uvCommand = if (Test-Path -LiteralPath $Uv) {
    (Resolve-Path -LiteralPath $Uv -ErrorAction Stop).ProviderPath
} else {
    (Get-Command $Uv -ErrorAction Stop).Source
}
$npmCommand = if (Test-Path -LiteralPath $Npm) {
    (Resolve-Path -LiteralPath $Npm -ErrorAction Stop).ProviderPath
} else {
    (Get-Command $Npm -ErrorAction Stop).Source
}
$pythonCommand = if (Test-Path -LiteralPath $Python) {
    (Resolve-Path -LiteralPath $Python -ErrorAction Stop).ProviderPath
} else {
    (Get-Command $Python -ErrorAction Stop).Source
}

try {
    Set-Location -LiteralPath $repoRoot

    Write-Host "== Python quality report (G-01, report-only) =="
    Write-Host "Ruff: $RuffVersion"

    $ruffArgs = @()
    if ($Offline) {
        $ruffArgs += "--offline"
    }
    $ruffArgs += @(
        "ruff@$RuffVersion"
        "check"
        "--exit-zero"
        "--no-cache"
        "--output-format"
        "concise"
        "."
    )
    & $uvCommand @ruffArgs
    $ruffExitCode = $LASTEXITCODE
    if ($ruffExitCode -ne 0) {
        throw "Ruff report execution failed with exit code $ruffExitCode."
    }

    Write-Host "Ruff report completed. Findings are non-blocking during G-01; execution and configuration failures remain blocking."

    Write-Host "`n== Pyright baseline ratchet (G-02a) =="
    Write-Host "Pyright: $PyrightVersion"

    $pyrightCacheArg = if ($Offline) { "--offline" } else { "--prefer-offline" }
    $pyrightArgs = @(
        "exec"
        "--yes"
        $pyrightCacheArg
        "--package"
        "pyright@$PyrightVersion"
        "--"
        "pyright"
        "--outputjson"
        "--project"
        "pyrightconfig.json"
    )
    $pyrightOutput = @(& $npmCommand @pyrightArgs)
    $pyrightExitCode = $LASTEXITCODE
    if ($pyrightExitCode -notin @(0, 1)) {
        throw "Pyright execution failed with exit code $pyrightExitCode."
    }
    if ($pyrightOutput.Count -eq 0) {
        throw "Pyright produced no JSON report."
    }

    $pyrightOutput |
        & $pythonCommand (Join-Path $PSScriptRoot "check_pyright_baseline.py")
    $baselineExitCode = $LASTEXITCODE
    if ($baselineExitCode -ne 0) {
        throw "Pyright baseline ratchet failed with exit code $baselineExitCode."
    }

    Write-Host "`n== Python import boundary gate (G-03a) =="
    & $pythonCommand (Join-Path $PSScriptRoot "check_python_import_boundaries.py")
    $importBoundaryExitCode = $LASTEXITCODE
    if ($importBoundaryExitCode -ne 0) {
        throw "Python import boundary gate failed with exit code $importBoundaryExitCode."
    }

    Write-Host "`n== Python size/complexity ratchet (G-05A) =="
    & $pythonCommand (Join-Path $PSScriptRoot "check_python_size_complexity.py")
    $sizeComplexityExitCode = $LASTEXITCODE
    if ($sizeComplexityExitCode -ne 0) {
        throw "Python size/complexity ratchet failed with exit code $sizeComplexityExitCode."
    }

    Write-Host "`n== Python file-disposition contract (PTC-01) =="
    & $pythonCommand (Join-Path $PSScriptRoot "check_python_file_dispositions.py")
    $fileDispositionExitCode = $LASTEXITCODE
    if ($fileDispositionExitCode -ne 0) {
        throw "Python file-disposition contract failed with exit code $fileDispositionExitCode."
    }
}
finally {
    Set-Location -LiteralPath $originalLocation
}
