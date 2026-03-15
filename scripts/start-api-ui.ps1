$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$apiScript = Join-Path $PSScriptRoot 'start-api.ps1'
$uiScript = Join-Path $PSScriptRoot 'start-ui.ps1'

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

