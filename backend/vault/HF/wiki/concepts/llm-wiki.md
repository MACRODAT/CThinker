# LLM Wiki

## Summary

An LLM wiki is a persistent markdown knowledge base maintained by an LLM over time. It differs from standard RAG because synthesis is accumulated into durable pages instead of being rediscovered from raw documents for every query.

## Details

- The central artifact is the wiki itself, not transient chat output.
- New sources are integrated into existing pages, not merely indexed for retrieval.
- The wiki compounds: cross-links, contradictions, summaries, and evolving interpretations accumulate with each ingest.
- The human role is source curation, direction, and interpretation.
- The agent role is summarization, filing, linking, maintenance, and consistency updates across many pages.

## Why It Matters

- Repeated synthesis work is amortized.
- The knowledge base gets more useful over time instead of staying flat.
- Obsidian becomes the browsing interface while the LLM acts as the maintainer.

## Links

- Related: [[wiki/concepts/ingest-query-lint]], [[wiki/concepts/schema-index-log]], [[wiki/syntheses/second-brain-blueprint]]
- Sources: [[wiki/sources/2026-04-16-llm-wiki-idea]]

## Sources

- [[wiki/sources/2026-04-16-llm-wiki-idea]]
