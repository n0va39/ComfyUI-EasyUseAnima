[CmdletBinding()]
param(
    [string]$TypeScriptVersion = "6.0.3"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$originalLocation = (Get-Location).Path

try {
    Set-Location -LiteralPath $repoRoot
    Get-Command node -ErrorAction Stop | Out-Null
    Get-Command npx -ErrorAction Stop | Out-Null

    $jsFiles = @(
        Get-ChildItem -File -Recurse -Path "web\js" -Filter "*.js" |
            Sort-Object FullName
    )
    if ($jsFiles.Count -eq 0) {
        throw "No frontend JavaScript files were found under web\js."
    }

    foreach ($file in $jsFiles) {
        & node --check $file.FullName
        if ($LASTEXITCODE -ne 0) {
            throw "JavaScript syntax check failed: $($file.FullName)"
        }
    }

    & node "tests\frontend_highlight_core_smoke.mjs"
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend highlight core smoke failed with exit code $LASTEXITCODE."
    }

    & node "tests\frontend_highlight_overlay_core_smoke.mjs"
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend highlight overlay core smoke failed with exit code $LASTEXITCODE."
    }

    & node "tests\frontend_aio_profile_core_smoke.mjs"
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend AiO profile core smoke failed with exit code $LASTEXITCODE."
    }

    & node "tests\frontend_aio_dependency_core_smoke.mjs"
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend AiO dependency core smoke failed with exit code $LASTEXITCODE."
    }

    & node "tests\frontend_aio_preview_core_smoke.mjs"
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend AiO preview core smoke failed with exit code $LASTEXITCODE."
    }

    & node "tests\frontend_aio_settings_core_smoke.mjs"
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend AiO settings core smoke failed with exit code $LASTEXITCODE."
    }

    & node "tests\frontend_aio_dom_controls_core_smoke.mjs"
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend AiO DOM controls core smoke failed with exit code $LASTEXITCODE."
    }

    & node "tests\frontend_aio_dialog_primitives_smoke.mjs"
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend AiO dialog primitives smoke failed with exit code $LASTEXITCODE."
    }

    & node "tests\frontend_aio_input_settings_dialog_smoke.mjs"
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend AiO Input Settings dialog smoke failed with exit code $LASTEXITCODE."
    }

    & node "tests\frontend_aio_postprocess_settings_dialog_smoke.mjs"
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend AiO Postprocess Settings dialog smoke failed with exit code $LASTEXITCODE."
    }

    & node "tests\frontend_regional_pure_data_smoke.mjs"
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend Regional pure data smoke failed with exit code $LASTEXITCODE."
    }

    & node "tests\frontend_regional_runtime_smoke.mjs"
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend Regional runtime lifecycle smoke failed with exit code $LASTEXITCODE."
    }

    & node "tests\frontend_lora_preset_profile_data_smoke.mjs"
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend LoRA preset profile data smoke failed with exit code $LASTEXITCODE."
    }

    & npx --yes --package "typescript@$TypeScriptVersion" -- tsc -p jsconfig.json
    if ($LASTEXITCODE -ne 0) {
        throw "TypeScript check failed with exit code $LASTEXITCODE."
    }

    Write-Host "Frontend checks passed: $($jsFiles.Count) JavaScript files, TypeScript $TypeScriptVersion."
}
finally {
    Set-Location -LiteralPath $originalLocation
}
