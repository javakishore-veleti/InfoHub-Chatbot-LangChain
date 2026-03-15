from __future__ import annotations

from typing import Any

from app.Core.db.migration_manager import Migration


class M001WorkflowExecution(Migration):
    """Creates the workflow_execution table and its indexes."""

    @property
    def version(self) -> str:
        return "001"

    @property
    def description(self) -> str:
        return "Create workflow_execution table"

    def upgrade(self, connection: Any, ph: str) -> None:
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
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_we_workflow_id ON workflow_execution(workflow_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_we_status ON workflow_execution(status)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_we_started_at ON workflow_execution(started_at DESC)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_we_module_name ON workflow_execution(module_name)"
        )

    def downgrade(self, connection: Any, ph: str) -> None:
        connection.cursor().execute("DROP TABLE IF EXISTS workflow_execution")
