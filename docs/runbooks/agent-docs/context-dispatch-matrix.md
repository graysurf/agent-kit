# Context Dispatch Matrix (Runtime Intent -> Resolution Order)

## Scope

- This document is the canonical dispatch contract for `agent-docs` context loading.
- Built-in contexts covered here: `startup`, `task-tools`, `project-dev`, `skill-dev`.
- `AGENTS.md` and `AGENTS.override.md` must reference this file instead of duplicating dispatch rules.

## Built-in contexts and trigger points

| Context | Trigger points | Runtime intent signals | Gate level |
| --- | --- | --- | --- |
| `startup` | First turn in a new session, session resume, or policy reload at task start | "continue", "resume", any new task start | Hard gate |
| `task-tools` | Technical lookup before/during work | "look up", "latest", "docs", "verify source", external API/library uncertainty | Soft gate (hard when user demands strict authoritative lookup) |
| `project-dev` | Any repository implementation flow | edit code, run tests/build, refactor, fix bug, prepare commit/PR | Hard gate for write actions |
| `skill-dev` | Skill lifecycle work | create/update/remove skills, skill contract/governance checks | Hard gate |

## Runtime intent -> context resolution order (with preflight)

| Workflow type | Required preflight commands | Context resolution order | Strictness policy | Missing required docs fallback |
| --- | --- | --- | --- | --- |
| Startup session load | `agent-docs resolve --context startup --strict --format text` | `startup` | Strict required | If strict resolve fails: run `agent-docs baseline --check --target home --strict --format text`, block task execution (read-only diagnostics only), report missing docs and stop. |
| Technical research | `agent-docs resolve --context startup --format text` (session entry), `agent-docs resolve --context task-tools --strict --format text` | `startup -> task-tools` | Strict first, may downgrade to non-strict | If strict resolve fails: rerun `agent-docs resolve --context task-tools --format text`; continue only with `status=present` docs and explicitly label degraded mode. If no usable docs remain, stop. |
| Project implementation | `agent-docs resolve --context startup --format text` (session entry), `agent-docs resolve --context project-dev --strict --format text`; optional `agent-docs resolve --context task-tools --format text` when external lookup is needed | `startup -> project-dev -> task-tools` (optional) | `project-dev` strict required before edits/tests/commit; `task-tools` strict optional | If `project-dev` strict resolve fails: block file edits/commit, run strict baseline check, request remediation. If only `task-tools` is missing: proceed with local-repo evidence only and mark assumptions. |
| Skill authoring | `agent-docs resolve --context startup --format text` (session entry), `agent-docs resolve --context skill-dev --strict --format text`; optional `agent-docs resolve --context task-tools --format text` | `startup -> skill-dev -> task-tools` (optional) | `skill-dev` strict required; `task-tools` strict optional | If `skill-dev` strict resolve fails: block skill file changes and remediation-first. If only `task-tools` is missing: continue with local skill templates/contracts only, no external claims without citation. |

## Strict vs non-strict rules (concrete)

1. Strict mode: use `agent-docs resolve --context <ctx> --strict --format text`. Any missing required doc is a failure signal for that context.
2. Non-strict mode: use `agent-docs resolve --context <ctx> --format text`. Missing required docs are allowed but must be surfaced.
3. Hard-gate contexts: `startup`, `project-dev` (for write operations), `skill-dev`.
4. Soft-gate context: `task-tools` unless user explicitly requests strict/authoritative verification, in which case treat it as hard gate.
5. Degraded-mode execution is allowed only after an explicit strict failure on a soft-gate context, and the response must list assumptions and missing documents.

## Operator checklist

1. Identify workflow type from runtime intent.
2. Execute preflight commands in the order defined by the matrix row.
3. Apply hard/soft gate behavior exactly as defined above.
4. If degraded mode is used, explicitly disclose it in the response.
