# LLM Wiki Idea

## Summary

- `raw.md` proposes replacing query-time-only retrieval with a persistent LLM-maintained markdown wiki.
- The system has three layers: immutable raw sources, an LLM-authored wiki, and a schema that governs behavior.
- The core operating loop is ingest, query, and lint.
- `index.md` and `log.md` are essential control files for navigation and chronology.
- Obsidian is positioned as the browsing interface while the LLM performs maintenance work.

## Source Details

- Source file: `raw.md`
- Source type: idea/spec note
- Ingest date: 2026-04-16
- Confidence: high for intent, since this is the seed specification for the vault

## Key Claims

1. A maintained wiki compounds knowledge better than repeatedly reconstructing answers from raw sources.
2. The LLM should own the bookkeeping layer: summarization, cross-linking, updates, and contradiction tracking.
3. Good query outputs should be filed back into the wiki as durable pages.
4. A lightweight markdown-native workflow can work well without full RAG infrastructure at moderate scale.

## Implications For This Vault

- The wiki should be treated as the primary working knowledge layer.
- Each ingest should update multiple related pages, not only create a one-off summary.
- The schema must be explicit enough to keep future sessions disciplined.
- The vault should remain readable and navigable in plain markdown and Obsidian.

## Open Questions

- Whether future pages should standardize on frontmatter for Dataview support.
- At what size the vault will need a dedicated local search tool.

## Links

- Concepts: [[wiki/concepts/llm-wiki]], [[wiki/concepts/ingest-query-lint]], [[wiki/concepts/schema-index-log]]
- Synthesis: [[wiki/syntheses/second-brain-blueprint]]
- Raw source: `raw.md`

## Sources

- `raw.md`
