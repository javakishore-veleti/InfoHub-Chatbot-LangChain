from __future__ import annotations

from typing import Any

from app.Core.db.migration_manager import Migration


class M002WorkflowStatus(Migration):
    """Creates the workflow_status table — one row per workflow_id.

    Replaces Data_Engineering_Status.json with a proper DB table.
    """

    @property
    def version(self) -> str:
        return "002"

    @property
    def description(self) -> str:
        return "Create workflow_status table (replaces Data_Engineering_Status.json)"

    def upgrade(self, connection: Any, ph: str) -> None:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS workflow_status (
                workflow_id TEXT PRIMARY KEY,
                workflow_selector TEXT,
                display_name TEXT,
                completed INTEGER DEFAULT 0,
                last_started_at TEXT,
                last_completed_at TEXT,
                last_return_code INTEGER,
                last_execution_id TEXT,
                last_run_folder TEXT,
                metadata_json TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_ws_completed ON workflow_status(completed)"
        )

    def downgrade(self, connection: Any, ph: str) -> None:
        connection.cursor().execute("DROP TABLE IF EXISTS workflow_status")
