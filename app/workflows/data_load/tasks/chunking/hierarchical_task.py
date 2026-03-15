from app.common.dtos.ingest_dtos import IngestReqDto
from app.workflows.data_load.tasks.chunking.base_strategy_task import BaseChunkingStrategyTask


class HierarchicalChunkingTask(BaseChunkingStrategyTask):
    method_name = "hierarchical"

    def build_chunks(self, text: str, reqDto: IngestReqDto) -> list[str]:
        max_tokens = int(reqDto.get_ctx_data_by_key("max_tokens") or 400)
        parent_limit = max(max_tokens * 2, max_tokens)
        parent_chunks = self.shared.split_by_paragraph(text, parent_limit)
        child_chunks: list[str] = []
        for parent in parent_chunks:
            child_chunks.extend(self.shared.split_text_by_tokens(parent, max_tokens))
        return child_chunks

