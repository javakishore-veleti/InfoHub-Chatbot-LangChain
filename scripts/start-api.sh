#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

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

# Run FastAPI backend for Angular portal integration.
"$UV_BIN" run --active python -m uvicorn app.Api.api_app:app --host 0.0.0.0 --port 8000 --reload


