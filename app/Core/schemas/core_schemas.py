from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Workflow Status (one row per workflow_id) ────────────────

class WorkflowStatusRecord(BaseModel):
    workflow_id: str
    workflow_selector: str | None = None
    display_name: str | None = None
    completed: bool = False
    last_started_at: datetime | None = None
    last_completed_at: datetime | None = None
    last_return_code: int | None = None
    last_execution_id: str | None = None
    last_run_folder: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── Execution History (all runs for a workflow) ──────────────

class ExecutionHistoryRecord(BaseModel):
    id: int | None = None
    workflow_id: str
    execution_id: str | None = None
    workflow_selector: str | None = None
    display_name: str | None = None
    status: str
    return_code: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    run_folder: str | None = None
    reused_latest_run: bool = False
    error_message: str | None = None
    summary_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class ExecutionHistoryPage(BaseModel):
    items: list[ExecutionHistoryRecord]
    page: int
    page_size: int
    total_items: int
    total_pages: int
