# HF Builder

## Summary

- `HF_BUILDER.md` defines the foundational design brief for the Health and Welfare department inside the larger `CThinker` system.
- HF's mission is to act as a personal health advisory department focused on prevention, routines, long-term strategy, and daily tracking.
- The document embeds HF inside a broader multi-department architecture with agents, CEOs, threads, points, memory limits, and heartbeat-based ticking.
- It explicitly names `SANA` as the current CEO of HF and anticipates future subordinate agents.
- One direct deliverable is required: an initial markdown file that teaches a novice what HF is and how it works.

## Source Details

- Source file: `raw/inbox/HF_BUILDER.md`
- Source type: implementation brief / system design note
- Ingest date: 2026-04-16
- Confidence: medium-high for intended system rules; low for final wording because parts are rough and may evolve

## Core Claims

1. HF is the foundational department because brain and body quality constrain every other department's performance.
2. CThinker uses a gamified internal structure: agents, departments, threads, wallets, points, and status transitions.
3. Agents act on heartbeat-based ticks and consume points simply by operating.
4. SANA is the current sole CEO of HF but the architecture anticipates organizational expansion.
5. HF should produce clear operational documentation that a novice can understand.

## Ambiguities And Design Gaps

- The draft mixes core platform rules (`CThinker`) with department-specific policy (`HF`), so future pages should keep those separated.
- Some thread permissions are marked as conditional or tentative, especially around superior chains and founder approval.
- The exact storage format for wallets, logs, threads, and tick execution is not defined here.
- The document does not define concrete daily health metrics yet; it only defines mission and governance.

## Implications For This Vault

- HF needs an entity page as a department, not just a source summary.
- SANA needs an entity page because the CEO role is central to HF governance.
- CThinker needs an entity page because HF is nested inside that larger structure.
- The agent/points/thread system deserves its own concept pages so future HF content does not repeat platform mechanics everywhere.
- The novice-facing deliverable should live as a synthesis or handbook page.

## Links

- Entities: [[wiki/entities/hf-department]], [[wiki/entities/sana]], [[wiki/entities/cthinker]]
- Concepts: [[wiki/concepts/agent-economy]], [[wiki/concepts/heartbeat-tick-model]]
- Synthesis: [[wiki/syntheses/hf-handbook]]
- Raw source: `raw/inbox/HF_BUILDER.md`

## Sources

- `raw/inbox/HF_BUILDER.md`
