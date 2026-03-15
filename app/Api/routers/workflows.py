from fastapi import APIRouter, HTTPException, Query

from app.Api.services.workflow_config_service import get_workflow_detail, list_workflows

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("")
def get_workflows(domain: str | None = Query(default=None)):
    return list_workflows(domain=domain)


@router.get("/{workflow_selector:path}")
def get_workflow(workflow_selector: str):
    try:
        return get_workflow_detail(workflow_selector)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

