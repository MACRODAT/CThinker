# Ingest Query Lint

## Summary

The operating loop of the vault has three recurring actions: ingest sources, answer questions against the wiki, and periodically lint the wiki for quality and gaps.

## Details

### Ingest

- Read a new raw source.
- Summarize it into a source page.
- Update affected concept, entity, and synthesis pages.
- Refresh `index.md` and append to `log.md`.

### Query

- Search the existing wiki first.
- Synthesize an answer from relevant pages.
- Save valuable answers back into the wiki as durable artifacts.

### Lint

- Identify contradictions, stale claims, orphan pages, and missing cross-links.
- Suggest further research or missing source material.
- Record maintenance output as a durable meta page when useful.

## Operating Principle

Questions and ingests both improve the wiki. The vault is not passive storage; it is an actively maintained knowledge structure.

## Links

- Related: [[wiki/concepts/llm-wiki]], [[wiki/concepts/schema-index-log]]
- Sources: [[wiki/sources/2026-04-16-llm-wiki-idea]]

## Sources

- [[wiki/sources/2026-04-16-llm-wiki-idea]]
