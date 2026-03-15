from app.common.constants.wf_constants import WfReturnCodes
from app.common.dtos.exec_ctx_dto import ExecCtxData
from app.common.dtos.ingest_dtos import IngestReqDto, IngestRespDto
from app.common.interfaces.wf_interfaces import WfTask
from app.Core.services.workflow_status_service import WorkflowStatusService
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
    def execute(self, reqDto: IngestReqDto, respDto: IngestRespDto, execCtxData: ExecCtxData) -> int:
        status_service = WorkflowStatusService()

        workflow_id = execCtxData.get_ctx_data_by_key("workflow_id") or "ingest_001"
        workflow_selector = execCtxData.get_ctx_data_by_key("workflow_selector") or execCtxData.get_ctx_data_by_key("workflow_name")
        execution_id = execCtxData.get_ctx_data_by_key("execution_id")

        # Check if workflow already completed (skip unless fetch_again=True)
        fetch_again = bool(reqDto.get_ctx_data_by_key("fetch_again"))
        if status_service.is_completed(workflow_id) and not fetch_again:
            respDto.set_status("skipped")
            status_service.mark_skipped(
                workflow_id=workflow_id,
                execution_id=execution_id,
                workflow_selector=workflow_selector,
            )
            return WfReturnCodes.SKIPPED

        # Mark as started
        status_service.mark_started(
            workflow_id=workflow_id,
            workflow_selector=workflow_selector,
            execution_id=execution_id,
        )

        # Execute tasks in order
        for task in self._tasks(execCtxData):
            result = task.execute(reqDto, respDto, execCtxData)
            if result != WfReturnCodes.SUCCESS:
                return result

        return WfReturnCodes.SUCCESS
