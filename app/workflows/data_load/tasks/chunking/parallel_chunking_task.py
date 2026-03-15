from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.common.constants.wf_constants import WfReturnCodes
from app.common.dtos.exec_ctx_dto import ExecCtxData
from app.common.dtos.ingest_dtos import IngestReqDto, IngestRespDto
from app.common.interfaces.wf_interfaces import WfTask
from app.workflows.data_load.tasks.chunking.base_strategy_task import BaseChunkingStrategyTask
from app.workflows.data_load.tasks.chunking.fixed_token_task import FixedTokenChunkingTask
from app.workflows.data_load.tasks.chunking.hierarchical_task import HierarchicalChunkingTask
from app.workflows.data_load.tasks.chunking.paragraph_section_task import ParagraphSectionChunkingTask
from app.workflows.data_load.tasks.chunking.query_aware_task import QueryAwareChunkingTask
from app.workflows.data_load.tasks.chunking.semantic_task import SemanticChunkingTask
from app.workflows.data_load.tasks.chunking.sentence_task import SentenceChunkingTask
from app.workflows.data_load.tasks.chunking.sliding_window_overlap_task import SlidingWindowOverlapChunkingTask
from app.workflows.data_load.tasks.storage_manager import IngestStorageManager


class ChunkHtmlTextTask(WfTask):
    """Coordinator task that runs selected chunking strategy tasks in parallel.

    Example meaning with the sample Bedrock onboarding text:
    the same content containing the intro, Step 1, Step 2, and Step 3 is passed
    to every strategy once crawl text is ready. Each strategy then produces a
    different chunk view of that same content.
    """

    def __init__(self):
        super().__init__()
        self.task_name = "CHUNK_HTML_TEXT_TASK"

    @staticmethod
    def _strategy_registry() -> dict[str, BaseChunkingStrategyTask]:
        return {
            "fixed_token": FixedTokenChunkingTask(),
            "sliding_window_overlap": SlidingWindowOverlapChunkingTask(),
            "sentence": SentenceChunkingTask(),
            "paragraph_section": ParagraphSectionChunkingTask(),
            "semantic": SemanticChunkingTask(),
            "hierarchical": HierarchicalChunkingTask(),
            "query_aware": QueryAwareChunkingTask(),
        }

    @staticmethod
    def _aliases() -> dict[str, str]:
        return {
            "fixed_token_overlap": "sliding_window_overlap",
            "paragraph": "paragraph_section",
        }

    def _resolve_methods(self, reqDto: IngestReqDto) -> list[str]:
        """Resolve configured methods and normalize backward-compatible aliases."""
        strategy_registry = self._strategy_registry()
        aliases = self._aliases()
        requested_methods = reqDto.get_ctx_data_by_key("chunking_methods") or list(strategy_registry.keys())
        resolved_methods: list[str] = []
        for method in requested_methods:
            canonical = aliases.get(method, method)
            if canonical in strategy_registry and canonical not in resolved_methods:
                resolved_methods.append(canonical)
        return resolved_methods

    def execute(self, reqDto: IngestReqDto, respDto: IngestRespDto, execCtxData: ExecCtxData) -> int:
        """Execute strategy tasks over crawled text, persist outputs, and publish aggregate keys.

        Using the sample Bedrock text as an example:
        - fixed token may split inside Step 2 if the token budget ends there
        - paragraph strategy may keep each step block together
        - query-aware may emphasize Step 2/Step 3 if the query is about API keys or SDKs
        This method coordinates all of those runs on the same input text.
        """
        pages_text_by_url = respDto.get_ctx_data_by_key("crawled_page_text_by_url") or {}
        run_folder_str = respDto.get_ctx_data_by_key("active_run_folder")
        if not pages_text_by_url or not run_folder_str:
            respDto.set_status("failed")
            return WfReturnCodes.FAILED

        methods = self._resolve_methods(reqDto)
        if not methods:
            respDto.set_status("failed")
            return WfReturnCodes.FAILED

        strategy_registry = self._strategy_registry()
        chunk_results_by_method: dict[str, dict[str, list[str]]] = {}

        try:
            with ThreadPoolExecutor(max_workers=min(8, len(methods))) as executor:
                futures = {
                    method: executor.submit(
                        self._build_method_chunks,
                        strategy_registry[method],
                        pages_text_by_url,
                        reqDto,
                        execCtxData,
                    )
                    for method in methods
                }
                for method, future in futures.items():
                    chunk_results_by_method[method] = future.result()

            storage_root = execCtxData.get_ctx_data_by_key("ingest_storage_root")
            storage = IngestStorageManager(Path(storage_root))
            storage.write_chunk_results(Path(run_folder_str), chunk_results_by_method)
        except Exception:
            respDto.set_status("failed")
            return WfReturnCodes.FAILED

        primary_method = "fixed_token" if "fixed_token" in chunk_results_by_method else methods[0]
        respDto.add_ctx_data("chunking_methods_executed", methods)
        respDto.add_ctx_data("chunk_results_by_method", chunk_results_by_method)
        respDto.add_ctx_data("extracted_html_chunks", chunk_results_by_method[primary_method])
        return WfReturnCodes.SUCCESS

    @staticmethod
    def _build_method_chunks(
        strategy_task: BaseChunkingStrategyTask,
        pages_text_by_url: dict[str, str],
        reqDto: IngestReqDto,
        execCtxData: ExecCtxData,
    ) -> dict[str, list[str]]:
        """Build one method result map `{url: [chunks...]}` for all crawled pages."""
        return {
            url: strategy_task.build_chunks(text, reqDto, execCtxData)
            for url, text in pages_text_by_url.items()
            if text and text.strip()
        }

