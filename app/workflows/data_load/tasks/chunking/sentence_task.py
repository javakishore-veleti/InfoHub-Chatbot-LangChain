from app.common.dtos.exec_ctx_dto import ExecCtxData
from app.common.dtos.ingest_dtos import IngestReqDto
from app.workflows.data_load.tasks.chunking.base_strategy_task import BaseChunkingStrategyTask
from app.workflows.data_load.tasks.chunking.shared import ChunkingSharedUtils


class SentenceChunkingTask(BaseChunkingStrategyTask):
    """Sentence-aware strategy that prefers sentence boundaries over raw token cuts.

    Example meaning with the Bedrock getting-started content:
    the intro sentences stay together, and each step sentence is more likely to
    remain whole instead of being cut mid-sentence.
    """

    method_name = "sentence"

    def build_chunks(self, text: str, reqDto: IngestReqDto, execCtxData: ExecCtxData) -> list[str]:
        """Split into sentences first, then merge by token limit.

        On the sample content, "Step 2 - API key ... authenticate your requests"
        is kept as a natural sentence unit before packing into chunks.
        """
        max_tokens = int(reqDto.get_ctx_data_by_key("max_tokens") or 400)
        return ChunkingSharedUtils.split_by_sentence(text, max_tokens, execCtxData)

