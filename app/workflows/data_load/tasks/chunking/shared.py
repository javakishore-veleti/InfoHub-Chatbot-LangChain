from __future__ import annotations

import re

import tiktoken

from app.common.dtos.exec_ctx_dto import ExecCtxData


class ChunkingSharedUtils:
    """Reusable tokenizer helpers shared by all chunking strategy tasks."""

    @staticmethod
    def get_tokenizer(execCtxData: ExecCtxData):
        """Return cached tokenizer from execution context, creating it once if missing."""
        tokenizer = execCtxData.get_ctx_data_by_key("tokenizer")
        if tokenizer is None:
            tokenizer = tiktoken.get_encoding("cl100k_base")
            execCtxData.add_ctx_data("tokenizer", tokenizer)
        return tokenizer

    @classmethod
    def split_text_by_tokens(cls, text: str, max_tokens: int, execCtxData: ExecCtxData) -> list[str]:
        """Pack words left-to-right into non-overlapping token-limited chunks."""
        tokenizer = cls.get_tokenizer(execCtxData)
        chunks: list[str] = []
        current_chunk = ""
        for word in text.split():
            candidate_chunk = f"{current_chunk} {word}".strip()
            if len(tokenizer.encode(candidate_chunk)) <= max_tokens:
                current_chunk = candidate_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = word
        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    @classmethod
    def split_by_sentence(cls, text: str, max_tokens: int, execCtxData: ExecCtxData) -> list[str]:
        """Split by sentence boundary first, then merge under token limit."""
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.replace("\n", " ")) if part.strip()]
        return cls.merge_units_by_token_limit(sentences, max_tokens, execCtxData)

    @classmethod
    def split_by_paragraph(cls, text: str, max_tokens: int, execCtxData: ExecCtxData) -> list[str]:
        """Split by paragraph/newline units first, then merge under token limit."""
        paragraphs = [part.strip() for part in text.split("\n") if part.strip()]
        return cls.merge_units_by_token_limit(paragraphs, max_tokens, execCtxData)

    @classmethod
    def split_with_overlap(cls, text: str, max_tokens: int, overlap_tokens: int, execCtxData: ExecCtxData) -> list[str]:
        """Create sliding token windows with overlap to preserve boundary context."""
        tokenizer = cls.get_tokenizer(execCtxData)
        token_ids = tokenizer.encode(text)
        if not token_ids:
            return []
        safe_overlap = min(max(overlap_tokens, 0), max_tokens - 1) if max_tokens > 1 else 0
        step = max(max_tokens - safe_overlap, 1)
        chunks: list[str] = []
        for start in range(0, len(token_ids), step):
            window = token_ids[start:start + max_tokens]
            if not window:
                continue
            chunk = tokenizer.decode(window).strip()
            if chunk:
                chunks.append(chunk)
            if start + max_tokens >= len(token_ids):
                break
        return chunks

    @classmethod
    def merge_units_by_token_limit(cls, units: list[str], max_tokens: int, execCtxData: ExecCtxData) -> list[str]:
        """Merge units while within token budget; fallback to token split for very long units."""
        tokenizer = cls.get_tokenizer(execCtxData)
        chunks: list[str] = []
        current_chunk = ""
        for unit in units:
            candidate_chunk = f"{current_chunk} {unit}".strip()
            if len(tokenizer.encode(candidate_chunk)) <= max_tokens:
                current_chunk = candidate_chunk
                continue
            if current_chunk:
                chunks.append(current_chunk)
            if len(tokenizer.encode(unit)) <= max_tokens:
                current_chunk = unit
            else:
                chunks.extend(cls.split_text_by_tokens(unit, max_tokens, execCtxData))
                current_chunk = ""
        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    @staticmethod
    def term_set(text: str) -> set[str]:
        """Build normalized term set used by semantic similarity heuristics."""
        return {token for token in re.findall(r"[a-zA-Z]{3,}", text.lower())}

    @staticmethod
    def jaccard_similarity(left: set[str], right: set[str]) -> float:
        """Compute Jaccard similarity score between two term sets."""
        if not left and not right:
            return 1.0
        union = left.union(right)
        if not union:
            return 0.0
        return len(left.intersection(right)) / len(union)

