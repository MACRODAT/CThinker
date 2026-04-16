# Agent Economy

## Summary

The `CThinker` model uses agents, points, threads, and role-based permissions as an internal operating economy. HF inherits this model rather than inventing its own separate mechanism.

## Details

- Agents have roles, department affiliations, and point budgets.
- Agents operate in one of four modes: Points Accounter, Creator, Investor, and Custom.
- Agents may preserve a small amount of memory between ticks.
- Threads have owners, statuses, budgets, and contribution rules.
- Actions like creating threads, posting, and investing consume or redistribute points.
- Reward logic exists for approved threads and splits value between contributors and departments.

## Why It Matters

HF behavior cannot be understood only as health guidance. It must be understood as health guidance operating inside an incentive and budget framework.

## Caveats

- The source defines the rules at a high level but does not yet specify implementation details like exact file schemas or ledger structures.
- Some permission flows may need simplification before operational use.

## Links

- Related: [[wiki/concepts/heartbeat-tick-model]], [[wiki/entities/cthinker]], [[wiki/entities/hf-department]], [[wiki/entities/sana]]
- Sources: [[wiki/sources/2026-04-16-hf-builder]]

## Sources

- [[wiki/sources/2026-04-16-hf-builder]]
