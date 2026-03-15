from fastapi import APIRouter, HTTPException, Query

from app.Api.schemas.datalake_schemas import (
    DatasetFileDetail,
    DatasetFilePage,
    DatasetOverviewPage,
    FolderTypeInfo,
    RunFolderInfo,
)
from app.Api.services.datalake.datalake_service import DatalakeService

router = APIRouter(prefix="/datalake", tags=["datalake"])

_service = DatalakeService()


@router.get("/datasets", response_model=DatasetOverviewPage)
def list_datasets(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    return _service.list_datasets(page, page_size)


@router.get("/datasets/{workflow_id}/runs", response_model=list[RunFolderInfo])
def list_run_folders(workflow_id: str):
    return _service.list_run_folders(workflow_id)


@router.get("/datasets/{workflow_id}/folder-types", response_model=list[FolderTypeInfo])
def list_folder_types(
    workflow_id: str,
    run_folder: str | None = Query(default=None),
):
    return _service.list_folder_types(workflow_id, run_folder)


@router.get("/datasets/{workflow_id}/files", response_model=DatasetFilePage)
def list_files(
    workflow_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    folder_type: str = Query(default="crawled_pages"),
    run_folder: str | None = Query(default=None),
):
    return _service.list_files(workflow_id, page, page_size, folder_type, run_folder)


@router.get("/datasets/{workflow_id}/files/{file_id}", response_model=DatasetFileDetail)
def get_file_detail(
    workflow_id: str,
    file_id: str,
    folder_type: str = Query(default="crawled_pages"),
    run_folder: str | None = Query(default=None),
):
    result = _service.get_file_content(workflow_id, file_id, folder_type, run_folder)
    if not result:
        raise HTTPException(status_code=404, detail="File not found")
    return result
