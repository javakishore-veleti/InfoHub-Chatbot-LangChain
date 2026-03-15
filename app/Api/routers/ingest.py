from fastapi import APIRouter, HTTPException

from app.Api.schemas.workflow_schemas import WorkflowRunRequest
from app.Api.services.execution_service import ExecutionService

router = APIRouter(prefix="/ingest", tags=["ingest"])
service = ExecutionService()


@router.post("/runs/{workflow_selector:path}")
def create_ingest_run(workflow_selector: str, request: WorkflowRunRequest):
    try:
        return service.submit_ingest_run(workflow_selector, request.inputs)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

