from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IExecutionRepository(ABC):
    """Interface for workflow execution persistence."""

    @abstractmethod
    def create_execution(self, record: dict[str, Any]) -> None: ...

    @abstractmethod
    def update_execution(self, execution_id: str, **updates: Any) -> None: ...

    @abstractmethod
    def get_execution(self, execution_id: str) -> dict[str, Any] | None: ...

    @abstractmethod
    def list_executions(self, filters: Any, page: int, page_size: int) -> dict[str, Any]: ...

    @abstractmethod
    def get_latest_execution_by_workflow_ids(self, workflow_ids: list[str]) -> dict[str, dict[str, Any]]: ...


class IWorkflowStatusRepository(ABC):
    """Interface for workflow status persistence (one row per workflow_id). Replaces Data_Engineering_Status.json."""

    @abstractmethod
    def get_status(self, workflow_id: str) -> dict[str, Any] | None: ...

    @abstractmethod
    def upsert_status(self, workflow_id: str, **fields: Any) -> None: ...

    @abstractmethod
    def list_all_statuses(self) -> list[dict[str, Any]]: ...


class IExecutionHistoryRepository(ABC):
    """Interface for workflow execution history (all runs for a given workflow_id)."""

    @abstractmethod
    def add_history_entry(self, record: dict[str, Any]) -> None: ...

    @abstractmethod
    def list_history(self, workflow_id: str, page: int, page_size: int) -> dict[str, Any]: ...

    @abstractmethod
    def get_history_entry(self, history_id: int) -> dict[str, Any] | None: ...
