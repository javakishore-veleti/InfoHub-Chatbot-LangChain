from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.Core.db.provider_factory import DbProviderFactory
from app.Core.interfaces.repository_interfaces import IWorkflowStatusRepository
from app.Core.utils.singleton import SingletonABCMeta


class WorkflowStatusRepository(IWorkflowStatusRepository, metaclass=SingletonABCMeta):
    """Persists one status row per workflow_id. Replaces Data_Engineering_Status.json. Stateless singleton."""

    def _conn(self):
        return DbProviderFactory.get_provider().connection()

    def _ph(self) -> str:
        return DbProviderFactory.get_provider().placeholder

    def get_status(self, workflow_id: str) -> dict[str, Any] | None:
        ph = self._ph()
        with self._conn() as conn:
            row = conn.cursor().execute(
                f"SELECT * FROM workflow_status WHERE workflow_id = {ph}",
                (workflow_id,),
            ).fetchone()
        return self._row_to_dict(row) if row else None

    def upsert_status(self, workflow_id: str, **fields: Any) -> None:
        ph = self._ph()
        now = datetime.now().isoformat(timespec="seconds")

        existing = self.get_status(workflow_id)
        if existing:
            # UPDATE
            set_parts: list[str] = []
            values: list[Any] = []
            for key, value in fields.items():
                if key == "metadata_json" and isinstance(value, dict):
                    value = json.dumps(value)
                elif key == "completed":
                    value = 1 if value else 0
                set_parts.append(f"{key} = {ph}")
                values.append(value)
            set_parts.append(f"updated_at = {ph}")
            values.append(now)
            values.append(workflow_id)

            with self._conn() as conn:
                conn.cursor().execute(
                    f"UPDATE workflow_status SET {', '.join(set_parts)} WHERE workflow_id = {ph}",
                    values,
                )
                conn.commit()
        else:
            # INSERT
            fields.setdefault("created_at", now)
            fields.setdefault("updated_at", now)
            if "completed" in fields:
                fields["completed"] = 1 if fields["completed"] else 0
            if "metadata_json" in fields and isinstance(fields["metadata_json"], dict):
                fields["metadata_json"] = json.dumps(fields["metadata_json"])

            columns = ["workflow_id"] + list(fields.keys())
            placeholders = ", ".join(ph for _ in columns)
            col_names = ", ".join(columns)
            values = [workflow_id] + list(fields.values())

            with self._conn() as conn:
                conn.cursor().execute(
                    f"INSERT INTO workflow_status ({col_names}) VALUES ({placeholders})",
                    values,
                )
                conn.commit()

    def list_all_statuses(self) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.cursor().execute(
                "SELECT * FROM workflow_status ORDER BY workflow_id"
            ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    @staticmethod
    def _row_to_dict(row) -> dict[str, Any]:
        metadata_raw = row["metadata_json"]
        try:
            metadata = json.loads(metadata_raw) if metadata_raw else {}
        except (json.JSONDecodeError, TypeError):
            metadata = {}

        return {
            "workflow_id": row["workflow_id"],
            "workflow_selector": row["workflow_selector"],
            "display_name": row["display_name"],
            "completed": bool(row["completed"]),
            "last_started_at": row["last_started_at"],
            "last_completed_at": row["last_completed_at"],
            "last_return_code": row["last_return_code"],
            "last_execution_id": row["last_execution_id"],
            "last_run_folder": row["last_run_folder"],
            "metadata_json": metadata,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
