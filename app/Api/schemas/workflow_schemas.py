from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


FieldType = Literal["text", "textarea", "textarea-list", "number", "checkbox", "url", "select", "multiselect", "datetime-local"]


class WorkflowFieldOption(BaseModel):
    label: str
    value: str


class WorkflowFieldSchema(BaseModel):
    key: str
    label: str
    type: FieldType
    description: str | None = None
    placeholder: str | None = None
    required: bool = False
    default: Any = None
    read_only: bool = False
    min: int | None = None
    max: int | None = None
    pattern: str | None = None
    options: list[WorkflowFieldOption] = Field(default_factory=list)


class WorkflowLastExecutionSummary(BaseModel):
    execution_id: str | None = None
    status: str = "Never Executed"
    started_at: datetime | None = None
    completed_at: datetime | None = None


class WorkflowSummary(BaseModel):
    module: str
    workflow_selector: str
    workflow_parent: str
    workflow_child: str
    workflow_id: str
    display_name: str
    short_description: str
    last_execution: WorkflowLastExecutionSummary


class WorkflowDetail(WorkflowSummary):
    title: str
    description: str
    fields: list[WorkflowFieldSchema]
    raw_config: dict[str, Any]


class WorkflowRunRequest(BaseModel):
    inputs: dict[str, Any] = Field(default_factory=dict)

