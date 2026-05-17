---
name: orchestrator-first
description: Use when the user wants the main agent to own scope, dispatch, integration, validation, and final synthesis while subagents own implementation lanes.
---

# Orchestrator First

## Contract

Prereqs:

- User explicitly invokes `orchestrator-first`, asks for orchestrator-first mode, or requests an orchestration-owned multi-lane workflow.
- The canonical prompt source exists at `references/prompts/orchestrator-first.md`.
- Subagent delegation is available and allowed by active runtime instructions before any subagents are spawned.

Inputs:

- Optional goal, constraints, lane boundaries, validation expectations, or disable instruction.
- Future user requests in the same thread when the mode has been explicitly enabled.

Outputs:

- Confirmation that orchestrator-first mode is enabled when invoked as a mode-setting prompt.
- Delegation gate and disable instruction from the canonical prompt source.
- No subagents unless the current request passes the active delegation gate.

Exit codes:

- N/A (conversation workflow; no repo scripts)

Failure modes:

- Prompt source is missing or empty.
- The request is too small, unclear, tightly coupled, destructive, or immediately blocked on subagent output.
- Active runtime instructions prohibit delegation despite the requested mode.

## Workflow

1. Read `references/prompts/orchestrator-first.md`.
2. Treat that file as the canonical prompt text for this skill invocation.
3. If enabling the mode, respond with the required confirmation, delegation gate, and disable instruction.
4. For later work in this thread, apply the mode only when the user has explicitly enabled it and active runtime rules allow delegation.
