#!/usr/bin/env bash
set -euo pipefail

# Stop API + UI processes that were started with Docker backend env vars.
# Docker containers (Redis, Postgres) are left running — use devops:docker:stop-all to stop those.

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec bash "$script_dir/stop-api-ui.sh"
