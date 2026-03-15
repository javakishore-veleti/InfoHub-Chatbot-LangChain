#!/usr/bin/env bash
set -euo pipefail

NETWORK_NAME="infohub-chatbot-lc-net"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Stopping Redis..."
docker compose -f "$script_dir/Redis/docker-compose.yml" down

echo "Stopping Postgres..."
docker compose -f "$script_dir/Postgres/docker-compose.yaml" down

# Remove shared network if no containers are using it
if docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
  echo "Removing bridge network '$NETWORK_NAME'..."
  docker network rm "$NETWORK_NAME" 2>/dev/null || echo "  Network still in use — skipping removal."
fi

echo ""
echo "All services stopped."
