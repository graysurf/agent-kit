# AGENTS.md

## Purpose & Scope

- This file defines home-scope/global defaults for the agent-kit toolchain.
- It is git-managed in this repository and live-loaded through `$AGENT_HOME/AGENTS.md`
  (normally `$HOME/.agents/AGENTS.md`).
- It must be safe as fallback policy for unrelated workspaces, not only this repo.
- A closer project or directory `AGENTS.md` can override or extend these defaults.
- Keep this file concise. Detailed workflows belong in docs resolved by `agent-docs`.

## Default Work Mode

- Natural-language collaboration is the default interface.
- Prompt templates and skills are steering aids, not mandatory entrypoints unless
  explicitly invoked.
- For explicit implementation, maintenance, validation, or delivery requests,
  execute after required preflight instead of prolonging planning.
- For business, requirement, feasibility, or customer-facing discussions, evaluate
  first and do not jump to implementation unless asked.
- Treat user-provided or customer-provided material as input to assess, not as
  already-validated truth.
- When conclusions depend on uncertainty, separate known facts, assumptions,
  inferences, and open questions.

## Delegation Modes

- Subagent delegation is opt-in. Use explicit user instruction or prompt modes
  such as `parallel-first` or `orchestrator-first` before spawning subagents.
- `parallel-first` optimizes for safely parallelizable sidecar work.
- `orchestrator-first` makes the main agent own intent, scope, dispatch,
  integration, validation, and final answer while subagents own implementation lanes.
- Outside an explicit delegation mode, follow the runtime harness rules and do not
  treat this file alone as permission to spawn subagents.
- Do not use delegation modes for small changes, unclear requirements, tightly
  coupled refactors, destructive operations, or work whose next step blocks on a
  subagent result.

## Operating Defaults

- Ask only the minimum clarification needed when objective, done criteria, scope,
  constraints, environment, or safety/reversibility are materially unclear.
- When assumptions are acceptable, state them briefly and proceed.
- Before editing code, scripts, docs, or config, inspect the target plus relevant
  definitions, call sites, loading paths, or project rules.
- For testable production behavior changes, prefer failing-test evidence before
  editing production code; when not practical, state an explicit waiver and
  substitute validation before editing.
- For external, unstable, or time-sensitive claims, prefer authoritative sources
  and cite the evidence used.
- Keep answers concise, high-signal, and easy to verify.
- Default user-facing language is Traditional Chinese unless requested otherwise.
- Keep precision-critical technical terms, standards, APIs, commands, and proper
  nouns in English when clearer.

## Evidence & Traceability

- Use traceable citations when source material materially affects a requirement,
  feasibility, work, or external-fact claim.
- Source tags: `[U#]` user input, `[F#]` local files/code/docs, `[W#]` web source,
  `[A#]` app/API/CLI/tool result, `[I#]` inference from cited facts.
- Do not present unsupported assumptions as facts.
- If external lookup is needed, run the `task-tools` preflight first.

## Memory Usage

- Use personal environment memory only for personal setup, recurring preferences,
  workspace/account conventions, or phrases like "same as before" and
  "my usual setup".
- Follow `$AGENT_HOME/docs/runbooks/agent-docs/MEMORY_USAGE.md` for detailed rules.
- Do not use memory for secrets, temporary task state, or project state.

## `agent-docs` Policy

- `agent-docs` is the mandatory home-scope dispatch contract before implementation,
  external lookup, or skill lifecycle work.
- Always pin resolution with `--docs-home "$AGENT_HOME"`.
- Required context sequence:
  - new session or task: `startup`
  - repository edits, tests, commits, or delivery: `startup` -> `project-dev`
  - technical research or external verification: `startup` -> `task-tools`
  - skill lifecycle work: `startup` -> `skill-dev`
- Resolve each required context in strict checklist mode:
  `agent-docs --docs-home "$AGENT_HOME" resolve --context <context> --strict --format checklist`.
- If a hard-gate strict resolve fails, stop write actions and delivery claims, run:
  `agent-docs --docs-home "$AGENT_HOME" baseline --check --target all --strict --format text`
  Then report the missing docs or degraded mode explicitly.

## Files, Hooks, And Validation

- Follow the active project's conventions for deliverables and generated files.
- For temporary/debug artifacts without a project-defined output path, create a
  project run directory with `agent-out project --topic <topic> --mkdir`.
- Do not override established tool/workflow artifact contracts; use
  `agent-out audit` before cleaning or enforcing `$AGENT_HOME/out/`.
- Do not create durable discussion or decision artifacts unless asked, required by
  project rules, or clearly reusable.
- Codex hooks may enforce mechanical guardrails, but hooks do not replace policy.
- Hook source and managed config live under `$AGENT_HOME/hooks/codex/`.
- Use `$AGENT_HOME/scripts/codex-hooks-sync sync --apply` to update local
  `$HOME/.codex/config.toml`; do not track or symlink the whole Codex config file.
- Prefer project-defined validation commands. If none exist, run the smallest
  meaningful checks and report what was or was not run.
- For agent-kit repository maintenance, use `$AGENT_HOME/DEVELOPMENT.md` and run
  `scripts/check.sh --all` before reporting maintenance complete.
- Commits must use `semantic-commit` or `semantic-commit-autostage`; do not run
  `git commit` directly.
