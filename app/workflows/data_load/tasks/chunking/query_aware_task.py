import re

from app.common.dtos.exec_ctx_dto import ExecCtxData
from app.common.dtos.ingest_dtos import IngestReqDto
from app.workflows.data_load.tasks.chunking.base_strategy_task import BaseChunkingStrategyTask
from app.workflows.data_load.tasks.chunking.shared import ChunkingSharedUtils


class QueryAwareChunkingTask(BaseChunkingStrategyTask):
    """Query-focused strategy that prioritizes passages near configured terms.

    Example meaning with the Bedrock getting-started content:
    if query terms include "API key" or "SDK", the Step 2 and Step 3 lines are
    prioritized over the AWS account step.
    """

    method_name = "query_aware"

    def build_chunks(self, text: str, reqDto: IngestReqDto, execCtxData: ExecCtxData) -> list[str]:
        """Select term-matching sentences and neighbors; fallback if no matches.

        On the sample content, a query about authentication can pull in the
        "Step 2 - API key" sentence plus nearby support sentences.
        """
        max_tokens = int(reqDto.get_ctx_data_by_key("max_tokens") or 400)
        query_terms = reqDto.get_ctx_data_by_key("query_terms") or []
        lowered_terms = [term.lower().strip() for term in query_terms if term and term.strip()]
        if not lowered_terms:
            return ChunkingSharedUtils.split_by_sentence(text, max_tokens, execCtxData)

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
            return ChunkingSharedUtils.split_by_sentence(text, max_tokens, execCtxData)

        ordered_units = [sentences[idx] for idx in sorted(selected_indexes)]
        return ChunkingSharedUtils.merge_units_by_token_limit(ordered_units, max_tokens, execCtxData)

