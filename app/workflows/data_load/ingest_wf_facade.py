from datetime import datetime

from app.common.constants.wf_constants import WfReturnCodes
from app.common.dtos.exec_ctx_dto import ExecCtxData
from app.common.dtos.ingest_dtos import IngestReqDto, IngestRespDto
from app.common.interfaces.wf_interfaces import WfTask
from app.workflows.data_load.tasks.extract_html_files import CrawlHtmlFilesTask, ChunkHtmlTextTask


class IngestWfFacade:
    @staticmethod
    def _tasks() -> list[WfTask]:
        return [
            CrawlHtmlFilesTask(),
            ChunkHtmlTextTask(),
        ]

    # noinspection PyPep8Naming
    def execute(self, reqDto:IngestReqDto, respDto: IngestRespDto, execCtxData: ExecCtxData) -> int:
        status_json = execCtxData.get_ctx_data_by_key("data_engg_status_json") or {}
        workflows_status = status_json.setdefault("workflows", {})
        ingest_status = workflows_status.setdefault("ingest", {})

        fetch_again = bool(reqDto.get_ctx_data_by_key("fetch_again"))
        if ingest_status.get("completed") and not fetch_again:
            respDto.set_status("skipped")
            return WfReturnCodes.SKIPPED

        ingest_status["last_started_at"] = datetime.now().isoformat(timespec="seconds")
        ingest_status["completed"] = False

        for task in self._tasks():
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