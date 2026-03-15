import re

from app.common.dtos.exec_ctx_dto import ExecCtxData
from app.common.dtos.ingest_dtos import IngestReqDto
from app.workflows.data_load.tasks.chunking.base_strategy_task import BaseChunkingStrategyTask
from app.workflows.data_load.tasks.chunking.shared import ChunkingSharedUtils


class SemanticChunkingTask(BaseChunkingStrategyTask):
    """Semantic-ish strategy that cuts chunks when topic similarity drops.

    Example meaning with the Bedrock getting-started content:
    the general introduction is one topic, AWS account setup is another, API key
    creation is another, and SDK installation is another.
    """

    method_name = "semantic"

    def build_chunks(self, text: str, reqDto: IngestReqDto, execCtxData: ExecCtxData) -> list[str]:
        """Use sentence token budget + term similarity to detect topic shifts.

        On the sample content, a topic change from "Step 1 - AWS Account" to
        "Step 2 - API key" is likely to trigger a new chunk.
        """
        max_tokens = int(reqDto.get_ctx_data_by_key("max_tokens") or 400)
        tokenizer = ChunkingSharedUtils.get_tokenizer(execCtxData)
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.replace("\n", " ")) if part.strip()]
        if not sentences:
            return []

        chunks: list[str] = []
        current_units: list[str] = []
        current_terms: set[str] = set()

        for sentence in sentences:
            sentence_terms = ChunkingSharedUtils.term_set(sentence)
            candidate = " ".join(current_units + [sentence]).strip()
            if not current_units:
                current_units = [sentence]
                current_terms = sentence_terms
                continue

            similarity = ChunkingSharedUtils.jaccard_similarity(current_terms, sentence_terms)
            candidate_tokens = len(tokenizer.encode(candidate))
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



