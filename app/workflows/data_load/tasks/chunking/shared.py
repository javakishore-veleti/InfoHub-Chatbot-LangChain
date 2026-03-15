from __future__ import annotations

import re

import tiktoken


class ChunkingSharedUtils:
    def __init__(self):
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def split_text_by_tokens(self, text: str, max_tokens: int) -> list[str]:
        chunks: list[str] = []
        current_chunk = ""
        for word in text.split():
            candidate_chunk = f"{current_chunk} {word}".strip()
            if len(self.tokenizer.encode(candidate_chunk)) <= max_tokens:
                current_chunk = candidate_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = word
        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    def split_by_sentence(self, text: str, max_tokens: int) -> list[str]:
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.replace("\n", " ")) if part.strip()]
        return self.merge_units_by_token_limit(sentences, max_tokens)

    def split_by_paragraph(self, text: str, max_tokens: int) -> list[str]:
        paragraphs = [part.strip() for part in text.split("\n") if part.strip()]
        return self.merge_units_by_token_limit(paragraphs, max_tokens)

    def split_with_overlap(self, text: str, max_tokens: int, overlap_tokens: int) -> list[str]:
        token_ids = self.tokenizer.encode(text)
        if not token_ids:
            return []
        safe_overlap = min(max(overlap_tokens, 0), max_tokens - 1) if max_tokens > 1 else 0
        step = max(max_tokens - safe_overlap, 1)
        chunks: list[str] = []
        for start in range(0, len(token_ids), step):
            window = token_ids[start:start + max_tokens]
            if not window:
                continue
            chunk = self.tokenizer.decode(window).strip()
            if chunk:
                chunks.append(chunk)
            if start + max_tokens >= len(token_ids):
                break
        return chunks

    def merge_units_by_token_limit(self, units: list[str], max_tokens: int) -> list[str]:
        chunks: list[str] = []
        current_chunk = ""
        for unit in units:
            candidate_chunk = f"{current_chunk} {unit}".strip()
            if len(self.tokenizer.encode(candidate_chunk)) <= max_tokens:
                current_chunk = candidate_chunk
                continue
            if current_chunk:
                chunks.append(current_chunk)
            if len(self.tokenizer.encode(unit)) <= max_tokens:
                current_chunk = unit
            else:
                chunks.extend(self.split_text_by_tokens(unit, max_tokens))
                current_chunk = ""
        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    @staticmethod
    def term_set(text: str) -> set[str]:
        return {token for token in re.findall(r"[a-zA-Z]{3,}", text.lower())}

    @staticmethod
    def jaccard_similarity(left: set[str], right: set[str]) -> float:
        if not left and not right:
            return 1.0
        union = left.union(right)
        if not union:
            return 0.0
        return len(left.intersection(right)) / len(union)

