#!/usr/bin/env bash
set -euo pipefail

# Launch API + UI with Docker services (Redis, Postgres) enabled.
# Expects Docker containers to already be running via DevOps/Local/docker-all-up.sh

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export DB_TYPE="${DB_TYPE:-postgres}"
export POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
export POSTGRES_PORT="${POSTGRES_PORT:-5432}"
export POSTGRES_USER="${POSTGRES_USER:-infohub}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-infohub_dev}"
export POSTGRES_DB="${POSTGRES_DB:-infohub}"
export REDIS_HOST="${REDIS_HOST:-localhost}"
export REDIS_PORT="${REDIS_PORT:-6379}"

echo "DB: Postgres at $POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB"
echo "Redis cache enabled at $REDIS_HOST:$REDIS_PORT"

exec bash "$script_dir/start-api-ui.sh"
