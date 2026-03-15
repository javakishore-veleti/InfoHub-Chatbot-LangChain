#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

API_PORT=8000
UI_PORT=4200

# Kill any process occupying a given port.
free_port() {
  local port=$1
  local pid=""
  # Try lsof first (Linux/macOS), fall back to netstat (Windows/Git Bash).
  # Wrapped in a subshell with pipefail disabled so grep returning no match
  # does not abort the script under set -euo pipefail.
  pid=$(lsof -ti :"$port" 2>/dev/null) || \
    pid=$(set +o pipefail; netstat -ano 2>/dev/null | grep ":$port " | grep LISTENING | awk '{print $NF}' | head -1) || \
    true
  if [[ -n "${pid:-}" ]]; then
    echo "Port $port is in use by PID $pid — stopping it..."
    kill "$pid" 2>/dev/null || taskkill //PID "$pid" //F 2>/dev/null || true
    sleep 1
  fi
}

free_port "$API_PORT"
free_port "$UI_PORT"

cleanup() {
  if [[ -n "${API_PID:-}" ]]; then
    kill "$API_PID" 2>/dev/null || true
  fi
  if [[ -n "${UI_PID:-}" ]]; then
    kill "$UI_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

bash "$script_dir/start-api.sh" &
API_PID=$!
echo "Started API with PID $API_PID"

bash "$script_dir/start-ui.sh" &
UI_PID=$!
echo "Started UI with PID $UI_PID"

wait "$API_PID" "$UI_PID"
