# InfoHub-Chatbot-LangChain

This project uses `uv` for Python dependency management and `npm` scripts as convenient local command wrappers.

## Prerequisites

- Python 3.11
- `uv` installed on your machine
- Node.js + npm
- Bash-compatible shell (Git Bash, WSL, or similar)

Install `uv` on Windows:

```powershell
winget install --id astral-sh.uv -e --accept-package-agreements --accept-source-agreements
```

## Local setup commands

Initialize local setup (creates/uses venv, syncs dependencies, prints status):

```bash
npm run setup:local:init
```

Set up only the venv:

```bash
npm run setup:local:venv:setup
```

Show the activate command for your current shell:

```bash
npm run setup:local:venv:activate
```

Show the deactivate guidance:

```bash
npm run setup:local:venv:deactivate
```

Show environment status:

```bash
npm run setup:local:status
```

Destroy environment:

```bash
npm run setup:local:destroy
```

Other useful commands:

```bash
npm run setup:local:sync
npm run setup:local:python:version
npm run setup:local:deps:check
```

Note: `npm run` executes in a child process, so activate/deactivate cannot directly mutate your current terminal session. Use the printed activation command in the shell you want to work in.

## Optional: choose a custom venv location

By default, scripts use:

1. `INFOHUB_VENV_PATH` (if set)
2. `VIRTUAL_ENV` (if set)
3. Project-local `.venv`

Example (Bash):

```bash
export INFOHUB_VENV_PATH="$HOME/runtime_data/python_venvs/InfoHub-Chatbot-LangChain"
npm run setup:local:init
```

## PyCharm interpreter

Set the project interpreter to `<venv-path>/Scripts/python.exe` (Windows venv) or `<venv-path>/bin/python` (Unix venv), based on your resolved environment path.

Current direct dependencies are tracked in `pyproject.toml`:

- `openai`
- `beautifulsoup4`
- `pandas`
- `scipy`
- `tiktoken`
