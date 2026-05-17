---
name: actionable-knowledge
description: Use when the user wants to learn a concept or resolve confusion with multiple lenses, assumptions, and one recommended next step.
---

# Actionable Knowledge

## Contract

Prereqs:

- User explicitly invokes `actionable-knowledge`, asks to use this prompt-style skill, or asks for a structured learning-oriented
  explanation.
- The canonical prompt source exists at `references/prompts/actionable-knowledge.md`.

Inputs:

- User question, concept, confusion, or learning goal.
- Optional context such as current understanding, domain, desired depth, time budget, or constraints.

Outputs:

- A learning-focused answer shaped by the canonical prompt source.
- Explicit assumptions and open questions when the prompt cannot safely infer intent or background.
- No repo file changes, command execution, or durable artifacts unless the user separately asks for them.

Exit codes:

- N/A (conversation workflow; no repo scripts)

Failure modes:

- Prompt source is missing or empty.
- The request requires current external facts; follow the active external-verification workflow before answering.
- The topic is underspecified enough that a baseline explanation would be misleading.

## Workflow

1. Read `references/prompts/actionable-knowledge.md`.
2. Treat that file as the canonical prompt text for this skill invocation.
3. Replace `$ARGUMENTS` conceptually with the current user question and available context.
4. Follow the prompt shape unless higher-priority system, developer, user, or project instructions conflict.
