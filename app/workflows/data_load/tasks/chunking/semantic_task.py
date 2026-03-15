import re

from app.common.dtos.ingest_dtos import IngestReqDto
from app.workflows.data_load.tasks.chunking.base_strategy_task import BaseChunkingStrategyTask


class SemanticChunkingTask(BaseChunkingStrategyTask):
    method_name = "semantic"

    def build_chunks(self, text: str, reqDto: IngestReqDto) -> list[str]:
        max_tokens = int(reqDto.get_ctx_data_by_key("max_tokens") or 400)
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.replace("\n", " ")) if part.strip()]
        if not sentences:
            return []

        chunks: list[str] = []
        current_units: list[str] = []
        current_terms: set[str] = set()

        for sentence in sentences:
            sentence_terms = self.shared.term_set(sentence)
            candidate = " ".join(current_units + [sentence]).strip()
            if not current_units:
                current_units = [sentence]
                current_terms = sentence_terms
                continue

            similarity = self.shared.jaccard_similarity(current_terms, sentence_terms)
            candidate_tokens = len(self.shared.tokenizer.encode(candidate))
            should_cut = similarity < 0.15 and candidate_tokens > int(max_tokens * 0.35)

            if candidate_tokens > max_tokens or should_cut:
                chunks.append(" ".join(current_units).strip())
                current_units = [sentence]
                current_terms = sentence_terms
            else:
                current_units.append(sentence)
                current_terms.update(sentence_terms)

        if current_units:
            chunks.append(" ".join(current_units).strip())
        return chunks

