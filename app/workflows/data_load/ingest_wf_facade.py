from datetime import datetime

from app.common.constants.wf_constants import WfReturnCodes
from app.common.dtos.exec_ctx_dto import ExecCtxData
from app.common.dtos.ingest_dtos import IngestReqDto, IngestRespDto
from app.common.interfaces.wf_interfaces import WfTask
from app.workflows.workflow_task_loader import WorkflowTaskLoader


class IngestWfFacade:
    @staticmethod
    def _fallback_task_paths() -> list[str]:
        # Safety fallback if the external task registry is missing.
        # Example for AWS Bedrock ingest: crawl docs first, then run chunking strategies.
        return [
            "app.workflows.data_load.tasks.extract_html_files:CrawlHtmlFilesTask",
            "app.workflows.data_load.tasks.chunking.parallel_chunking_task:ChunkHtmlTextTask",
        ]

    @classmethod
    def _tasks(cls, execCtxData: ExecCtxData) -> list[WfTask]:
        # Human-readable workflow selector used for task lookup.
        # Example: "ingest/AWSBedrock".
        workflow_name = execCtxData.get_ctx_data_by_key("workflow_selector") or execCtxData.get_ctx_data_by_key("workflow_name") or "ingest/AWSBedrock"

        # Path to the JSON registry that maps workflow names to task class paths.
        registry_path = execCtxData.get_ctx_data_by_key("workflow_task_registry_path")
        if not registry_path:
            # If no registry path is available, use the built-in fallback task list.
            task_paths = cls._fallback_task_paths()
            tasks = WorkflowTaskLoader.instantiate_task_paths(task_paths)
            execCtxData.add_ctx_data("resolved_workflow_task_paths", task_paths)
            return tasks

        try:
            # Normal path: resolve tasks from the external registry.
            # Example resolved list for AWS Bedrock ingest:
            # ["...:CrawlHtmlFilesTask", "...:ChunkHtmlTextTask"]
            tasks, task_paths = WorkflowTaskLoader.load_tasks(
                workflow_name=workflow_name,
                registry_path=registry_path,
                fallback_task_paths=cls._fallback_task_paths(),
            )
        except FileNotFoundError:
            # Registry file missing at runtime -> recover with fallback tasks.
            task_paths = cls._fallback_task_paths()
            tasks = WorkflowTaskLoader.instantiate_task_paths(task_paths)

        # Store the resolved task paths in execution context for debugging / observability.
        execCtxData.add_ctx_data("resolved_workflow_task_paths", task_paths)
        return tasks

    # noinspection PyPep8Naming
    def execute(self, reqDto:IngestReqDto, respDto: IngestRespDto, execCtxData: ExecCtxData) -> int:
        # Shared mutable workflow status JSON loaded earlier in app startup.
        status_json = execCtxData.get_ctx_data_by_key("data_engg_status_json") or {}
        workflows_status = status_json.setdefault("workflows", {})

        # Stable runtime-safe ID used for status and storage.
        # Example: AWSBedrock child workflow maps to "ingest_001".
        workflow_id = execCtxData.get_ctx_data_by_key("workflow_id") or execCtxData.get_ctx_data_by_key("workflow_name") or "ingest_001"

        # Human-readable selector is still useful for migration/debugging.
        # Example: "ingest/AWSBedrock".
        workflow_selector = execCtxData.get_ctx_data_by_key("workflow_selector") or execCtxData.get_ctx_data_by_key("workflow_name")

        # Backward-compatibility migration:
        # if older status used "ingest/AWSBedrock" as key, move it to "ingest_001".
        if workflow_id not in workflows_status and workflow_selector in workflows_status:
            workflows_status[workflow_id] = workflows_status.pop(workflow_selector)

        # Get or initialize status bucket for this workflow id.
        ingest_status = workflows_status.setdefault(workflow_id, {})

        # "fetch_again=true" means force a fresh crawl/chunk run even if this workflow already completed.
        # Example: user wants a brand-new AWS Bedrock ingest timestamp folder.
        fetch_again = bool(reqDto.get_ctx_data_by_key("fetch_again"))
        if ingest_status.get("completed") and not fetch_again:
            respDto.set_status("skipped")
            return WfReturnCodes.SKIPPED

        # Mark workflow as started before executing individual tasks.
        ingest_status["last_started_at"] = datetime.now().isoformat(timespec="seconds")
        ingest_status["completed"] = False

        # Execute tasks in order.
        # For AWS Bedrock this usually means:
        # 1. crawl allowed docs pages once
        # 2. apply multiple chunking strategies on the crawled text
        for task in self._tasks(execCtxData):
            result = task.execute(reqDto, respDto, execCtxData)
            if result != WfReturnCodes.SUCCESS:
                # Capture failure details immediately so status file reflects the partial run.
                ingest_status["last_completed_at"] = datetime.now().isoformat(timespec="seconds")
                ingest_status["completed"] = False
                ingest_status["last_return_code"] = result
                return result

        # All tasks finished successfully; mark workflow complete.
        ingest_status["last_completed_at"] = datetime.now().isoformat(timespec="seconds")
        ingest_status["completed"] = True
        ingest_status["last_return_code"] = WfReturnCodes.SUCCESS
        return WfReturnCodes.SUCCESS