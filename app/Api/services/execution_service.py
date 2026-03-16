from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from uuid import uuid4

from app.Core.repositories.execution_repository import ExecutionFilters, ExecutionRepository
from app.Core.services.workflow_status_service import WorkflowStatusService
from app.Api.schemas.execution_schemas import ExecutionDetail, ExecutionPage, ExecutionSummary
from app.Api.services.workflow_config_service import build_effective_config
from app.common.app_constants import DEFAULT_INGEST_STORAGE_BASE, WORKFLOW_TASK_REGISTRY_PATH
from app.common.dtos.exec_ctx_dto import ExecCtxData
from app.common.dtos.ingest_dtos import IngestReqDto, IngestRespDto
from app.workflows.data_load.ingest_wf_facade import IngestWfFacade


logger = logging.getLogger(__name__)


class ExecutionService:
    """Background execution orchestration for workflow runs requested by the portal."""

    _executor = ThreadPoolExecutor(max_workers=4)

    def __init__(self):
        self.repository = ExecutionRepository()
        self.status_service = WorkflowStatusService()

    def submit_ingest_run(self, workflow_selector: str, inputs: dict) -> ExecutionSummary:
        logger.info("Submitting ingest run for workflow_selector=%s", workflow_selector)
        parent_name, child_name, selector, workflow_id, effective_config = build_effective_config(workflow_selector, inputs)
        display_name = effective_config.get("ui", {}).get("display_name") or effective_config.get("display_name") or child_name
        now = datetime.now().isoformat(timespec="seconds")
        execution_id = str(uuid4())
        record = {
            "execution_id": execution_id,
            "workflow_selector": selector,
            "workflow_id": workflow_id,
            "workflow_parent": parent_name,
            "workflow_child": child_name,
            "module_name": parent_name,
            "display_name": display_name,
            "status": "IN_PROGRESS",
            "request_payload": inputs,
            "effective_config": effective_config,
            "response_summary": {},
            "active_run_folder": None,
            "reused_latest_run": False,
            "return_code": None,
            "error_message": None,
            "started_at": now,
            "completed_at": None,
            "created_at": now,
            "updated_at": now,
        }
        self.repository.create_execution(record)
        logger.info("Execution %s created for workflow_id=%s — submitting to thread pool", execution_id, workflow_id)
        self._executor.submit(self._run_execution, execution_id, record)
        return ExecutionSummary.model_validate(self.repository.get_execution(execution_id))

    def list_executions(
        self,
        module_name: str | None,
        workflow_id: str | None,
        status: str | None,
        started_from: str | None,
        started_to: str | None,
        page: int,
        page_size: int,
    ) -> ExecutionPage:
        page_result = self.repository.list_executions(
            ExecutionFilters(
                module_name=module_name,
                workflow_id=workflow_id,
                status=status,
                started_from=started_from,
                started_to=started_to,
            ),
            page,
            page_size,
        )
        return ExecutionPage(
            items=[ExecutionSummary.model_validate(item) for item in page_result["items"]],
            page=page_result["page"],
            page_size=page_result["page_size"],
            total_items=page_result["total_items"],
            total_pages=page_result["total_pages"],
        )

    def get_execution(self, execution_id: str) -> ExecutionDetail | None:
        record = self.repository.get_execution(execution_id)
        return ExecutionDetail.model_validate(record) if record else None

    def _run_execution(self, execution_id: str, record: dict) -> None:
        logger.info("Background execution started: execution_id=%s, workflow=%s",
                     execution_id, record["workflow_selector"])
        req_dto = IngestReqDto()
        for key, value in record["effective_config"].items():
            if key == "workflow_id":
                continue
            req_dto.add_ctx_data(key, value)
        req_dto.add_ctx_data("fetch_again", bool(record["request_payload"].get("fetch_again", False)))

        resp_dto = IngestRespDto()
        exec_ctx_data = ExecCtxData()
        exec_ctx_data.add_ctx_data("workflow_name", record["workflow_selector"])
        exec_ctx_data.add_ctx_data("workflow_selector", record["workflow_selector"])
        exec_ctx_data.add_ctx_data("workflow_parent", record["workflow_parent"])
        exec_ctx_data.add_ctx_data("workflow_child", record["workflow_child"])
        exec_ctx_data.add_ctx_data("workflow_key", record["workflow_selector"])
        exec_ctx_data.add_ctx_data("workflow_id", record["workflow_id"])
        exec_ctx_data.add_ctx_data("workflow_task_registry_path", str(WORKFLOW_TASK_REGISTRY_PATH))
        exec_ctx_data.add_ctx_data("workflow_config", record["effective_config"])
        exec_ctx_data.add_ctx_data("ingest_storage_root", str(DEFAULT_INGEST_STORAGE_BASE / record["workflow_id"]))
        exec_ctx_data.add_ctx_data("execution_id", execution_id)

        # Mark workflow as started in the status DB
        self.status_service.mark_started(
            workflow_id=record["workflow_id"],
            workflow_selector=record["workflow_selector"],
            display_name=record["display_name"],
            execution_id=execution_id,
        )

        try:
            return_code = IngestWfFacade().execute(req_dto, resp_dto, exec_ctx_data)
            status = {0: "COMPLETED", 1: "FAILED", 2: "SKIPPED"}.get(return_code, "FAILED")
            logger.info("Execution %s finished: status=%s, return_code=%d", execution_id, status, return_code)
            response_summary = {
                "workflow": record["workflow_selector"],
                "workflow_id": record["workflow_id"],
                "pages": len(resp_dto.get_ctx_data_by_key("extracted_html_chunks") or {}),
                "chunks_by_method": {
                    method: sum(len(chunks) for chunks in page_chunks.values())
                    for method, page_chunks in (resp_dto.get_ctx_data_by_key("chunk_results_by_method") or {}).items()
                },
            }
            run_folder = resp_dto.get_ctx_data_by_key("active_run_folder")
            self.repository.update_execution(
                execution_id,
                status=status,
                return_code=return_code,
                active_run_folder=run_folder,
                reused_latest_run=bool(resp_dto.get_ctx_data_by_key("reused_latest_run")),
                response_summary=response_summary,
                completed_at=datetime.now().isoformat(timespec="seconds"),
                updated_at=datetime.now().isoformat(timespec="seconds"),
            )

            # Update workflow status and record history
            self.status_service.mark_completed(
                workflow_id=record["workflow_id"],
                return_code=return_code,
                run_folder=run_folder,
                execution_id=execution_id,
                workflow_selector=record["workflow_selector"],
                display_name=record["display_name"],
                summary=response_summary,
            )

            # Invalidate datalake cache
            from app.Api.services.datalake.cache_manager import DatalakeCacheManager
            DatalakeCacheManager().invalidate_workflow(record["workflow_id"])

        except Exception as exc:
            logger.exception("Execution %s failed with exception", execution_id)
            self.repository.update_execution(
                execution_id,
                status="FAILED",
                error_message=str(exc),
                completed_at=datetime.now().isoformat(timespec="seconds"),
                updated_at=datetime.now().isoformat(timespec="seconds"),
            )

            self.status_service.mark_completed(
                workflow_id=record["workflow_id"],
                return_code=1,
                execution_id=execution_id,
                workflow_selector=record["workflow_selector"],
                display_name=record["display_name"],
                error_message=str(exc),
            )

            from app.Api.services.datalake.cache_manager import DatalakeCacheManager
            DatalakeCacheManager().invalidate_workflow(record["workflow_id"])
