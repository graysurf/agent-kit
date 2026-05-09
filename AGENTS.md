# AGENTS.md

## Purpose & scope

- This file defines home-scope/global agent defaults for the agent-kit toolchain.
- It is git-managed in this repository and live-loaded through `$AGENT_HOME/AGENTS.md`
  (normally `$HOME/.agents/AGENTS.md`).
- Do not treat this file as policy for the agent-kit repository only; it must be safe
  as the fallback policy for unrelated workspaces.
- A closer project or directory `AGENTS.md` can override or extend these defaults.
- Keep this file concise. Long-form workflows belong in docs resolved by
  `agent-docs`.

## Default work mode

- Natural-language collaboration is the default interface. Prompt templates and
  skills are steering aids, not mandatory entrypoints unless explicitly invoked.
- For explicit implementation, maintenance, validation, or delivery requests,
  execute after the required preflight instead of prolonging planning.
- For business, requirement, feasibility, or customer-facing discussions, evaluate
  the request before solutioning and do not jump to implementation unless asked.
- Treat user-provided or customer-provided material as input to assess, not as
  already-validated truth.
- Work-oriented discussion should converge toward:
  - what the request actually is
  - whether it is feasible
  - what can be done immediately
  - what the hardest parts are
  - what prerequisites, dependencies, or breakthroughs are needed
  - what the recommended next step is
- When conclusions depend on uncertainty, explicitly separate known facts,
  assumptions, inferences, and open questions.

## Delegation defaults

- Prefer delegating independent sidecar work to subagents when a task has clear
  parallel lanes, limited file overlap, concrete validation, and a
  straightforward integration path.
- The main agent owns scope, critical path, integration, validation, and the
  final answer.
- Do not delegate small changes, tightly coupled refactors, unclear requirements,
  destructive actions, or work whose next step blocks on the subagent result.
- Keep subagent outputs concise and artifact-based when practical; summarize only
  decisions, changed paths, blockers, and validation.

## Operating defaults

- Ask only the minimum clarification needed when objective, done criteria, scope,
  constraints, environment, or safety/reversibility are materially unclear.
- When assumptions are needed and the risk is acceptable, state them briefly and
  proceed.
- Before editing code, scripts, docs, or config, inspect the target plus the
  relevant definitions, call sites, loading paths, or project rules needed to avoid
  partial-context changes.
- For external, unstable, or time-sensitive claims, prefer authoritative sources
  and cite the evidence used.
- Keep answers concise, high-signal, and easy to verify. Use structure when useful,
  but do not force a fixed response template.
- Default user-facing language is Traditional Chinese unless the user explicitly
  requests another language.
- Keep precision-critical technical terms, standards, APIs, commands, and proper
  nouns in English when that is clearer.

## Evidence & traceability

- Use traceable citations for work, requirement, feasibility, and external-fact
  claims when the source materially affects the conclusion.
- Source tags:
  - `[U#]`: user-provided or customer-provided input
  - `[F#]`: local files, repository docs, or code
  - `[W#]`: web or other published external source
  - `[A#]`: app, connector, API, CLI, or tool result
  - `[I#]`: explicit inference from cited facts
- Do not present unsupported assumptions as facts.
- If external lookup is needed, run the `task-tools` preflight first.

## Memory usage

- Personal environment memory, when present, lives in
  `~/.config/agent-memory/`.
- Detailed read/write rules live in
  `$AGENT_HOME/docs/runbooks/agent-docs/MEMORY_USAGE.md`.
- Read that doc when a task may depend on personal setup, recurring preferences,
  workspace/account conventions, or phrases like "same as before" and
  "my usual setup".
- Do not use memory for secrets, temporary task state, or project state.

## `agent-docs` policy

- `agent-docs` is the mandatory home-scope dispatch contract before
  implementation, external lookup, or skill lifecycle work.
- The canonical dispatch matrix is
  `$AGENT_HOME/docs/runbooks/agent-docs/context-dispatch-matrix.md`; keep
  detailed trigger rules there instead of duplicating them here.
- Always pin resolution with `--docs-home "$AGENT_HOME"`; nils-cli >= 0.8.0 no
  longer reads `AGENT_HOME` implicitly.
- Required context sequence:
  - new session or task: `startup`
  - repository edits, tests, commits, or delivery: `startup` -> `project-dev`
  - technical research or external verification: `startup` -> `task-tools`
  - skill lifecycle work: `startup` -> `skill-dev`
- Resolve each required context in strict checklist mode:
  `agent-docs --docs-home "$AGENT_HOME" resolve --context <context> --strict --format checklist`.
- If a hard-gate strict resolve fails, stop write actions and delivery claims, run
  `agent-docs --docs-home "$AGENT_HOME" baseline --check --target all --strict --format text`,
  then report the missing docs or degraded mode explicitly.
- Codex hooks may inject lightweight `agent-docs` reminders, but hooks are
  enforcement support and do not replace this policy.

## Files and artifacts

- Follow the active project's conventions for deliverables and generated files.
- Put temporary debug or test artifacts under `$AGENT_HOME/out/` instead of `/tmp`
  when practical, and mention that path in the reply.
- Do not create files only to mirror response text unless the task specifically
  calls for an artifact.
- Do not persist conversation records by default. Create durable discussion or
  decision artifacts only when the user asks, project rules require it, or the
  result is clearly reusable.

## Hook-Enforced Guardrails

- Codex hooks may enforce mechanical guardrails such as direct `git commit`,
  PR/MR creation, `.mcp.json` secret scanning, project-memory write boundaries,
  lightweight `agent-docs` reminders, and PR-readiness reminders.
- Treat hooks as enforcement support, not the only source of policy. If hooks
  are unavailable, follow the policy summaries here and the linked runbooks.
- Hook source and the managed config block live under `$AGENT_HOME/hooks/codex/`.
  Use `$AGENT_HOME/scripts/codex-hooks-sync sync --apply` to write that block
  into local `$HOME/.codex/config.toml`; do not track or symlink the whole
  Codex config file.

## Canonical references

- Home dispatch and bootstrap:
  - `$AGENT_HOME/AGENT_DOCS.toml`
  - `$AGENT_HOME/docs/runbooks/agent-docs/`
- Tool selection and research workflow:
  - `$AGENT_HOME/CLI_TOOLS.md`
  - `$AGENT_HOME/RESEARCH_WORKFLOW.md`
- This agent-kit repository maintenance:
  - `$AGENT_HOME/DEVELOPMENT.md`

## Validation and commits

- Prefer project-defined validation commands. If no project rules exist, run the
  smallest meaningful checks for the change and report what was or was not run.
- Before reporting implementation work complete, run the relevant checks or state
  clearly why they could not be run.
- For changes to this agent-kit toolchain repository, use `DEVELOPMENT.md` as the
  canonical source and run `scripts/check.sh --all` before reporting maintenance
  complete.
- Commits must use `semantic-commit` or `semantic-commit-autostage`; do not run
  `git commit` directly.
