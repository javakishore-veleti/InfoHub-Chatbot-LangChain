from __future__ import annotations

import logging

from app.common.constants.wf_constants import WfReturnCodes
from app.common.dtos.exec_ctx_dto import ExecCtxData
from app.common.dtos.ingest_dtos import IngestReqDto, IngestRespDto
from app.common.interfaces.wf_interfaces import WfTask

logger = logging.getLogger(__name__)


class BaseChunkingStrategyTask(WfTask):
    """Base workflow task for chunking one page text map with one strategy."""

    method_name = "base"

    def __init__(self):
        super().__init__()
        self.task_name = f"CHUNKING_{self.method_name.upper()}"

    def build_chunks(self, text: str, reqDto: IngestReqDto, execCtxData: ExecCtxData) -> list[str]:
        """Return chunks for one document text using strategy-specific logic."""
        raise NotImplementedError

    def execute(self, reqDto: IngestReqDto, respDto: IngestRespDto, execCtxData: ExecCtxData) -> int:
        """Apply this strategy to all crawled pages and store method-scoped output in response context."""
        pages_text_by_url = respDto.get_ctx_data_by_key("crawled_page_text_by_url") or {}
        if not pages_text_by_url:
            respDto.set_status("failed")
            return WfReturnCodes.FAILED

        results: dict[str, list[str]] = {}
        for url, text in pages_text_by_url.items():
            if text and text.strip():
                chunks = self.build_chunks(text, reqDto, execCtxData)
                results[url] = chunks
                logger.debug("[%s] Chunked %s → %d chunks", self.method_name, url, len(chunks))

        respDto.add_ctx_data(f"chunk_result::{self.method_name}", results)
        return WfReturnCodes.SUCCESS

