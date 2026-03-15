from __future__ import annotations

import math
from typing import Any

from app.Core.repositories.execution_repository import ExecutionRepository
from app.Api.schemas.datalake_schemas import (
    DatasetFileDetail,
    DatasetFileMeta,
    DatasetFilePage,
    DatasetOverview,
    DatasetOverviewPage,
    FolderTypeInfo,
    RunFolderInfo,
)
from app.Api.services.datalake.cache_manager import DatalakeCacheManager
from app.Api.services.datalake.reader_factory import StorageReaderFactory


class DatalakeService:
    """Orchestrates datalake browsing — storage reader + optional cache + execution metadata."""

    def __init__(self, storage_type: str = "local"):
        self.reader = StorageReaderFactory.create(storage_type)
        self.cache = DatalakeCacheManager()
        self.execution_repo = ExecutionRepository()

    def list_datasets(self, page: int = 1, page_size: int = 20) -> DatasetOverviewPage:
        workflow_ids = self.reader.list_workflow_ids()
        total = len(workflow_ids)
        total_pages = max(1, math.ceil(total / page_size))
        offset = (page - 1) * page_size
        page_ids = workflow_ids[offset : offset + page_size]

        # Enrich with latest execution data
        latest_execs = self.execution_repo.get_latest_execution_by_workflow_ids(page_ids)

        items: list[DatasetOverview] = []
        for wf_id in page_ids:
            exec_data = latest_execs.get(wf_id)
            latest_run = self.reader.get_latest_run_folder(wf_id)

            # Count files in latest run
            file_count = 0
            if latest_run:
                folder_types = self.reader.list_folder_types(wf_id, latest_run)
                file_count = sum(ft.get("file_count", 0) for ft in folder_types)

            items.append(DatasetOverview(
                workflow_id=wf_id,
                display_name=exec_data["display_name"] if exec_data else wf_id,
                workflow_selector=exec_data["workflow_selector"] if exec_data else f"ingest/{wf_id}",
                latest_status=exec_data["status"] if exec_data else "Never Executed",
                latest_started_at=exec_data["started_at"] if exec_data else None,
                latest_completed_at=exec_data.get("completed_at") if exec_data else None,
                latest_run_folder=latest_run,
                file_count=file_count,
            ))

        return DatasetOverviewPage(
            items=items,
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages,
        )

    def list_run_folders(self, workflow_id: str) -> list[RunFolderInfo]:
        folders = self.reader.list_run_folders(workflow_id)
        return [RunFolderInfo(**f) for f in folders]

    def list_folder_types(self, workflow_id: str, run_folder: str | None = None) -> list[FolderTypeInfo]:
        if not run_folder:
            run_folder = self.reader.get_latest_run_folder(workflow_id)
        if not run_folder:
            return []
        folder_types = self.reader.list_folder_types(workflow_id, run_folder)
        return [FolderTypeInfo(**ft) for ft in folder_types]

    def list_files(
        self,
        workflow_id: str,
        page: int = 1,
        page_size: int = 50,
        folder_type: str = "crawled_pages",
        run_folder: str | None = None,
    ) -> DatasetFilePage:
        if not run_folder:
            run_folder = self.reader.get_latest_run_folder(workflow_id)
        if not run_folder:
            return DatasetFilePage(
                items=[], page=page, page_size=page_size,
                total_items=0, total_pages=0,
                workflow_id=workflow_id, run_folder=None,
            )

        # Try cache
        cache_key = f"datalake:{workflow_id}:{run_folder}:{folder_type}:p{page}:s{page_size}"
        cached = self.cache.get(cache_key)
        if cached:
            return DatasetFilePage(**cached)

        items_raw, total = self.reader.list_files(workflow_id, run_folder, folder_type, page, page_size)
        total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 0

        result = DatasetFilePage(
            items=[DatasetFileMeta(**item) for item in items_raw],
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages,
            workflow_id=workflow_id,
            run_folder=run_folder,
        )

        self.cache.set(cache_key, result.model_dump(mode="json"))
        return result

    def get_file_content(
        self,
        workflow_id: str,
        file_id: str,
        folder_type: str = "crawled_pages",
        run_folder: str | None = None,
    ) -> DatasetFileDetail | None:
        if not run_folder:
            run_folder = self.reader.get_latest_run_folder(workflow_id)
        if not run_folder:
            return None

        file_name = f"{file_id}.json"
        content = self.reader.get_file_content(workflow_id, run_folder, folder_type, file_name)
        if not content:
            return None

        # Get file size
        from app.Api.services.datalake.local_fs_reader import LocalFsReader
        size = 0
        if isinstance(self.reader, LocalFsReader):
            target_dir = self.reader._resolve_folder(workflow_id, run_folder, folder_type)
            if target_dir:
                file_path = target_dir / file_name
                try:
                    size = file_path.stat().st_size
                except OSError:
                    pass

        return DatasetFileDetail(
            file_id=file_id,
            file_name=file_name,
            url=content.get("url"),
            folder_type=folder_type,
            content=content,
            size_bytes=size,
        )
