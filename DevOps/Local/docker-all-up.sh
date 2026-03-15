#!/usr/bin/env bash
set -euo pipefail

NETWORK_NAME="infohub-chatbot-lc-net"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create shared bridge network if it doesn't exist
if ! docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
  echo "Creating bridge network '$NETWORK_NAME'..."
  docker network create --driver bridge "$NETWORK_NAME"
fi

echo "Starting Redis..."
docker compose -f "$script_dir/Redis/docker-compose.yml" up -d

echo "Starting Postgres..."
docker compose -f "$script_dir/Postgres/docker-compose.yaml" up -d

echo ""
echo "All services started."
bash "$script_dir/docker-all-status.sh"
