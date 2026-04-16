# Folder Conventions

## Purpose

This page defines where information belongs so the wiki stays predictable as it grows.

## Structure

- `raw/inbox/`: newly added source files waiting to be ingested
- `raw/library/`: raw files that have been ingested and retained as immutable source documents
- `raw/assets/`: downloaded images and attachments
- `wiki/sources/`: source summaries with key claims and why the source matters
- `wiki/entities/`: durable pages for people, orgs, products, places, and projects
- `wiki/concepts/`: durable pages for ideas, methods, themes, systems, and frameworks
- `wiki/syntheses/`: cross-source analysis, comparisons, thesis pages, plans
- `wiki/queries/`: durable answers created from question-driven work
- `wiki/meta/`: maintenance and control documents

## Placement Rules

- A raw document never lives in `wiki/`.
- A wiki page should summarize and integrate; it should not mirror the raw file verbatim.
- If a page is mostly about one source, it belongs in `wiki/sources/`.
- If a page exists independent of any single source, it likely belongs in `wiki/concepts/`, `wiki/entities/`, or `wiki/syntheses/`.
- If an answer came from a question and is likely reusable, store it in `wiki/queries/` or promote it to `wiki/syntheses/`.

## Status

Current convention is optimized for a single-user Obsidian vault operated by an LLM agent.

## Links

- Related: [[Agents]], [[wiki/concepts/schema-index-log]], [[wiki/syntheses/second-brain-blueprint]]
