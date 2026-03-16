$ErrorActionPreference = 'Stop'

$ApiPort = 8000
$UiPort = 4200

function Free-Port {
    param([int]$Port)
    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $connections) {
        Write-Host "No process found on port $Port."
        return
    }
    foreach ($conn in $connections) {
        $pid = $conn.OwningProcess
        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "Port $Port is in use by PID $pid ($($proc.ProcessName)) - stopping it..."
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 1
            Write-Host "Stopped process on port $Port."
        }
    }
}

Write-Host "Stopping API + UI..."
Free-Port -Port $ApiPort
Free-Port -Port $UiPort
Write-Host "Done."