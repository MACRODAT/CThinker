# HF Daily Operating System

## Summary

This page defines the first practical operating layer for HF: what to track daily, how SANA should interpret the signals, and how a daily health report should be written.

## Goal

The first HF operating system should be simple enough to run every day and useful enough to influence behavior. It should favor consistency over precision-heavy tracking.

## Design Principles

- Track the smallest set of signals that meaningfully affect cognitive and physical performance.
- Prefer daily repeatability over perfect measurement.
- Separate raw observations from interpretation.
- Make the daily report short enough that it can be sustained.
- Escalate when multiple bad signals cluster together.

## Core Daily Metrics

Track these metrics first.

### Sleep

- `sleep_hours`: total estimated hours slept
- `sleep_quality`: 1-5 subjective rating
- `sleep_timing`: on-time, late, very late

Why it matters:
- Sleep quality directly affects clarity, mood, recovery, and discipline.

### Energy

- `morning_energy`: 1-5
- `midday_energy`: 1-5
- `evening_energy`: 1-5

Why it matters:
- Energy is the simplest daily proxy for whether the system is resourced or strained.

### Mental Clarity

- `mental_clarity`: 1-5
- `focus_block_done`: yes or no

Why it matters:
- HF exists partly to protect the quality of thought. This metric ties health back to actual cognition.

### Mood And Stress

- `mood`: 1-5
- `stress`: 1-5

Why it matters:
- Mood and stress are early warning signals for overload, poor recovery, and failing routines.

### Movement

- `steps_or_walk`: rough count or yes/no
- `training`: none, light, moderate, hard
- `mobility`: yes or no

Why it matters:
- Movement keeps the body active without requiring a complex fitness protocol from day one.

### Nutrition

- `protein_quality`: poor, mixed, good
- `hydration`: poor, adequate, good
- `meal_control`: poor, mixed, good

Why it matters:
- Nutrition quality strongly affects recovery, satiety, mood stability, and energy consistency.

### Recovery Friction

- `pain_or_discomfort`: none, mild, moderate, severe
- `illness_signal`: none, possible, active

Why it matters:
- HF should be preventive. Recovery friction is one of the clearest reasons to slow down or intervene early.

## Minimum Daily Check-In

If time or motivation is low, HF should still capture this minimum set:

- sleep_hours
- sleep_quality
- morning_energy
- mental_clarity
- mood
- stress
- training
- hydration
- pain_or_discomfort

This is the minimum viable HF report.

## Scoring Heuristic

Use a lightweight judgment model instead of pretending to be clinical.

### Green Day

- sleep was acceptable
- energy is mostly stable
- clarity is workable
- no major pain or illness flags

Interpretation:
- proceed normally and reinforce what worked

### Yellow Day

- one or two major signals are off
- or several minor signals are slipping

Interpretation:
- reduce unnecessary strain, tighten routines, and watch tomorrow closely

### Red Day

- severe sleep loss
- poor clarity plus high stress
- active illness
- moderate or severe pain
- strong multi-signal deterioration

Interpretation:
- prioritize recovery and reduce demand; do not pretend this is a normal operating day

## Daily HF Workflow

1. Capture daily metrics.
2. Classify the day as green, yellow, or red.
3. Write a short interpretation.
4. Set one corrective action for tomorrow.
5. If red flags persist for multiple days, create a dedicated HF strategy or issue page.

## Corrective Action Rules

Daily corrective actions should be single-step and behavior-specific.

Good examples:

- sleep before 12:00 AM
- 20-minute walk after lunch
- drink 2 liters of water before evening
- no heavy training tomorrow
- one 45-minute focus block before noon

Bad examples:

- be healthier
- fix lifestyle
- optimize everything

## Weekly Review Trigger

Run a weekly HF review if any of these happen:

- 3 or more yellow/red days in a week
- recurring late sleep timing
- declining clarity for several days
- persistent pain or illness signal
- repeated failure of the same corrective action

## Links

- Related: [[wiki/syntheses/hf-handbook]], [[wiki/entities/hf-department]], [[wiki/entities/sana]]
- Concepts: [[wiki/concepts/heartbeat-tick-model]]
