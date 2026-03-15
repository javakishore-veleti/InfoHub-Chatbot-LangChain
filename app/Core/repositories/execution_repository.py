from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.Core.db.provider_factory import DbProviderFactory
from app.Core.interfaces.repository_interfaces import IExecutionRepository
from app.Core.utils.singleton import SingletonABCMeta


@dataclass
class ExecutionFilters:
    module_name: str | None = None
    workflow_id: str | None = None
    status: str | None = None
    started_from: str | None = None
    started_to: str | None = None


class ExecutionRepository(IExecutionRepository, metaclass=SingletonABCMeta):
    """SQLite/Postgres persistence for workflow execution metadata. Stateless singleton."""

    def _conn(self):
        return DbProviderFactory.get_provider().connection()

    def _ph(self) -> str:
        return DbProviderFactory.get_provider().placeholder

    def create_execution(self, record: dict[str, Any]) -> None:
        ph = self._ph()
        placeholders = ", ".join([ph] * 19)
        with self._conn() as connection:
            connection.cursor().execute(
                f"""
                INSERT INTO workflow_execution (
                    execution_id, workflow_selector, workflow_id, workflow_parent, workflow_child,
                    module_name, display_name, status, request_payload_json, effective_config_json,
                    response_summary_json, active_run_folder, reused_latest_run, return_code,
                    error_message, started_at, completed_at, created_at, updated_at
                ) VALUES ({placeholders})
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
        ph = self._ph()
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
            fields.append(f"{db_key} = {ph}")
            values.append(value)
        values.append(execution_id)

        with self._conn() as connection:
            connection.cursor().execute(
                f"UPDATE workflow_execution SET {', '.join(fields)} WHERE execution_id = {ph}",
                values,
            )
            connection.commit()

    def get_execution(self, execution_id: str) -> dict[str, Any] | None:
        ph = self._ph()
        with self._conn() as connection:
            row = connection.cursor().execute(
                f"SELECT * FROM workflow_execution WHERE execution_id = {ph}",
                (execution_id,),
            ).fetchone()
        return self._row_to_record(row) if row else None

    def list_executions(self, filters: ExecutionFilters, page: int, page_size: int) -> dict[str, Any]:
        ph = self._ph()
        where_clauses: list[str] = []
        values: list[Any] = []
        if filters.module_name:
            where_clauses.append(f"module_name = {ph}")
            values.append(filters.module_name)
        if filters.workflow_id:
            where_clauses.append(f"workflow_id = {ph}")
            values.append(filters.workflow_id)
        if filters.status and filters.status != "Never Executed":
            where_clauses.append(f"status = {ph}")
            values.append(filters.status)
        if filters.started_from:
            where_clauses.append(f"started_at >= {ph}")
            values.append(filters.started_from)
        if filters.started_to:
            where_clauses.append(f"started_at <= {ph}")
            values.append(filters.started_to)

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        offset = (page - 1) * page_size

        with self._conn() as connection:
            cursor = connection.cursor()
            total_items = cursor.execute(
                f"SELECT COUNT(*) FROM workflow_execution {where_sql}", values,
            ).fetchone()[0]
            rows = cursor.execute(
                f"""
                SELECT * FROM workflow_execution
                {where_sql}
                ORDER BY started_at DESC
                LIMIT {ph} OFFSET {ph}
                """,
                (*values, page_size, offset),
            ).fetchall()

        return {
            "items": [self._row_to_record(row) for row in rows],
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": math.ceil(total_items / page_size) if page_size else 0,
        }

    def get_latest_execution_by_workflow_ids(self, workflow_ids: list[str]) -> dict[str, dict[str, Any]]:
        if not workflow_ids:
            return {}
        ph = self._ph()
        placeholders = ", ".join(ph for _ in workflow_ids)
        query = f"""
            SELECT * FROM workflow_execution
            WHERE workflow_id IN ({placeholders})
            ORDER BY started_at DESC
        """
        latest: dict[str, dict[str, Any]] = {}
        with self._conn() as connection:
            for row in connection.cursor().execute(query, workflow_ids).fetchall():
                record = self._row_to_record(row)
                wf_id = record["workflow_id"]
                if wf_id not in latest:
                    latest[wf_id] = record
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
