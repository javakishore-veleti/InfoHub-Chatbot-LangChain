from app.common.dtos.exec_ctx_dto import ExecCtxData
from app.common.dtos.ingest_dtos import IngestReqDto
from app.workflows.data_load.tasks.chunking.base_strategy_task import BaseChunkingStrategyTask
from app.workflows.data_load.tasks.chunking.shared import ChunkingSharedUtils


class HierarchicalChunkingTask(BaseChunkingStrategyTask):
    """Two-level strategy: coarse parent chunks followed by finer child chunks.

    Example meaning with the Bedrock getting-started content:
    a larger parent chunk may contain the intro plus Step 1, then smaller child
    chunks are made from that parent for more precise retrieval.
    """

    method_name = "hierarchical"

    def build_chunks(self, text: str, reqDto: IngestReqDto, execCtxData: ExecCtxData) -> list[str]:
        """Create larger paragraph parents, then re-split into retrieval-size children.

        On the sample content, Step 2 and Step 3 may first be grouped broadly,
        then broken into smaller chunks for downstream search.
        """
        max_tokens = int(reqDto.get_ctx_data_by_key("max_tokens") or 400)
        parent_limit = max(max_tokens * 2, max_tokens)
        parent_chunks = ChunkingSharedUtils.split_by_paragraph(text, parent_limit, execCtxData)
        child_chunks: list[str] = []
        for parent in parent_chunks:
            child_chunks.extend(ChunkingSharedUtils.split_text_by_tokens(parent, max_tokens, execCtxData))
        return child_chunks

