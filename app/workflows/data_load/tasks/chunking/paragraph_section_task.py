from app.common.dtos.ingest_dtos import IngestReqDto
from app.workflows.data_load.tasks.chunking.base_strategy_task import BaseChunkingStrategyTask


class ParagraphSectionChunkingTask(BaseChunkingStrategyTask):
    method_name = "paragraph_section"

    def build_chunks(self, text: str, reqDto: IngestReqDto) -> list[str]:
        max_tokens = int(reqDto.get_ctx_data_by_key("max_tokens") or 400)
        return self.shared.split_by_paragraph(text, max_tokens)

