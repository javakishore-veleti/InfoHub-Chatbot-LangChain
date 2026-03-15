from app.common.dtos.exec_ctx_dto import ExecCtxData
from app.common.dtos.ingest_dtos import IngestReqDto
from app.workflows.data_load.tasks.chunking.base_strategy_task import BaseChunkingStrategyTask
from app.workflows.data_load.tasks.chunking.shared import ChunkingSharedUtils


class SlidingWindowOverlapChunkingTask(BaseChunkingStrategyTask):
    """Sliding-window strategy with overlap to keep boundary context between chunks.

    Example meaning with the Bedrock getting-started content:
    if one chunk ends near "Step 2 - API key", the next chunk repeats some of
    those ending tokens so the API key explanation is visible in both chunks.
    """

    method_name = "sliding_window_overlap"

    def build_chunks(self, text: str, reqDto: IngestReqDto, execCtxData: ExecCtxData) -> list[str]:
        """Build overlapping token windows using max_tokens and overlap_tokens.

        On the sample content, the end of Step 1 can be repeated at the start of
        the next chunk so step continuity is not lost.
        """
        max_tokens = int(reqDto.get_ctx_data_by_key("max_tokens") or 400)
        overlap_tokens = int(reqDto.get_ctx_data_by_key("overlap_tokens") or 40)
        return ChunkingSharedUtils.split_with_overlap(text, max_tokens, overlap_tokens, execCtxData)

