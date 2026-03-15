from fastapi import APIRouter, HTTPException, Query

from app.Api.services.execution_service import ExecutionService
from app.Core.services.workflow_status_service import WorkflowStatusService

router = APIRouter(prefix="/executions", tags=["executions"])
service = ExecutionService()
_status_service = WorkflowStatusService()


@router.get("/")
def get_executions(
    module_name: str | None = Query(default=None),
    workflow_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    started_from: str | None = Query(default=None),
    started_to: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=15, ge=1, le=100),
):
    return service.list_executions(
        module_name=module_name,
        workflow_id=workflow_id,
        status=status,
        started_from=started_from,
        started_to=started_to,
        page=page,
        page_size=page_size,
    )


@router.get("/history/{workflow_id}")
def get_workflow_execution_history(
    workflow_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    return _status_service.get_execution_history(workflow_id, page, page_size)


@router.get("/status/{workflow_id}")
def get_workflow_status(workflow_id: str):
    status = _status_service.get_status(workflow_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Workflow status not found")
    return status


@router.get("/{execution_id}")
def get_execution(execution_id: str):
    execution = service.get_execution(execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution

