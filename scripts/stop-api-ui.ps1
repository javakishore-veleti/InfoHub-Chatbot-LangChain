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
    $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($pid in $pids) {
        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "Port $Port — killing PID $pid ($($proc.ProcessName)) with process tree..."
            # /T kills the entire process tree
            & taskkill /PID $pid /T /F 2>$null
        }
    }

    # Wait for port to be released.
    $retries = 5
    while ($retries -gt 0) {
        Start-Sleep -Seconds 1
        $remaining = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        if (-not $remaining) { break }
        Write-Host "Port $Port still in use — retrying ($retries)..."
        $remaining | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object {
            & taskkill /PID $_ /T /F 2>$null
        }
        $retries--
    }
    Write-Host "Stopped all processes on port $Port."
}

Write-Host "Stopping API + UI..."
Free-Port -Port $ApiPort
Free-Port -Port $UiPort
Write-Host "Done."
