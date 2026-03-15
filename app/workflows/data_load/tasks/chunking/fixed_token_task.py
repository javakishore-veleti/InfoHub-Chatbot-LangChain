from app.common.dtos.exec_ctx_dto import ExecCtxData
from app.common.dtos.ingest_dtos import IngestReqDto
from app.workflows.data_load.tasks.chunking.base_strategy_task import BaseChunkingStrategyTask
from app.workflows.data_load.tasks.chunking.shared import ChunkingSharedUtils


class FixedTokenChunkingTask(BaseChunkingStrategyTask):
    """Baseline strategy: split text into non-overlapping token-limited chunks.

    Example meaning with the Bedrock getting-started content:
    the intro plus part of "Step 1 - AWS Account" may end up in one chunk,
    then the rest of Step 1 and part of "Step 2 - API key" may go into the next.
    This strategy only cares about token size, not step boundaries.
    """

    method_name = "fixed_token"

    def build_chunks(self, text: str, reqDto: IngestReqDto, execCtxData: ExecCtxData) -> list[str]:
        """Use configured max token size and pack words left-to-right.

        On the sample content, this can split in the middle of Step 2 or Step 3
        if the token limit is reached there.
        """
        max_tokens = int(reqDto.get_ctx_data_by_key("max_tokens") or 400)
        return ChunkingSharedUtils.split_text_by_tokens(text, max_tokens, execCtxData)

