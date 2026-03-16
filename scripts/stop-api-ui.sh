#!/usr/bin/env bash
set -euo pipefail

API_PORT=8000
UI_PORT=4200

# Kill any process occupying a given port.
# Works on Linux/macOS (lsof) and Windows/Git Bash (netstat).
free_port() {
  local port=$1
  local pid=""

  # Try lsof first (Linux/macOS).
  if command -v lsof &>/dev/null; then
    pid=$(lsof -ti :"$port" 2>/dev/null || true)
  fi

  # Fall back to netstat (Windows/Git Bash).
  if [[ -z "${pid:-}" ]]; then
    pid=$(netstat -ano 2>/dev/null | tr -d '\r' | grep ":${port} " | grep "LISTENING" | awk '{print $NF}' | head -1 || true)
  fi

  if [[ -n "${pid:-}" ]]; then
    echo "Port $port is in use by PID $pid — stopping it..."
    kill "$pid" 2>/dev/null || taskkill //PID "$pid" //F 2>/dev/null || true
    sleep 1
    echo "Stopped process on port $port."
  else
    echo "No process found on port $port."
  fi
}

echo "Stopping API + UI..."
free_port "$API_PORT"
free_port "$UI_PORT"
echo "Done."