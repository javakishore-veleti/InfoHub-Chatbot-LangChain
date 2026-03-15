from __future__ import annotations

import sqlite3
from pathlib import Path

from app.common.app_constants import DEFAULT_SQLITE_DB_PATH


def get_db_path() -> Path:
    """Return the SQLite database path used by the API backend."""
    DEFAULT_SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return DEFAULT_SQLITE_DB_PATH


def get_connection() -> sqlite3.Connection:
    """Create a SQLite connection with row access by column name."""
    db_path = get_db_path()
    connection = sqlite3.connect(db_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    """Create the execution table and supporting indexes if they do not already exist."""
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS workflow_execution (
                execution_id TEXT PRIMARY KEY,
                workflow_selector TEXT NOT NULL,
                workflow_id TEXT NOT NULL,
                workflow_parent TEXT NOT NULL,
                workflow_child TEXT NOT NULL,
                module_name TEXT NOT NULL,
                display_name TEXT NOT NULL,
                status TEXT NOT NULL,
                request_payload_json TEXT,
                effective_config_json TEXT,
                response_summary_json TEXT,
                active_run_folder TEXT,
                reused_latest_run INTEGER DEFAULT 0,
                return_code INTEGER,
                error_message TEXT,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """,
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_workflow_execution_workflow_id ON workflow_execution(workflow_id)",
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_workflow_execution_status ON workflow_execution(status)",
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_workflow_execution_started_at ON workflow_execution(started_at DESC)",
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_workflow_execution_module_name ON workflow_execution(module_name)",
        )
        connection.commit()

