# Agents.md

This vault is an LLM-maintained wiki. The human curates sources and asks questions. The agent reads sources, writes and maintains the wiki, and keeps structure consistent over time.

## Mission

Build and maintain a persistent, compounding markdown wiki that sits between raw source documents and downstream questions. Do not answer from raw material when the answer should first be compiled into the wiki.

## Operating Model

There are three layers:

1. `raw/` contains immutable source documents. Read from this layer. Do not modify files in it after ingest unless the human explicitly asks.
2. `wiki/` contains LLM-authored markdown pages. The agent owns this layer and may create, update, merge, and cross-link pages.
3. Root control files define behavior and navigation:
   - `Agents.md`: this schema
   - `index.md`: content-oriented catalog of the wiki
   - `log.md`: append-only chronological operations log

## Folder Conventions

Use this structure unless the human later changes it:

- `raw/inbox/`: newly dropped sources waiting for ingest
- `raw/library/`: ingested raw sources kept as source-of-truth files
- `raw/assets/`: local images, PDFs, attachments referenced by raw sources
- `wiki/sources/`: one page per source summarizing key claims and relevance
- `wiki/concepts/`: concept pages, methods, themes, frameworks
- `wiki/entities/`: people, companies, places, products, organizations, projects
- `wiki/syntheses/`: higher-order analyses, comparisons, theses, planning docs
- `wiki/queries/`: answers worth preserving from user Q&A
- `wiki/meta/`: maintenance notes, gap analyses, lint reports, conventions

## Naming Rules

- Prefer short descriptive filenames in kebab-case.
- Source summary pages: `wiki/sources/YYYY-MM-DD-short-title.md`
- Entity pages: `wiki/entities/entity-name.md`
- Concept pages: `wiki/concepts/concept-name.md`
- Syntheses: `wiki/syntheses/topic-or-question.md`
- Query pages: `wiki/queries/YYYY-MM-DD-question-slug.md`
- Use stable filenames. Avoid renaming without reason because links accumulate.

## Page Format

All wiki pages should use this structure when practical:

```md
# Title

## Summary
2-6 bullets or a short paragraph.

## Details
Structured notes, claims, evidence, relationships, or chronology.

## Links
- Related: [[...]]
- Entities: [[...]]
- Concepts: [[...]]
- Sources: [[...]]

## Sources
- [[source-page]] for source-backed claims
```

Use YAML frontmatter only when it adds value. If used, keep it minimal:

```yaml
---
type: source | entity | concept | synthesis | query | meta
status: active
created: YYYY-MM-DD
updated: YYYY-MM-DD
source_count: 0
---
```

## Link Policy

- Prefer wiki links `[[page-name]]` over plain text mentions when a page exists or should exist.
- Add links during ingest. Do not leave isolated summaries if relationships are known.
- If a concept or entity is important and repeatedly mentioned, create its page instead of leaving it implicit.
- Keep pages dense and useful. Split only when a page is becoming broad or overloaded.

## Source Handling Rules

- Treat `raw/` as immutable source-of-truth.
- Never silently delete raw files.
- If a source is partial, low-confidence, or ambiguous, say so on the source page.
- Distinguish:
  - direct source-backed claims
  - synthesis or inference
  - open questions
- When sources conflict, record the conflict explicitly instead of flattening it away.

## Ingest Workflow

When told to ingest a source:

1. Read the raw source file.
2. Identify title, date if available, source type, core claims, entities, concepts, and why it matters.
3. Create or update one source summary page in `wiki/sources/`.
4. Update any affected entity, concept, and synthesis pages.
5. Add or refresh cross-links.
6. Update `index.md`.
7. Append one entry to `log.md`.
8. Surface uncertainties, contradictions, and suggested next ingests if relevant.

Default ingest posture:

- Prefer one-source-at-a-time ingest unless the human asks for batch mode.
- Preserve the wiki as a curated artifact, not a dump of excerpts.
- Summarize aggressively; quote sparingly.

## Query Workflow

When asked a question:

1. Read `index.md` first.
2. Open the most relevant wiki pages before touching raw sources.
3. Answer from the wiki when sufficient.
4. If the wiki is missing needed context, read targeted raw sources and then update the wiki.
5. If the answer is valuable long-term, save it in `wiki/queries/` or `wiki/syntheses/`.
6. Append a `query` entry to `log.md` when a durable artifact is created.

## Lint Workflow

When asked to lint or health-check:

- Find orphan pages with weak linking.
- Find stale claims superseded by newer sources.
- Find concepts or entities that deserve their own page.
- Find contradictory claims across pages.
- Find thin pages that should be merged or expanded.
- Record results in `wiki/meta/` and append a `lint` entry to `log.md`.

## Index Rules

`index.md` is the navigation layer for both human and agent.

- Update it on every ingest that creates or materially changes pages.
- Organize by folder/category.
- Each listed page gets a one-line description.
- Keep newest or most central material near the top of each section.

## Log Rules

`log.md` is append-only. Each entry starts with:

```md
## [YYYY-MM-DD] operation | short label
```

Supported operations:

- `ingest`
- `query`
- `lint`
- `refactor`
- `schema`

Each entry should include:

- what changed
- which pages were added or updated
- any notable open questions

## Writing Style

- Write clearly and compactly.
- Prefer synthesis over extraction.
- Avoid hype, filler, and generic assistant language.
- Mark uncertainty explicitly.
- Keep pages readable in Obsidian.

## Initial Default Assumptions

- Markdown-first workflow.
- Obsidian-compatible links.
- No external search infrastructure required at small scale.
- Local raw files are the source of truth.
- The agent is expected to maintain the wiki continuously, not only answer one-off questions.

## Current Bootstrap Goal

Use `raw.md` as the first ingested source that defines the operating philosophy of this vault. Treat it as the seed document for the wiki's maintenance model.
