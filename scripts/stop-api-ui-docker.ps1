# Stop API + UI processes that were started with Docker backend env vars.
# Docker containers (Redis, Postgres) are left running — use devops:docker:stop-all to stop those.

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
& powershell -NoProfile -ExecutionPolicy Bypass -File "$scriptDir\stop-api-ui.ps1"
