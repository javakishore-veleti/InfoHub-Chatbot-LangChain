from __future__ import annotations

from typing import Any

from app.Core.db.migration_manager import Migration


class M003ExecutionHistory(Migration):
    """Creates workflow_execution_history — tracks every execution event for a workflow."""

    @property
    def version(self) -> str:
        return "003"

    @property
    def description(self) -> str:
        return "Create workflow_execution_history table"

    def upgrade(self, connection: Any, ph: str) -> None:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS workflow_execution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id TEXT NOT NULL,
                execution_id TEXT,
                workflow_selector TEXT,
                display_name TEXT,
                status TEXT NOT NULL,
                return_code INTEGER,
                started_at TEXT,
                completed_at TEXT,
                run_folder TEXT,
                reused_latest_run INTEGER DEFAULT 0,
                error_message TEXT,
                summary_json TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_weh_workflow_id ON workflow_execution_history(workflow_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_weh_execution_id ON workflow_execution_history(execution_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_weh_started_at ON workflow_execution_history(started_at DESC)"
        )

    def downgrade(self, connection: Any, ph: str) -> None:
        connection.cursor().execute("DROP TABLE IF EXISTS workflow_execution_history")
