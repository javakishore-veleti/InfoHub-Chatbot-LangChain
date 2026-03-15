from __future__ import annotations

from datetime import datetime
from typing import Any

from app.Core.repositories.execution_history_repository import ExecutionHistoryRepository
from app.Core.repositories.workflow_status_repository import WorkflowStatusRepository
from app.Core.utils.singleton import SingletonMeta


class WorkflowStatusService(metaclass=SingletonMeta):
    """Manages workflow status lifecycle. Replaces Data_Engineering_Status.json file operations.

    Stateless singleton — delegates all persistence to repositories.
    """

    def __init__(self):
        self._status_repo = WorkflowStatusRepository()
        self._history_repo = ExecutionHistoryRepository()

    def get_status(self, workflow_id: str) -> dict[str, Any] | None:
        return self._status_repo.get_status(workflow_id)

    def is_completed(self, workflow_id: str) -> bool:
        status = self._status_repo.get_status(workflow_id)
        return bool(status and status.get("completed"))

    def mark_started(
        self,
        workflow_id: str,
        workflow_selector: str | None = None,
        display_name: str | None = None,
        execution_id: str | None = None,
    ) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        self._status_repo.upsert_status(
            workflow_id,
            workflow_selector=workflow_selector,
            display_name=display_name,
            completed=False,
            last_started_at=now,
            last_execution_id=execution_id,
        )

    def mark_completed(
        self,
        workflow_id: str,
        return_code: int,
        run_folder: str | None = None,
        execution_id: str | None = None,
        workflow_selector: str | None = None,
        display_name: str | None = None,
        error_message: str | None = None,
        summary: dict[str, Any] | None = None,
    ) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        completed = return_code == 0
        self._status_repo.upsert_status(
            workflow_id,
            completed=completed,
            last_completed_at=now,
            last_return_code=return_code,
            last_run_folder=run_folder,
            last_execution_id=execution_id,
        )

        # Record in execution history
        self._history_repo.add_history_entry({
            "workflow_id": workflow_id,
            "execution_id": execution_id,
            "workflow_selector": workflow_selector,
            "display_name": display_name,
            "status": "COMPLETED" if completed else "FAILED",
            "return_code": return_code,
            "started_at": self._get_last_started(workflow_id),
            "completed_at": now,
            "run_folder": run_folder,
            "error_message": error_message,
            "summary_json": summary or {},
        })

    def mark_skipped(
        self,
        workflow_id: str,
        execution_id: str | None = None,
        workflow_selector: str | None = None,
        display_name: str | None = None,
    ) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        self._history_repo.add_history_entry({
            "workflow_id": workflow_id,
            "execution_id": execution_id,
            "workflow_selector": workflow_selector,
            "display_name": display_name,
            "status": "SKIPPED",
            "return_code": 2,
            "started_at": now,
            "completed_at": now,
        })

    def list_all_statuses(self) -> list[dict[str, Any]]:
        return self._status_repo.list_all_statuses()

    def get_execution_history(self, workflow_id: str, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        return self._history_repo.list_history(workflow_id, page, page_size)

    def _get_last_started(self, workflow_id: str) -> str | None:
        status = self._status_repo.get_status(workflow_id)
        return status.get("last_started_at") if status else None
