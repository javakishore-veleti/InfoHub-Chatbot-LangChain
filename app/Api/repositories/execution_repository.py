from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import math
from typing import Any

from app.Api.db.sqlite_db import get_connection


@dataclass
class ExecutionFilters:
    module_name: str | None = None
    workflow_id: str | None = None
    status: str | None = None
    started_from: str | None = None
    started_to: str | None = None


class ExecutionRepository:
    """SQLite persistence for workflow execution metadata used by the portal."""

    def create_execution(self, record: dict[str, Any]) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO workflow_execution (
                    execution_id, workflow_selector, workflow_id, workflow_parent, workflow_child,
                    module_name, display_name, status, request_payload_json, effective_config_json,
                    response_summary_json, active_run_folder, reused_latest_run, return_code,
                    error_message, started_at, completed_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["execution_id"],
                    record["workflow_selector"],
                    record["workflow_id"],
                    record["workflow_parent"],
                    record["workflow_child"],
                    record["module_name"],
                    record["display_name"],
                    record["status"],
                    json.dumps(record.get("request_payload", {})),
                    json.dumps(record.get("effective_config", {})),
                    json.dumps(record.get("response_summary", {})),
                    record.get("active_run_folder"),
                    1 if record.get("reused_latest_run") else 0,
                    record.get("return_code"),
                    record.get("error_message"),
                    record["started_at"],
                    record.get("completed_at"),
                    record["created_at"],
                    record["updated_at"],
                ),
            )
            connection.commit()

    def update_execution(self, execution_id: str, **updates: Any) -> None:
        if not updates:
            return
        fields: list[str] = []
        values: list[Any] = []
        for key, value in updates.items():
            if key in {"request_payload", "effective_config", "response_summary"}:
                db_key = f"{key}_json"
                value = json.dumps(value or {})
            elif key == "reused_latest_run":
                db_key = key
                value = 1 if value else 0
            else:
                db_key = key
            fields.append(f"{db_key} = ?")
            values.append(value)
        values.append(execution_id)

        with get_connection() as connection:
            connection.execute(
                f"UPDATE workflow_execution SET {', '.join(fields)} WHERE execution_id = ?",
                values,
            )
            connection.commit()

    def get_execution(self, execution_id: str) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT * FROM workflow_execution WHERE execution_id = ?",
                (execution_id,),
            ).fetchone()
        return self._row_to_record(row) if row else None

    def list_executions(self, filters: ExecutionFilters, page: int, page_size: int) -> dict[str, Any]:
        where_clauses = []
        values: list[Any] = []
        if filters.module_name:
            where_clauses.append("module_name = ?")
            values.append(filters.module_name)
        if filters.workflow_id:
            where_clauses.append("workflow_id = ?")
            values.append(filters.workflow_id)
        if filters.status and filters.status != "Never Executed":
            where_clauses.append("status = ?")
            values.append(filters.status)
        if filters.started_from:
            where_clauses.append("started_at >= ?")
            values.append(filters.started_from)
        if filters.started_to:
            where_clauses.append("started_at <= ?")
            values.append(filters.started_to)

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        offset = (page - 1) * page_size

        with get_connection() as connection:
            total_items = connection.execute(
                f"SELECT COUNT(*) FROM workflow_execution {where_sql}",
                values,
            ).fetchone()[0]
            rows = connection.execute(
                f"""
                SELECT * FROM workflow_execution
                {where_sql}
                ORDER BY started_at DESC
                LIMIT ? OFFSET ?
                """,
                (*values, page_size, offset),
            ).fetchall()

        items = [self._row_to_record(row) for row in rows]
        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": math.ceil(total_items / page_size) if page_size else 0,
        }

    def get_latest_execution_by_workflow_ids(self, workflow_ids: list[str]) -> dict[str, dict[str, Any]]:
        if not workflow_ids:
            return {}
        placeholders = ", ".join("?" for _ in workflow_ids)
        query = f"""
            SELECT * FROM workflow_execution
            WHERE workflow_id IN ({placeholders})
            ORDER BY started_at DESC
        """
        latest: dict[str, dict[str, Any]] = {}
        with get_connection() as connection:
            for row in connection.execute(query, workflow_ids).fetchall():
                record = self._row_to_record(row)
                workflow_id = record["workflow_id"]
                if workflow_id not in latest:
                    latest[workflow_id] = record
        return latest

    @staticmethod
    def _row_to_record(row) -> dict[str, Any]:
        return {
            "execution_id": row["execution_id"],
            "workflow_selector": row["workflow_selector"],
            "workflow_id": row["workflow_id"],
            "workflow_parent": row["workflow_parent"],
            "workflow_child": row["workflow_child"],
            "module_name": row["module_name"],
            "display_name": row["display_name"],
            "status": row["status"],
            "request_payload": json.loads(row["request_payload_json"] or "{}"),
            "effective_config": json.loads(row["effective_config_json"] or "{}"),
            "response_summary": json.loads(row["response_summary_json"] or "{}"),
            "active_run_folder": row["active_run_folder"],
            "reused_latest_run": bool(row["reused_latest_run"]),
            "return_code": row["return_code"],
            "error_message": row["error_message"],
            "started_at": datetime.fromisoformat(row["started_at"]),
            "completed_at": datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
        }

