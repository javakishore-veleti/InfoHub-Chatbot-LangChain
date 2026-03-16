#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

API_PORT=8000

# Kill any process occupying the API port.
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

free_port "$API_PORT"

cd "$repo_root"

# Resolve uv for Bash on Windows (where uv may only be available as uv.exe).
if command -v uv >/dev/null 2>&1; then
  UV_BIN="uv"
elif command -v uv.exe >/dev/null 2>&1; then
  UV_BIN="uv.exe"
elif [[ -x "$HOME/.local/bin/uv.exe" ]]; then
  UV_BIN="$HOME/.local/bin/uv.exe"
elif [[ -x "$HOME/.cargo/bin/uv.exe" ]]; then
  UV_BIN="$HOME/.cargo/bin/uv.exe"
else
  echo "uv executable not found. Install uv or add it to PATH."
  echo "Expected examples: uv, uv.exe, $HOME/.local/bin/uv.exe"
  exit 127
fi

echo "Starting FastAPI backend on http://0.0.0.0:$API_PORT (DB_TYPE=${DB_TYPE:-sqlite})"
"$UV_BIN" run --active python -m uvicorn app.Api.api_app:app --host 0.0.0.0 --port "$API_PORT" --reload
