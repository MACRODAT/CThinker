# Heartbeat Tick Model

## Summary

HF runs on the broader `CThinker` heartbeat: a 3600-second cycle that resets every hour. Agents wake on configured tick intervals, and each tick costs points.

## Details

- A heartbeat counter increments every second until 3600 and then resets.
- Each agent has a unique tick value.
- An agent activates when the heartbeat counter is divisible by its tick value.
- Each activation costs 1 point.
- HF activity is funded by the HF departmental wallet; if the wallet reaches zero, HF stops ticking.

## Strategic Meaning

The source frames health maintenance as something that must remain continuously funded and active. If points run out, health strategy freezes.

## Open Questions

- Whether some HF actions should cost more than one tick
- How emergency or manual interventions bypass normal scheduling
- Whether all future HF agents must have globally unique ticks or only department-unique ticks

## Links

- Related: [[wiki/concepts/agent-economy]], [[wiki/entities/hf-department]], [[wiki/entities/sana]], [[wiki/entities/cthinker]]
- Sources: [[wiki/sources/2026-04-16-hf-builder]]

## Sources

- [[wiki/sources/2026-04-16-hf-builder]]
