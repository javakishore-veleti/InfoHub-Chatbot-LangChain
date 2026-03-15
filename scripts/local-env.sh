#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <setup|sync|status|destroy|python-version|deps-check|activate|deactivate>"
  exit 1
fi

action="$1"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
project_name="$(basename "$repo_root")"

if [[ -n "${INFOHUB_VENV_PATH:-}" ]]; then
  venv_path="$INFOHUB_VENV_PATH"
elif [[ -n "${VIRTUAL_ENV:-}" ]]; then
  venv_path="$VIRTUAL_ENV"
else
  venv_path="$repo_root/.venv"
fi

# Keep uv aligned to one explicit environment path.
export UV_PROJECT_ENVIRONMENT="$venv_path"

uv_cmd() {
  uv "$@"
}

venv_python_path() {
  if [[ -x "$venv_path/Scripts/python.exe" ]]; then
    echo "$venv_path/Scripts/python.exe"
    return 0
  fi
  if [[ -x "$venv_path/bin/python" ]]; then
    echo "$venv_path/bin/python"
    return 0
  fi
  return 1
}

venv_activate_path() {
  if [[ -f "$venv_path/Scripts/activate" ]]; then
    echo "$venv_path/Scripts/activate"
    return 0
  fi
  if [[ -f "$venv_path/bin/activate" ]]; then
    echo "$venv_path/bin/activate"
    return 0
  fi
  return 1
}

echo "Project root: $repo_root"
echo "Project name: $project_name"
echo "Virtual env: $venv_path"

case "$action" in
  setup)
    uv_cmd python pin 3.11
    if [[ ! -d "$venv_path" ]]; then
      uv_cmd venv --python 3.11 "$venv_path"
    else
      echo "Environment already exists. Skipping venv creation."
    fi
    uv_cmd sync
    echo "Local environment setup complete."
    ;;
  sync)
    uv_cmd sync
    echo "Dependencies synced."
    ;;
  status)
    if python_exe="$(venv_python_path)"; then
      echo "Environment exists: yes"
      "$python_exe" --version
    else
      echo "Environment exists: no"
      echo "Run npm run setup:local:venv:setup"
    fi
    uv_cmd tree --depth 1
    ;;
  activate)
    if activate_script="$(venv_activate_path)"; then
      echo "Activation cannot persist when run via npm child process."
      echo "Run this command in your current shell:"
      echo "source \"$activate_script\""
    else
      echo "Environment does not exist yet."
      echo "Run npm run setup:local:venv:setup"
      exit 1
    fi
    ;;
  deactivate)
    echo "Deactivation must be run in the currently activated shell."
    echo "In that shell, run: deactivate"
    ;;
  destroy)
    if [[ -d "$venv_path" ]]; then
      rm -rf "$venv_path"
      echo "Environment deleted."
    else
      echo "Environment not found. Nothing to delete."
    fi
    ;;
  python-version)
    uv_cmd run -- python --version
    ;;
  deps-check)
    uv_cmd run -- python -c "import openai, bs4, pandas, scipy, tiktoken; print('deps-ok')"
    ;;
  *)
    echo "Unknown action: $action"
    exit 1
    ;;
esac

