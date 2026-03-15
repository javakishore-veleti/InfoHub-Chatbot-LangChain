from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
from pathlib import Path
from threading import Lock
from uuid import uuid4

from app.Api.repositories.execution_repository import ExecutionFilters, ExecutionRepository
from app.Api.schemas.execution_schemas import ExecutionDetail, ExecutionPage, ExecutionSummary
from app.Api.services.workflow_config_service import build_effective_config
from app.common.app_constants import DEFAULT_INGEST_STORAGE_BASE, DEFAULT_STATUS_FILE, STATUS_TEMPLATE_PATH, WORKFLOW_TASK_REGISTRY_PATH
from app.common.dtos.exec_ctx_dto import ExecCtxData
from app.common.dtos.ingest_dtos import IngestReqDto, IngestRespDto
from app.workflows.data_load.ingest_wf_facade import IngestWfFacade


class ExecutionService:
    """Background execution orchestration for workflow runs requested by the portal."""

    _executor = ThreadPoolExecutor(max_workers=4)
    _status_file_lock = Lock()

    def __init__(self):
        self.repository = ExecutionRepository()

    def submit_ingest_run(self, workflow_selector: str, inputs: dict) -> ExecutionSummary:
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
        req_dto = IngestReqDto()
        for key, value in record["effective_config"].items():
            if key == "workflow_id":
                continue
            req_dto.add_ctx_data(key, value)
        req_dto.add_ctx_data("fetch_again", bool(record["request_payload"].get("fetch_again", False)))

        resp_dto = IngestRespDto()
        data_engg_status_json = self._load_data_engineering_status(DEFAULT_STATUS_FILE)
        exec_ctx_data = ExecCtxData()
        exec_ctx_data.add_ctx_data("workflow_name", record["workflow_selector"])
        exec_ctx_data.add_ctx_data("workflow_selector", record["workflow_selector"])
        exec_ctx_data.add_ctx_data("workflow_parent", record["workflow_parent"])
        exec_ctx_data.add_ctx_data("workflow_child", record["workflow_child"])
        exec_ctx_data.add_ctx_data("workflow_key", record["workflow_selector"])
        exec_ctx_data.add_ctx_data("workflow_id", record["workflow_id"])
        exec_ctx_data.add_ctx_data("workflow_task_registry_path", str(WORKFLOW_TASK_REGISTRY_PATH))
        exec_ctx_data.add_ctx_data("workflow_config", record["effective_config"])
        exec_ctx_data.add_ctx_data("data_engg_status_json", data_engg_status_json)
        exec_ctx_data.add_ctx_data("data_engg_status_file_path", str(DEFAULT_STATUS_FILE))
        exec_ctx_data.add_ctx_data("ingest_storage_root", str(DEFAULT_INGEST_STORAGE_BASE / record["workflow_id"]))

        try:
            return_code = IngestWfFacade().execute(req_dto, resp_dto, exec_ctx_data)
            status = {0: "COMPLETED", 1: "FAILED", 2: "SKIPPED"}.get(return_code, "FAILED")
            response_summary = {
                "workflow": record["workflow_selector"],
                "workflow_id": record["workflow_id"],
                "pages": len(resp_dto.get_ctx_data_by_key("extracted_html_chunks") or {}),
                "chunks_by_method": {
                    method: sum(len(chunks) for chunks in page_chunks.values())
                    for method, page_chunks in (resp_dto.get_ctx_data_by_key("chunk_results_by_method") or {}).items()
                },
            }
            self.repository.update_execution(
                execution_id,
                status=status,
                return_code=return_code,
                active_run_folder=resp_dto.get_ctx_data_by_key("active_run_folder"),
                reused_latest_run=bool(resp_dto.get_ctx_data_by_key("reused_latest_run")),
                response_summary=response_summary,
                completed_at=datetime.now().isoformat(timespec="seconds"),
                updated_at=datetime.now().isoformat(timespec="seconds"),
            )
        except Exception as exc:
            self.repository.update_execution(
                execution_id,
                status="FAILED",
                error_message=str(exc),
                completed_at=datetime.now().isoformat(timespec="seconds"),
                updated_at=datetime.now().isoformat(timespec="seconds"),
            )
        finally:
            self._save_data_engineering_status(DEFAULT_STATUS_FILE, exec_ctx_data.get_ctx_data_by_key("data_engg_status_json") or {})

    @classmethod
    def _load_data_engineering_status(cls, status_file: Path) -> dict:
        with cls._status_file_lock:
            status_file.parent.mkdir(parents=True, exist_ok=True)
            if status_file.exists():
                try:
                    return json.loads(status_file.read_text(encoding="utf-8"))
                except Exception:
                    pass
            if STATUS_TEMPLATE_PATH.exists():
                payload = json.loads(STATUS_TEMPLATE_PATH.read_text(encoding="utf-8"))
            else:
                payload = {"workflows": {}}
            status_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            return payload

    @classmethod
    def _save_data_engineering_status(cls, status_file: Path, payload: dict) -> None:
        with cls._status_file_lock:
            status_file.parent.mkdir(parents=True, exist_ok=True)
            status_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

