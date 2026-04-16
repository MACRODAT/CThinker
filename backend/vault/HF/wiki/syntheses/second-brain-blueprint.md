# Second Brain Blueprint

## Summary

This vault implements the LLM Wiki pattern as a practical personal second brain: immutable source storage, an LLM-maintained wiki, explicit operating rules, and a repeatable ingest/query/lint workflow.

## Concrete Design

- Raw material is separated from maintained knowledge.
- The agent updates durable markdown pages rather than leaving insights trapped in chat.
- `Agents.md` defines how the agent behaves every session.
- `index.md` provides the top-level map of the wiki.
- `log.md` preserves the timeline of what the vault learned and when.

## Recommended Working Loop

1. Drop new material into `raw/inbox/`.
2. Ask the agent to ingest one source at a time.
3. Review the created source page and updated concept pages.
4. Ask questions against the wiki and preserve valuable answers.
5. Run periodic lint passes to find gaps and stale pages.

## Why This Is A Second Brain

- It externalizes memory into durable linked notes.
- It accumulates synthesis over time.
- It reduces repeated rediscovery work.
- It keeps a history of both sources and thinking artifacts.

## Links

- Related: [[Agents]], [[index]], [[log]], [[wiki/meta/folder-conventions]]
- Concepts: [[wiki/concepts/llm-wiki]], [[wiki/concepts/ingest-query-lint]], [[wiki/concepts/schema-index-log]]
- Sources: [[wiki/sources/2026-04-16-llm-wiki-idea]]

## Sources

- [[wiki/sources/2026-04-16-llm-wiki-idea]]
