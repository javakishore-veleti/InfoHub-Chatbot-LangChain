$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$portalRoot = Join-Path $repoRoot 'Portals\infohub-app'
$UiPort = 4200

function Free-Port {
    param([int]$Port)
    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    foreach ($conn in $connections) {
        $pid = $conn.OwningProcess
        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "Port $Port is in use by PID $pid ($($proc.ProcessName)) - stopping it..."
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 1
        }
    }
}

Free-Port -Port $UiPort

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

Write-Host "Starting Angular UI on http://0.0.0.0:$UiPort"
npm run start -- --host 0.0.0.0 --port $UiPort
if ($LASTEXITCODE -ne 0) {
    throw "UI process failed with exit code $LASTEXITCODE"
}
