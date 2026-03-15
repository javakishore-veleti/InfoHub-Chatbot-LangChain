#!/usr/bin/env bash
set -euo pipefail

NETWORK_NAME="infohub-chatbot-lc-net"

echo "=== InfoHub Docker Service Status ==="
echo ""
echo "--- Network ---"
if docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
  echo "  $NETWORK_NAME: active"
else
  echo "  $NETWORK_NAME: not found"
fi
echo ""
echo "--- Containers ---"
docker ps -a --filter "name=infohub-chatbot-lc-" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "  No containers found"
