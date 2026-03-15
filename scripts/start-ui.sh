#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
portal_root="$repo_root/Portals/infohub-app"

if [[ ! -d "$portal_root" ]]; then
  echo "Angular portal not found at $portal_root"
  exit 1
fi

cd "$portal_root"

if [[ ! -d "node_modules" ]]; then
  echo "Installing portal dependencies..."
  npm install
fi

npm run start -- --host 0.0.0.0 --port 4200

