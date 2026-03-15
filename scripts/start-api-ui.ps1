$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$apiScript = Join-Path $PSScriptRoot 'start-api.ps1'
$uiScript = Join-Path $PSScriptRoot 'start-ui.ps1'
$ApiPort = 8000
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

Free-Port -Port $ApiPort
Free-Port -Port $UiPort

$apiProc = $null
$uiProc = $null

try {
    Set-Location $repoRoot

    $apiProc = Start-Process -FilePath 'powershell' -ArgumentList @(
        '-NoProfile',
        '-ExecutionPolicy',
        'Bypass',
        '-File',
        $apiScript
    ) -PassThru
    Write-Host "Started API with PID $($apiProc.Id)"

    $uiProc = Start-Process -FilePath 'powershell' -ArgumentList @(
        '-NoProfile',
        '-ExecutionPolicy',
        'Bypass',
        '-File',
        $uiScript
    ) -PassThru
    Write-Host "Started UI with PID $($uiProc.Id)"

    Wait-Process -Id $apiProc.Id, $uiProc.Id
}
finally {
    foreach ($proc in @($apiProc, $uiProc)) {
        if ($null -ne $proc) {
            try {
                if (-not $proc.HasExited) {
                    Stop-Process -Id $proc.Id -Force
                }
            }
            catch {
                Write-Warning "Failed to stop PID $($proc.Id): $($_.Exception.Message)"
            }
        }
    }
}
