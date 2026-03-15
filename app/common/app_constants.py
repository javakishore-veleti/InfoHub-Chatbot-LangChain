from __future__ import annotations

from pathlib import Path


APP_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = APP_ROOT / "config.json"
STATUS_TEMPLATE_PATH = APP_ROOT / "data_engineering_status.template.json"
WORKFLOW_TASK_REGISTRY_PATH = APP_ROOT / "workflows" / "workflow_tasks.json"

SUPPORTED_CHUNKING_METHODS = {
    "fixed_token",
    "sliding_window_overlap",
    "sentence",
    "paragraph_section",
    "semantic",
    "hierarchical",
    "query_aware",
    "fixed_token_overlap",
    "paragraph",
}

DEFAULT_PROJECT_HOME = Path.home() / "Runtime_Data" / "AI_Projects" / "InfoHub-Chatblot"
DEFAULT_INGEST_STORAGE_BASE = DEFAULT_PROJECT_HOME / "ingest"
DEFAULT_STATUS_FILE = DEFAULT_PROJECT_HOME / "Data_Engineering_Status.json"
DEFAULT_SQLITE_DB_PATH = DEFAULT_PROJECT_HOME / "sqlite" / "infohub.db"

DEFAULT_API_HOST = "0.0.0.0"
DEFAULT_API_PORT = 8000
DEFAULT_UI_PORT = 4200

