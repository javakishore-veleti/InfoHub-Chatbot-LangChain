from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DatasetOverview(BaseModel):
    workflow_id: str
    display_name: str
    workflow_selector: str
    latest_status: str = "Never Executed"
    latest_started_at: datetime | None = None
    latest_completed_at: datetime | None = None
    latest_run_folder: str | None = None
    file_count: int = 0


class DatasetOverviewPage(BaseModel):
    items: list[DatasetOverview]
    page: int
    page_size: int
    total_items: int
    total_pages: int


class DatasetFileMeta(BaseModel):
    file_id: str
    file_name: str
    url: str | None = None
    size_bytes: int = 0
    modified_at: datetime | None = None
    folder_type: str


class DatasetFilePage(BaseModel):
    items: list[DatasetFileMeta]
    page: int
    page_size: int
    total_items: int
    total_pages: int
    workflow_id: str
    run_folder: str | None = None


class DatasetFileDetail(BaseModel):
    file_id: str
    file_name: str
    url: str | None = None
    folder_type: str
    content: dict[str, Any] = Field(default_factory=dict)
    size_bytes: int = 0


class RunFolderInfo(BaseModel):
    folder_name: str
    is_latest: bool = False
    updated_at: str | None = None


class FolderTypeInfo(BaseModel):
    folder_type: str
    label: str
    file_count: int = 0
