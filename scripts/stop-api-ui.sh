#!/usr/bin/env bash
set -euo pipefail

API_PORT=8000
UI_PORT=4200

# Kill ALL processes occupying a given port (including child process trees).
# Works on Linux/macOS (lsof) and Windows/Git Bash (netstat + taskkill).
free_port() {
  local port=$1
  local pids=""

  # Try lsof first (Linux/macOS).
  if command -v lsof &>/dev/null; then
    pids=$(lsof -ti :"$port" 2>/dev/null || true)
  fi

  # Fall back to netstat (Windows/Git Bash).
  if [[ -z "${pids:-}" ]]; then
    pids=$(netstat -ano 2>/dev/null | tr -d '\r' | grep ":${port} " | grep "LISTENING" | awk '{print $NF}' | sort -u || true)
  fi

  if [[ -z "${pids:-}" ]]; then
    echo "No process found on port $port."
    return
  fi

  for pid in $pids; do
    echo "Port $port — killing PID $pid (with process tree)..."
    # Use /T to kill the entire process tree on Windows.
    taskkill //PID "$pid" //T //F 2>/dev/null || kill "$pid" 2>/dev/null || true
  done

  # Wait for ports to be released.
  local retries=5
  while (( retries > 0 )); do
    sleep 1
    local remaining=""
    remaining=$(netstat -ano 2>/dev/null | tr -d '\r' | grep ":${port} " | grep "LISTENING" | awk '{print $NF}' | sort -u || true)
    if [[ -z "$remaining" ]]; then
      break
    fi
    echo "Port $port still in use — retrying ($retries)..."
    for pid in $remaining; do
      taskkill //PID "$pid" //T //F 2>/dev/null || kill "$pid" 2>/dev/null || true
    done
    (( retries-- ))
  done
  echo "Stopped all processes on port $port."
}

echo "Stopping API + UI..."
free_port "$API_PORT"
free_port "$UI_PORT"
echo "Done."
