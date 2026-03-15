from app.common.dtos.ingest_dtos import IngestReqDto
from app.workflows.data_load.tasks.chunking.base_strategy_task import BaseChunkingStrategyTask


class SlidingWindowOverlapChunkingTask(BaseChunkingStrategyTask):
    method_name = "sliding_window_overlap"

    def build_chunks(self, text: str, reqDto: IngestReqDto) -> list[str]:
        max_tokens = int(reqDto.get_ctx_data_by_key("max_tokens") or 400)
        overlap_tokens = int(reqDto.get_ctx_data_by_key("overlap_tokens") or 40)
        return self.shared.split_with_overlap(text, max_tokens, overlap_tokens)

