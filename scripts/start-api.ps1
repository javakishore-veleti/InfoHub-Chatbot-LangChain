$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

function Resolve-UvCommand {
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if ($uv) {
        return $uv.Source
    }

    $candidates = @(
        (Join-Path $HOME '.local\bin\uv.exe'),
        (Join-Path $HOME '.cargo\bin\uv.exe')
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw "uv executable not found. Install uv or add it to PATH."
}

$uvBin = Resolve-UvCommand
Write-Host "Using uv: $uvBin"
Write-Host 'Starting FastAPI backend on http://0.0.0.0:8000'

& $uvBin run --active python -m uvicorn app.Api.api_app:app --host 0.0.0.0 --port 8000 --reload
if ($LASTEXITCODE -ne 0) {
    throw "API process failed with exit code $LASTEXITCODE"
}

