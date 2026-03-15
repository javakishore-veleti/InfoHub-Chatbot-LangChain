# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

InfoHub Chatbot LangChain is a full-stack application for ingesting, chunking, and managing documentation using multiple chunking strategies. The system crawls HTML documentation sites, splits content using seven parallel chunking strategies, and provides a web portal for managing and monitoring these workflows. Built with Python 3.11 / FastAPI backend, Angular 20 frontend, and SQLite for execution history. Uses `uv` for Python dependency management.

## Architecture

### Backend (`app/`)

**CLI Entry Point** — `main.py` loads `config.json`, resolves a workflow selector (e.g. `ingest/AWSBedrock`) to a (parent, child, workflow_id) tuple, validates config, builds an `IngestReqDto`, and delegates to `IngestWfFacade.execute()`.

**Configuration** — `config.json` defines workflows with crawl parameters (seed_url, max_tokens, max_pages, max_depth, chunking_methods, allowed_domains) and UI field metadata that drives the Angular form dynamically.

**API Layer** (`Api/`) — FastAPI app with routers for health, workflows, ingest, executions, and chat. `ExecutionService` submits workflow runs to a `ThreadPoolExecutor` (max 4 workers), creates execution records in SQLite, and updates them on completion/failure.

**Task Framework** (`workflows/`) — `IngestWfFacade` orchestrates sequential task execution with status tracking. Tasks are dynamically loaded via `workflow_tasks.json`, which maps workflow selectors to Python class paths (e.g. `app.workflows.data_load.tasks.extract_html_files:CrawlHtmlFilesTask`). Falls back to a hardcoded task list if the registry is missing.

**Ingestion Tasks** (`workflows/data_load/tasks/`):
- `CrawlHtmlFilesTask` — BFS crawler using BeautifulSoup. Follows links up to max_depth, respects domain/path whitelists, extracts human-readable text.
- `chunking/ParallelChunkingTask` — Executes all configured chunking strategies concurrently. Each strategy inherits `BaseChunkingStrategyTask` and uses tiktoken (GPT-4 encoding) for token counting.
- Seven strategies: fixed_token, sliding_window_overlap, sentence, paragraph_section, semantic, hierarchical, query_aware.

### Frontend (`Portals/infohub-app/`)

Angular 20 with standalone components, Bootstrap 5, FontAwesome 6, light/dark theme. Enterprise SaaS layout with persistent left sidebar, top header bar with breadcrumbs and API status indicator, and toast notification system.

**Layout** (`layout/`): `ShellComponent` wraps all routes with sidebar + topbar + toast/confirm overlays. `SidebarComponent` is persistent (collapsible to 68px icon-only mode), with collapsible nav sections. `TopbarComponent` has breadcrumbs (auto-generated from route data), API health status dot, theme toggle, and user avatar placeholder.

**Shared** (`shared/`): Reusable components (toast-container, confirm-dialog, loading-skeleton, empty-state, status-badge), services (toast, confirm, breadcrumb), pipes (relative-time), and utils (status helpers). Design tokens in `styles.css` define spacing, typography, elevation, and radii scales.

**Pages** (`pages/`): Dashboard (metrics + recent executions + quick launch), Workflow Catalog (search, sort, status-colored cards), Workflow Run (sectioned form with confirmation dialog + toast notifications, navigates to detail on success), Execution History (paginated table with filters, clickable rows), Execution Detail (tabbed view: overview/request/response).

**Routing**: All routes wrapped under `ShellComponent`. Routes: `/dashboard`, `/ingest/workflows`, `/ingest/run`, `/ingest/executions`, `/ingest/executions/:executionId`. Model Build and Administration are disabled sidebar items (no routes).

### Data Flow

Config defines workflow parameters → HTML crawler fetches pages via BFS → Seven chunking strategies run in parallel → Results persisted under `~/Runtime_Data/AI_Projects/InfoHub-Chatblot/ingest/{workflow_id}/{timestamp}/`

## Key Design Patterns

- **Dynamic task registry**: `workflow_tasks.json` decouples workflow definitions from task implementations. `WorkflowTaskLoader` dynamically imports task classes at runtime.
- **Status tracking**: `Data_Engineering_Status.json` in the runtime folder tracks completion per workflow_id; re-execution is skipped unless `--fetch-again` is passed.
- **Runtime data separation**: All crawled text, chunks, and SQLite DB live under `~/Runtime_Data/AI_Projects/InfoHub-Chatblot/`, not in the repo.
- **Shared execution context**: `ExecCtxData` DTO is a mutable state bag passed through the task chain, allowing tasks to share intermediate results (e.g. crawler output feeds into chunking).

## Adding New Chunking Strategies

1. Create task class in `app/workflows/data_load/tasks/chunking/`, inheriting `BaseChunkingStrategyTask`
2. Add method name to `SUPPORTED_CHUNKING_METHODS` in `app/common/app_constants.py`
3. Register in `config.json` under the workflow's `chunking_methods` list