from __future__ import annotations

import logging
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


logger = logging.getLogger(__name__)


class ChunkHtmlTextTask(WfTask):
    """Coordinator task that runs selected chunking strategy tasks in parallel."""

    def __init__(self):
        super().__init__()
        self.task_name = "CHUNK_HTML_TEXT_TASK"

    @staticmethod
    def _strategy_registry() -> dict[str, BaseChunkingStrategyTask]:
        # Each key is the canonical strategy name used in config and JSON output.
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
        # Backward-compatible config names still accepted from older configs.
        # Example: "fixed_token_overlap" is normalized to "sliding_window_overlap".
        return {
            "fixed_token_overlap": "sliding_window_overlap",
            "paragraph": "paragraph_section",
        }

    def _resolve_methods(self, reqDto: IngestReqDto) -> list[str]:
        """Resolve configured methods and normalize backward-compatible aliases."""
        strategy_registry = self._strategy_registry()
        aliases = self._aliases()
        # If config omits chunking_methods, run every registered strategy.
        requested_methods = reqDto.get_ctx_data_by_key("chunking_methods") or list(strategy_registry.keys())
        resolved_methods: list[str] = []
        for method in requested_methods:
            canonical = aliases.get(method, method)
            # Keep the final list unique and canonical so storage folders stay predictable.
            if canonical in strategy_registry and canonical not in resolved_methods:
                resolved_methods.append(canonical)
        return resolved_methods

    def execute(self, reqDto: IngestReqDto, respDto: IngestRespDto, execCtxData: ExecCtxData) -> int:
        """Execute strategy tasks over crawled text, persist outputs, and publish aggregate keys."""
        logger.info("ChunkHtmlTextTask starting")
        pages_text_by_url = respDto.get_ctx_data_by_key("crawled_page_text_by_url") or {}
        run_folder_str = respDto.get_ctx_data_by_key("active_run_folder")
        if not pages_text_by_url or not run_folder_str:
            logger.warning("No crawled pages or run folder — cannot chunk")
            respDto.set_status("failed")
            return WfReturnCodes.FAILED

        methods = self._resolve_methods(reqDto)
        if not methods:
            logger.warning("No chunking methods resolved")
            respDto.set_status("failed")
            return WfReturnCodes.FAILED

        logger.info("Running %d chunking strategies in parallel: %s", len(methods), methods)

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
                    total_chunks = sum(len(c) for c in chunk_results_by_method[method].values())
                    logger.info("Strategy '%s' produced %d chunks across %d pages",
                                method, total_chunks, len(chunk_results_by_method[method]))

            storage_root = execCtxData.get_ctx_data_by_key("ingest_storage_root")
            storage = IngestStorageManager(Path(storage_root))
            storage.write_chunk_results(Path(run_folder_str), chunk_results_by_method)
            logger.info("Chunk results persisted to %s", run_folder_str)
        except Exception:
            logger.exception("ChunkHtmlTextTask failed")
            respDto.set_status("failed")
            return WfReturnCodes.FAILED

        # Keep one backward-compatible "primary" result map for simple summaries/older code.
        # Current preference is fixed_token when available.
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
        # Example output for paragraph_section on AWSBedrock docs:
        # one URL may become chunks like ["intro paragraph...", "Step 1...", "Step 2..."]
        return {
            url: strategy_task.build_chunks(text, reqDto, execCtxData)
            for url, text in pages_text_by_url.items()
            if text and text.strip()
        }

