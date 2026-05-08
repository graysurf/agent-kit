# Codex Native Roles

Codex no longer needs repo-managed `plan-issue-delivery` adapter files. Use
the native child-agent roles exposed by the active Codex runtime instead of
installing templates into `~/.codex/`.

## What Stays Canonical

- The repo contract remains:
  - `workflow_role=implementation|review|monitor`
  - dispatch bundle and runtime artifacts
  - `plan-issue-delivery-main-agent-init.md`
  - `plan-issue-delivery-subagent-init.md`
- Runtime traceability fields such as `runtime_name` / `runtime_role` stay in
  prompt manifests and dispatch records when named roles are used.

## Native Role Mapping

- Canonical `workflow_role=implementation`
  - Codex native role: `plan_issue_worker`
- Canonical `workflow_role=review`
  - Codex native role: `plan_issue_reviewer`
- Canonical `workflow_role=monitor`
  - Codex native role: `plan_issue_monitor`
- The main Codex thread remains the orchestrator; no extra named orchestrator
  role is required.

## No Adapter Install

- Repo-maintained Codex adapter templates were retired.
- `$AGENT_HOME/scripts/plan-issue-adapter` intentionally supports only retained
  repo-managed adapters (`claude|opencode`).
- Do not copy plan-issue role snippets into `~/.codex/config.toml` from this
  repository. If Codex role availability changes, use the active Codex runtime
  configuration surface rather than reintroducing repo templates.

## Usage Notes

1. Keep dynamic issue/sprint/task facts in the dispatch bundle and prompt
   snapshots, not in machine-scoped Codex config.
2. Record `runtime_name=codex` and the selected `runtime_role` only when a
   native role is actually used.
3. If named child-agent roles are unavailable, continue using the canonical
   `workflow_role` contract without Codex-specific adapter metadata.
4. No runtime adapter is the repo default; choose the active environment's
   native roles or retained repo-managed adapters explicitly.
