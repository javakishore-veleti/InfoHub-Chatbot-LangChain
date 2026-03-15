# Launch API + UI with Docker services (Redis, Postgres) enabled.
# Expects Docker containers to already be running via DevOps/Local/docker-all-up.sh

$env:DB_TYPE = if ($env:DB_TYPE) { $env:DB_TYPE } else { "postgres" }
$env:POSTGRES_HOST = if ($env:POSTGRES_HOST) { $env:POSTGRES_HOST } else { "localhost" }
$env:POSTGRES_PORT = if ($env:POSTGRES_PORT) { $env:POSTGRES_PORT } else { "5432" }
$env:POSTGRES_USER = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "infohub" }
$env:POSTGRES_PASSWORD = if ($env:POSTGRES_PASSWORD) { $env:POSTGRES_PASSWORD } else { "infohub_dev" }
$env:POSTGRES_DB = if ($env:POSTGRES_DB) { $env:POSTGRES_DB } else { "infohub" }
$env:REDIS_HOST = if ($env:REDIS_HOST) { $env:REDIS_HOST } else { "localhost" }
$env:REDIS_PORT = if ($env:REDIS_PORT) { $env:REDIS_PORT } else { "6379" }

Write-Host "DB: Postgres at $($env:POSTGRES_HOST):$($env:POSTGRES_PORT)/$($env:POSTGRES_DB)"
Write-Host "Redis cache enabled at $($env:REDIS_HOST):$($env:REDIS_PORT)"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
& bash "$scriptDir/start-api-ui.sh"
