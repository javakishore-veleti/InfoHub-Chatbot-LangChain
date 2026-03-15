from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ExecutionSummary(BaseModel):
    execution_id: str
    workflow_selector: str
    workflow_id: str
    workflow_parent: str
    workflow_child: str
    module_name: str
    display_name: str
    status: str
    return_code: int | None = None
    active_run_folder: str | None = None
    reused_latest_run: bool = False
    started_at: datetime
    completed_at: datetime | None = None


class ExecutionDetail(ExecutionSummary):
    request_payload: dict[str, Any] = Field(default_factory=dict)
    effective_config: dict[str, Any] = Field(default_factory=dict)
    response_summary: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None


class ExecutionPage(BaseModel):
    items: list[ExecutionSummary]
    page: int
    page_size: int
    total_items: int
    total_pages: int

