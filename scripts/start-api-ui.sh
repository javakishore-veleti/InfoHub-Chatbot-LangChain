#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

