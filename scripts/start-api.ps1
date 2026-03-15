$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$ApiPort = 8000

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

Free-Port -Port $ApiPort

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
Write-Host "Starting FastAPI backend on http://0.0.0.0:$ApiPort"

& $uvBin run --active python -m uvicorn app.Api.api_app:app --host 0.0.0.0 --port $ApiPort --reload
if ($LASTEXITCODE -ne 0) {
    throw "API process failed with exit code $LASTEXITCODE"
}
