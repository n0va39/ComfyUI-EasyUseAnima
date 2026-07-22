[CmdletBinding()]
param(
    [string]$RuffVersion = "0.15.22",
    [string]$Uv = "uvx"
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

try {
    Set-Location -LiteralPath $repoRoot

    Write-Host "== Python quality report (G-01, report-only) =="
    Write-Host "Ruff: $RuffVersion"

    $ruffArgs = @(
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
}
finally {
    Set-Location -LiteralPath $originalLocation
}
