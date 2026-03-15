$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$portalRoot = Join-Path $repoRoot 'Portals\infohub-app'

if (-not (Test-Path $portalRoot)) {
    throw "Angular portal not found at $portalRoot"
}

Set-Location $portalRoot

if (-not (Test-Path (Join-Path $portalRoot 'node_modules'))) {
    Write-Host 'Installing portal dependencies...'
    npm install
    if ($LASTEXITCODE -ne 0) {
        throw "npm install failed with exit code $LASTEXITCODE"
    }
}

Write-Host 'Starting Angular UI on http://0.0.0.0:4200'
npm run start -- --host 0.0.0.0 --port 4200
if ($LASTEXITCODE -ne 0) {
    throw "UI process failed with exit code $LASTEXITCODE"
}

