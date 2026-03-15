from datetime import datetime

from app.common.constants.wf_constants import WfReturnCodes
from app.common.dtos.exec_ctx_dto import ExecCtxData
from app.common.dtos.ingest_dtos import IngestReqDto, IngestRespDto
from app.common.interfaces.wf_interfaces import WfTask
from app.workflows.workflow_task_loader import WorkflowTaskLoader


class IngestWfFacade:
    @staticmethod
    def _fallback_task_paths() -> list[str]:
        return [
            "app.workflows.data_load.tasks.extract_html_files:CrawlHtmlFilesTask",
            "app.workflows.data_load.tasks.chunking.parallel_chunking_task:ChunkHtmlTextTask",
        ]

    @classmethod
    def _tasks(cls, execCtxData: ExecCtxData) -> list[WfTask]:
        workflow_name = execCtxData.get_ctx_data_by_key("workflow_selector") or execCtxData.get_ctx_data_by_key("workflow_name") or "ingest/AWSBedrock"
        registry_path = execCtxData.get_ctx_data_by_key("workflow_task_registry_path")
        if not registry_path:
            task_paths = cls._fallback_task_paths()
            tasks = WorkflowTaskLoader.instantiate_task_paths(task_paths)
            execCtxData.add_ctx_data("resolved_workflow_task_paths", task_paths)
            return tasks

        try:
            tasks, task_paths = WorkflowTaskLoader.load_tasks(
                workflow_name=workflow_name,
                registry_path=registry_path,
                fallback_task_paths=cls._fallback_task_paths(),
            )
        except FileNotFoundError:
            task_paths = cls._fallback_task_paths()
            tasks = WorkflowTaskLoader.instantiate_task_paths(task_paths)

        execCtxData.add_ctx_data("resolved_workflow_task_paths", task_paths)
        return tasks

    # noinspection PyPep8Naming
    def execute(self, reqDto:IngestReqDto, respDto: IngestRespDto, execCtxData: ExecCtxData) -> int:
        status_json = execCtxData.get_ctx_data_by_key("data_engg_status_json") or {}
        workflows_status = status_json.setdefault("workflows", {})
        workflow_id = execCtxData.get_ctx_data_by_key("workflow_id") or execCtxData.get_ctx_data_by_key("workflow_name") or "ingest_001"
        workflow_selector = execCtxData.get_ctx_data_by_key("workflow_selector") or execCtxData.get_ctx_data_by_key("workflow_name")

        if workflow_id not in workflows_status and workflow_selector in workflows_status:
            workflows_status[workflow_id] = workflows_status.pop(workflow_selector)

        ingest_status = workflows_status.setdefault(workflow_id, {})

        fetch_again = bool(reqDto.get_ctx_data_by_key("fetch_again"))
        if ingest_status.get("completed") and not fetch_again:
            respDto.set_status("skipped")
            return WfReturnCodes.SKIPPED

        ingest_status["last_started_at"] = datetime.now().isoformat(timespec="seconds")
        ingest_status["completed"] = False

        for task in self._tasks(execCtxData):
            result = task.execute(reqDto, respDto, execCtxData)
            if result != WfReturnCodes.SUCCESS:
                ingest_status["last_completed_at"] = datetime.now().isoformat(timespec="seconds")
                ingest_status["completed"] = False
                ingest_status["last_return_code"] = result
                return result

        ingest_status["last_completed_at"] = datetime.now().isoformat(timespec="seconds")
        ingest_status["completed"] = True
        ingest_status["last_return_code"] = WfReturnCodes.SUCCESS
        return WfReturnCodes.SUCCESS