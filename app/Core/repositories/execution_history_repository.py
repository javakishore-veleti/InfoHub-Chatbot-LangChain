from __future__ import annotations

import json
import math
from datetime import datetime
from typing import Any

from app.Core.db.provider_factory import DbProviderFactory
from app.Core.interfaces.repository_interfaces import IExecutionHistoryRepository
from app.Core.utils.singleton import SingletonABCMeta


class ExecutionHistoryRepository(IExecutionHistoryRepository, metaclass=SingletonABCMeta):
    """Tracks every execution event for a workflow_id. Stateless singleton."""

    def _conn(self):
        return DbProviderFactory.get_provider().connection()

    def _ph(self) -> str:
        return DbProviderFactory.get_provider().placeholder

    def add_history_entry(self, record: dict[str, Any]) -> None:
        ph = self._ph()
        summary = record.get("summary_json")
        if isinstance(summary, dict):
            summary = json.dumps(summary)

        with self._conn() as conn:
            conn.cursor().execute(
                f"""
                INSERT INTO workflow_execution_history (
                    workflow_id, execution_id, workflow_selector, display_name,
                    status, return_code, started_at, completed_at,
                    run_folder, reused_latest_run, error_message, summary_json
                ) VALUES ({', '.join([ph] * 12)})
                """,
                (
                    record["workflow_id"],
                    record.get("execution_id"),
                    record.get("workflow_selector"),
                    record.get("display_name"),
                    record["status"],
                    record.get("return_code"),
                    record.get("started_at"),
                    record.get("completed_at"),
                    record.get("run_folder"),
                    1 if record.get("reused_latest_run") else 0,
                    record.get("error_message"),
                    summary,
                ),
            )
            conn.commit()

    def list_history(self, workflow_id: str, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        ph = self._ph()
        offset = (page - 1) * page_size

        with self._conn() as conn:
            cursor = conn.cursor()
            total = cursor.execute(
                f"SELECT COUNT(*) FROM workflow_execution_history WHERE workflow_id = {ph}",
                (workflow_id,),
            ).fetchone()[0]

            rows = cursor.execute(
                f"""
                SELECT * FROM workflow_execution_history
                WHERE workflow_id = {ph}
                ORDER BY started_at DESC
                LIMIT {ph} OFFSET {ph}
                """,
                (workflow_id, page_size, offset),
            ).fetchall()

        return {
            "items": [self._row_to_dict(row) for row in rows],
            "page": page,
            "page_size": page_size,
            "total_items": total,
            "total_pages": math.ceil(total / page_size) if page_size else 0,
        }

    def get_history_entry(self, history_id: int) -> dict[str, Any] | None:
        ph = self._ph()
        with self._conn() as conn:
            row = conn.cursor().execute(
                f"SELECT * FROM workflow_execution_history WHERE id = {ph}",
                (history_id,),
            ).fetchone()
        return self._row_to_dict(row) if row else None

    @staticmethod
    def _row_to_dict(row) -> dict[str, Any]:
        summary_raw = row["summary_json"]
        try:
            summary = json.loads(summary_raw) if summary_raw else {}
        except (json.JSONDecodeError, TypeError):
            summary = {}

        return {
            "id": row["id"],
            "workflow_id": row["workflow_id"],
            "execution_id": row["execution_id"],
            "workflow_selector": row["workflow_selector"],
            "display_name": row["display_name"],
            "status": row["status"],
            "return_code": row["return_code"],
            "started_at": row["started_at"],
            "completed_at": row["completed_at"],
            "run_folder": row["run_folder"],
            "reused_latest_run": bool(row["reused_latest_run"]),
            "error_message": row["error_message"],
            "summary_json": summary,
            "created_at": row["created_at"],
        }
