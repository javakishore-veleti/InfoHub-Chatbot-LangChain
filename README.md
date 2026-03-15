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

## Ingest workflow CLI

![Ingest workflow architecture](Docs/Images/Ingest/01_ingest_workflow_architecture.png)

The CLI now reads workflow settings from `app/config.json`, so you do not need to pass crawl arguments each run.

Run with the default workflow from config:

```bash
uv run --active python -m app.main
```

Optional JSON output for scripting:

```bash
uv run --active python -m app.main --json
```

Force a fresh crawl into a new timestamp folder:

```bash
uv run --active python -m app.main --fetch-again --json
```

Run a specific workflow entry from config:

```bash
uv run --active python -m app.main --workflow ingest
```

Use a different config file:

```bash
uv run --active python -m app.main --config ./app/config.json
```

Supported flags:

- `--config`
- `--workflow`
- `--json`
- `--fetch-again`

Config format is modularized by workflows:

```json
{
  "default_workflow": "ingest",
  "workflows": {
	"ingest": {
	  "seed_url": "https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html",
	  "max_tokens": 400,
	  "overlap_tokens": 40,
	  "max_pages": 30,
	  "max_depth": 2,
	  "timeout_seconds": 20,
	  "chunking_methods": [
		"fixed_token",
		"sliding_window_overlap",
		"sentence",
		"paragraph_section",
		"semantic",
		"hierarchical",
		"query_aware"
	  ],
	  "query_terms": ["knowledge base", "foundation model", "guardrails"]
	}
  }
}
```

`ingest` now runs as a task list: crawl once, then apply all configured chunking methods in parallel on the already-crawled text.

Task responsibilities:

- `IngestWfFacade`: orchestrates task order and status-based skip behavior.
- `CrawlHtmlFilesTask`: single crawl and readable-text extraction per page.
- `ChunkHtmlTextTask`: parallel strategy execution on already-crawled text.
- `IngestStorageManager`: writes crawl/chunk artifacts and `latest_data.json`.

Detailed strategy/task documentation: `README_INGEST_CHUNKING.md`.

Runtime output is stored under:

- `~/Runtime_Data/AI_Projects/InfoHub-Chatblot/ingest/AWSBedrock/YYYY-MM-DD-HH-MM/...`
- `latest_data.json` in `AWSBedrock` points to the latest timestamp folder.
- Without `--fetch-again`, the latest folder is reused when available.
- With `--fetch-again`, a new timestamp folder is created and `latest_data.json` is updated.

Workflow completion state is tracked in:

- `~/Runtime_Data/AI_Projects/InfoHub-Chatblot/Data_Engineering_Status.json`

This generated status file is gitignored. Template file: `app/data_engineering_status.template.json`.

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
