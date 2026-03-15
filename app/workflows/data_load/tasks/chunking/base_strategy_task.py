from __future__ import annotations

from app.common.constants.wf_constants import WfReturnCodes
from app.common.dtos.exec_ctx_dto import ExecCtxData
from app.common.dtos.ingest_dtos import IngestReqDto, IngestRespDto
from app.common.interfaces.wf_interfaces import WfTask
from app.workflows.data_load.tasks.chunking.shared import ChunkingSharedUtils


class BaseChunkingStrategyTask(WfTask):
    method_name = "base"

    def __init__(self):
        super().__init__()
        self.task_name = f"CHUNKING_{self.method_name.upper()}"
        self.shared = ChunkingSharedUtils()

    def build_chunks(self, text: str, reqDto: IngestReqDto) -> list[str]:
        raise NotImplementedError

    def execute(self, reqDto: IngestReqDto, respDto: IngestRespDto, execCtxData: ExecCtxData) -> int:
        pages_text_by_url = respDto.get_ctx_data_by_key("crawled_page_text_by_url") or {}
        if not pages_text_by_url:
            respDto.set_status("failed")
            return WfReturnCodes.FAILED

        results = {
            url: self.build_chunks(text, reqDto)
            for url, text in pages_text_by_url.items()
            if text and text.strip()
        }
        respDto.add_ctx_data(f"chunk_result::{self.method_name}", results)
        return WfReturnCodes.SUCCESS

