# Ingest Chunking Guide

![Ingest workflow architecture](Docs/Images/Ingest/01_ingest_workflow_architecture.png)

## Ingest task map

- `IngestWfFacade`: orchestrates task order, checks workflow status, and skips completed runs unless fetch is forced.
- `CrawlHtmlFilesTask`: crawls Bedrock docs once, extracts readable text, and decides whether to reuse latest data or fetch again.
- `ChunkHtmlTextTask`: runs chunking strategy tasks in parallel after crawl text is ready.
- `IngestStorageManager`: persists crawled pages, per-strategy chunk outputs, and latest run pointer.
- `ExecCtxData`: shares runtime context between facade and tasks (storage root, status json, paths).
- `ExtractHtmlFilesTask`: compatibility wrapper that executes crawl then chunk tasks.

## What this project does

- Starts from a seed documentation page.
- Crawls related links from the same documentation area.
- Extracts readable text from each page. This means the human-visible words people read (titles, headings, paragraphs, bullets, and table text), while ignoring markup and page code.
- How we decide it is readable: if a page returns normal language text after cleanup (not just scripts, styling, or empty structure), it is used for chunking; otherwise it is skipped.
- Splits text into token-sized chunks.

## How chunking is done here

- Text is split word-by-word.
- A chunk grows until adding one more word would pass the token limit.
- When the limit is reached, a new chunk starts.
- Each page produces multiple chunks, all kept in original reading order.
- The crawl stage is done once; all chunking strategies reuse the same extracted page text.

## Why this approach

- Keeps each chunk small enough for LLM context windows.
- Improves retrieval precision compared to sending whole pages.
- Reduces prompt cost and latency.
- Preserves flow better than random fixed character cuts.

## Practical tradeoffs

- Very simple and reliable.
- Fast to run at scale.
- Can break context at arbitrary sentence boundaries.
- No overlap means edge facts near boundaries can be harder to retrieve. In simple terms, when one idea ends at the bottom of one chunk and continues in the next chunk, a search may fetch only one side and miss the full meaning.

## Common industry chunking strategies

- **Fixed-size token chunking**: simple blocks by token count; fast baseline.
- **Sliding window with overlap**: repeated context across chunks; better recall near boundaries.
- **Sentence-based chunking**: splits on sentence endings; more natural semantics.
- **Paragraph/section chunking**: aligns with headings and document structure.
- **Semantic chunking**: uses embeddings or similarity shifts to split where topic changes.
- **Hierarchical chunking**: large parent chunks + smaller child chunks for multi-stage retrieval.
- **Query-aware chunking**: creates chunks dynamically based on user intent or domain rules.

## Strategy tasks implemented

- `fixed_token`: baseline fixed token windows.
- `sliding_window_overlap`: token windows with overlap to preserve boundary continuity.
- `sentence`: sentence-first grouping, then merge by token limit.
- `paragraph_section`: paragraph/section-first grouping, then merge by token limit.
- `semantic`: topic-shift aware splitting using sentence-term similarity heuristics.
- `hierarchical`: parent chunks first, then child chunks for finer retrieval.
- `query_aware`: prioritizes lines related to configured query terms plus neighbors.

Aliases accepted in config:

- `fixed_token_overlap` -> `sliding_window_overlap`
- `paragraph` -> `paragraph_section`

## Strategy quick view

| Strategy | Quality | Speed | Cost | Best for |
|---|---|---|---|---|
| Fixed-size token | Medium | Very High | Low | Fast MVP and baseline RAG |
| Sliding window overlap | Medium-High | High | Medium | Better recall near chunk boundaries |
| Sentence-based | High | High | Medium | Q&A over prose-heavy docs |
| Paragraph/section | High | Medium-High | Medium | Technical docs with clear structure |
| Semantic | High | Medium | Medium-High | Topic-dense mixed-content documents |
| Hierarchical | Very High | Medium | High | Large enterprise knowledge bases |
| Query-aware | Very High | Medium-Low | High | Specialized domains and adaptive retrieval |

## Practical default

- Start with fixed-size token chunks.
- Add 10-20% overlap if retrieval misses boundary facts. This repeats a small part of the previous chunk in the next chunk so connected sentences stay visible together during retrieval.
- Move to section-aware or semantic chunking when answer quality plateaus. Plateau means answers stop getting better even after basic tuning, so smarter splitting based on document structure or meaning is needed.

## When to use which

- Start with fixed token chunking for speed and simplicity.
- Add overlap when factual continuity is important. Use this when one fact depends on the sentence before or after it, such as steps, warnings, limitations, or comparisons.
- Use structure-aware or semantic chunking for long technical docs.
- Use hierarchical chunking for enterprise-scale corpora and complex QA.

## Recommended next evolution

- Add small overlap (for example 10-20%) to improve boundary recall. Boundary recall means finding facts that sit near chunk edges, which are the easiest details to lose without overlap.
- Keep headings with nearby text to preserve context.
- Track retrieval metrics (precision, recall, answer quality) before and after changes.

