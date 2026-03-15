from app.common.dtos.exec_ctx_dto import ExecCtxData
from app.common.dtos.ingest_dtos import IngestReqDto
from app.workflows.data_load.tasks.chunking.base_strategy_task import BaseChunkingStrategyTask
from app.workflows.data_load.tasks.chunking.shared import ChunkingSharedUtils


class ParagraphSectionChunkingTask(BaseChunkingStrategyTask):
    """Structure-aware strategy that groups content by paragraph/section boundaries.

    Example meaning with the Bedrock getting-started content:
    the intro paragraph can become one chunk, "Step 1 - AWS Account" another,
    "Step 2 - API key" another, and "Step 3 - Get the SDK" another.
    """

    method_name = "paragraph_section"

    def build_chunks(self, text: str, reqDto: IngestReqDto, execCtxData: ExecCtxData) -> list[str]:
        """Split by paragraph-like lines and merge units under token limit.

        On the sample content, each step block is a strong candidate to stay as
        its own chunk because the text already has clean paragraph boundaries.
        """
        max_tokens = int(reqDto.get_ctx_data_by_key("max_tokens") or 400)
        return ChunkingSharedUtils.split_by_paragraph(text, max_tokens, execCtxData)

