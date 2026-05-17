---
name: create-gitlab-mr
description:
  Create a GitLab Merge Request through an audited glab workflow with standardized branch, body, draft, and source-branch handling.
---

# Create GitLab MR

## Contract

Prereqs:

- Run inside the target GitLab-backed git repo with a clean working tree, or with unrelated changes isolated.
- `git` and `glab` available on `PATH`, and `glab auth status` succeeds for the target host.
- `$AGENT_HOME` points at the agent-kit repo root, or this skill's scripts are otherwise reachable.
- Codex MR creation commands must use `AGENT_KIT_PR_SKILL=create-gitlab-mr` so the hook can audit the invocation.

Inputs:

- Required: MR outcome summary, `kind` (`feature`, `bug`, `config`, `deploy`, `docs`, or `chore`), source branch, target branch,
  and testing notes.
- Optional: labels, reviewers, assignees, related issue, draft/ready state, source-branch deletion preference, squash preference, and MR
  template overrides.

Outputs:

- A source branch with one or more commits pushed to the GitLab remote.
- A GitLab MR created via `glab` with a standardized body from `references/MR_TEMPLATE.md`.
- MR command invocation marked with `AGENT_KIT_PR_SKILL=create-gitlab-mr`.
- Final response populated from `references/ASSISTANT_RESPONSE_TEMPLATE.md`.

Exit codes:

- N/A (multi-command workflow; failures surfaced from underlying `git`/`glab` commands)

Failure modes:

- Dirty working tree with unrelated changes that cannot be isolated safely.
- Missing `glab` auth, wrong GitLab host/project, or insufficient push/MR permissions.
- Missing MR outcome, target branch, source branch, or testing notes.
- MR body missing required sections or relying on a housekeeping commit subject as its narrative.
- Source-branch deletion or squash behavior left implicit when repository defaults are unknown.

## Entrypoint

- `$AGENT_HOME/skills/workflows/mr/gitlab/create-gitlab-mr/scripts/render_gitlab_mr.sh`

## Preflight (mandatory)

1. Confirm the target GitLab project and remote host.
2. Confirm MR intent:
   - `kind`: `feature`, `bug`, `config`, `deploy`, `docs`, or `chore`.
   - source branch and target branch.
   - draft by default, ready only when the user explicitly requests it.
3. Confirm source-branch policy:
   - default to `--remove-source-branch=false` unless the user or repo convention explicitly says otherwise.
4. Collect testing notes before MR creation. If tests were not run, state `not run (reason)`.
5. For production behavior changes, collect test-first evidence or waiver:
   `Change classification`, `Failing test before fix`, `Final validation`, and `Waiver reason` when applicable.
6. Do not derive the MR title/body from `git log -1 --pretty=%B`; commits like `Update values` are not valid MR narratives.

## Branch Naming

- Reuse the current source branch when it already contains the intended work and has a clear name.
- For new branches, use the closest stable prefix:
  - `feature`: `feat/`
  - `bug`: `fix/`
  - `docs`: `docs/`
  - `config`, `deploy`, `chore`: `chore/`
- If a ticket ID like `IA-2581` appears, prefix the slug with the lowercased ticket ID.

## Workflow

1. Run preflight and stop if required MR context remains missing.
2. Confirm working tree scope. Commit only intended changes, using `semantic-commit-autostage` when Codex owns the full change set or
   `semantic-commit` when the user has staged a reviewed subset.
3. Generate the MR body:
   - `$AGENT_HOME/skills/workflows/mr/gitlab/create-gitlab-mr/scripts/render_gitlab_mr.sh --mr`
4. Push the source branch.
5. Create the MR with the audited marker. Prefer `glab mr create`:

   ```bash
   AGENT_KIT_PR_SKILL=create-gitlab-mr glab mr create \
     --draft \
     --title "$mr_title" \
     --description "$mr_body" \
     --source-branch "$source_branch" \
     --target-branch "$target_branch" \
     --remove-source-branch=false \
     --squash-before-merge=false \
     --yes
   ```

6. Use `glab api` only when the installed `glab mr create` cannot express a required field for the target GitLab version. Keep the same
   audited marker and set `remove_source_branch=false` explicitly.
7. Update the MR body or discussion with final testing notes if validation changes after creation.

## MR Rules

- Title: describe the outcome, not the latest commit subject.
- Body must include Summary, Changes, Test-First Evidence, Testing, Risk/Notes, Source Branch Policy, and Rollback sections.
- Test-First Evidence must include `Change classification`, `Failing test before fix`, `Final validation`, and `Waiver reason` when
  applicable.
- For deploy/config repos, include the rendered environment or manifest validation commands in Testing.
- Draft is the default; ready MR creation requires explicit user instruction.
- Do not include tokens, auth headers, cookies, or other secrets in body, commands, tests, or final output.

## Output

- Use `references/ASSISTANT_RESPONSE_TEMPLATE.md` as the response format.
- Use `$AGENT_HOME/skills/workflows/mr/gitlab/create-gitlab-mr/scripts/render_gitlab_mr.sh --output` to generate the output template quickly.
