import re

from app.common.dtos.ingest_dtos import IngestReqDto
from app.workflows.data_load.tasks.chunking.base_strategy_task import BaseChunkingStrategyTask


class QueryAwareChunkingTask(BaseChunkingStrategyTask):
    method_name = "query_aware"

    def build_chunks(self, text: str, reqDto: IngestReqDto) -> list[str]:
        max_tokens = int(reqDto.get_ctx_data_by_key("max_tokens") or 400)
        query_terms = reqDto.get_ctx_data_by_key("query_terms") or []
        lowered_terms = [term.lower().strip() for term in query_terms if term and term.strip()]
        if not lowered_terms:
            return self.shared.split_by_sentence(text, max_tokens)

        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.replace("\n", " ")) if part.strip()]
        if not sentences:
            return []

        selected_indexes: set[int] = set()
        for idx, sentence in enumerate(sentences):
            lowered_sentence = sentence.lower()
            if any(term in lowered_sentence for term in lowered_terms):
                selected_indexes.add(idx)
                if idx > 0:
                    selected_indexes.add(idx - 1)
                if idx < len(sentences) - 1:
                    selected_indexes.add(idx + 1)

        if not selected_indexes:
            return self.shared.split_by_sentence(text, max_tokens)

        ordered_units = [sentences[idx] for idx in sorted(selected_indexes)]
        return self.shared.merge_units_by_token_limit(ordered_units, max_tokens)

