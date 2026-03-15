param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('setup', 'sync', 'status', 'destroy', 'python-version', 'deps-check', 'activate', 'deactivate')]
    [string]$Action
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$projectName = Split-Path -Leaf $repoRoot

if ($env:INFOHUB_VENV_PATH) {
    $venvPath = $env:INFOHUB_VENV_PATH
} elseif ($env:VIRTUAL_ENV) {
    $venvPath = $env:VIRTUAL_ENV
} else {
    $venvPath = Join-Path $repoRoot '.venv'
}

# Ensure uv targets one consistent environment path for all commands.
$env:UV_PROJECT_ENVIRONMENT = $venvPath

function Invoke-Uv {
    param([string[]]$UvArgs)
    & uv @UvArgs
    if ($LASTEXITCODE -ne 0) {
        throw "uv command failed: uv $($UvArgs -join ' ')"
    }
}

function Get-VenvPythonPath {
    return Join-Path $venvPath 'Scripts\python.exe'
}

function Get-VenvActivatePath {
    return Join-Path $venvPath 'Scripts\Activate.ps1'
}

Write-Host "Project root: $repoRoot"
Write-Host "Project name: $projectName"
Write-Host "Virtual env: $venvPath"

switch ($Action) {
    'setup' {
        Invoke-Uv -UvArgs @('python', 'pin', '3.11')
        if (-not (Test-Path $venvPath)) {
            Invoke-Uv -UvArgs @('venv', '--python', '3.11', $venvPath)
        } else {
            Write-Host 'Environment already exists. Skipping venv creation.'
        }
        Invoke-Uv -UvArgs @('sync')
        Write-Host 'Local environment setup complete.'
    }
    'sync' {
        Invoke-Uv -UvArgs @('sync')
        Write-Host 'Dependencies synced.'
    }
    'status' {
        $pythonExe = Get-VenvPythonPath
        if (Test-Path $pythonExe) {
            Write-Host 'Environment exists: yes'
            & $pythonExe --version
        } else {
            Write-Host 'Environment exists: no'
            Write-Host 'Run npm run setup:local:venv:setup'
        }

        Invoke-Uv -UvArgs @('tree', '--depth', '1')
    }
    'activate' {
        $activateScript = Get-VenvActivatePath
        if (-not (Test-Path $activateScript)) {
            Write-Host 'Environment does not exist yet.'
            Write-Host 'Run npm run setup:local:venv:setup'
            exit 1
        }

        Write-Host 'Activation cannot persist when run via npm child process.'
        Write-Host 'Run this command in your current shell:'
        Write-Host "& '$activateScript'"
    }
    'deactivate' {
        Write-Host 'Deactivation must be run in the currently activated shell.'
        Write-Host 'In that shell, run: deactivate'
    }
    'destroy' {
        if (Test-Path $venvPath) {
            Remove-Item -LiteralPath $venvPath -Recurse -Force
            Write-Host 'Environment deleted.'
        } else {
            Write-Host 'Environment not found. Nothing to delete.'
        }
    }
    'python-version' {
        Invoke-Uv -UvArgs @('run', '--', 'python', '--version')
    }
    'deps-check' {
        Invoke-Uv -UvArgs @('run', '--', 'python', '-c', "import openai, bs4, pandas, scipy, tiktoken; print('deps-ok')")
    }
}
