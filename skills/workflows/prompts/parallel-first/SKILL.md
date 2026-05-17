---
name: parallel-first
description:
  Use when the user wants a parallel-first policy for safely parallelizable work through the shared parallel delegation protocol when
  appropriate.
---

# Parallel First

## Contract

Prereqs:

- User explicitly invokes `parallel-first`, asks for parallel-first mode, or requests a parallel-first execution policy.
- The canonical prompt source exists at `references/prompts/parallel-first.md`.
- Subagent delegation is available and allowed by active runtime instructions before any subagents are spawned.

Inputs:

- Optional preferences such as maximum agents, retry limits, or constraints.
- Future user requests in the same thread when the mode has been explicitly enabled.

Outputs:

- Confirmation that parallel-first mode is enabled when invoked as a mode-setting prompt.
- Parallelization gate, defaults, and disable instruction from the canonical prompt source.
- No subagents unless the current request is safely parallelizable and active runtime rules allow delegation.

Exit codes:

- N/A (conversation workflow; no repo scripts)

Failure modes:

- Prompt source is missing or empty.
- The request has fewer than two independent tasks, unclear acceptance criteria, overlapping write scope, or a tightly coupled next step.
- Active runtime instructions prohibit delegation despite the requested mode.

## Workflow

1. Read `references/prompts/parallel-first.md`.
2. Treat that file as the canonical prompt text for this skill invocation.
3. If enabling the mode, respond with the required confirmation, defaults, and disable instruction.
4. For later work in this thread, apply the mode only when the user has explicitly enabled it and active runtime rules allow delegation.
