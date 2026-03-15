#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
portal_root="$repo_root/Portals/infohub-app"

UI_PORT=4200

# Kill any process occupying the UI port.
free_port() {
  local port=$1
  local pid=""
  pid=$(lsof -ti :"$port" 2>/dev/null) || \
    pid=$(set +o pipefail; netstat -ano 2>/dev/null | grep ":$port " | grep LISTENING | awk '{print $NF}' | head -1) || \
    true
  if [[ -n "${pid:-}" ]]; then
    echo "Port $port is in use by PID $pid — stopping it..."
    kill "$pid" 2>/dev/null || taskkill //PID "$pid" //F 2>/dev/null || true
    sleep 1
  fi
}

free_port "$UI_PORT"

if [[ ! -d "$portal_root" ]]; then
  echo "Angular portal not found at $portal_root"
  exit 1
fi

cd "$portal_root"

if [[ ! -d "node_modules" ]]; then
  echo "Installing portal dependencies..."
  npm install
fi

echo "Starting Angular UI on http://0.0.0.0:$UI_PORT"
npm run start -- --host 0.0.0.0 --port "$UI_PORT"
