---
name: create-github-pr
description:
  Create a GitHub Pull Request through an audited gh workflow with standardized feature and bug PR body rendering.
---

# Create GitHub PR

## Contract

Prereqs:

- Run inside the target GitHub-backed git repo with a clean working tree, or with unrelated changes isolated.
- `git` and `gh` available on `PATH`, and `gh auth status` succeeds for the target host.
- `$AGENT_HOME` points at the agent-kit repo root, or this skill's scripts are otherwise reachable.
- Codex PR creation commands must use `AGENT_KIT_PR_SKILL=create-github-pr` so the hook can audit the invocation.

Inputs:

- Required: PR outcome summary, `kind` (`feature` or `bug`), source branch, base branch, and testing notes.
- Required for `feature`: feature summary and acceptance criteria.
- Required for `bug`: bug summary, expected behavior, actual behavior, impact, and reproduction notes when available.
- Optional: labels, reviewers, assignees, linked issues, draft/ready state, source-branch cleanup preference, and template overrides.

Outputs:

- A source branch with one or more commits pushed to the GitHub remote.
- A GitHub PR created via `gh` with a standardized body rendered by `scripts/render_github_pr.sh`.
- PR command invocation marked with `AGENT_KIT_PR_SKILL=create-github-pr`.
- Final response populated from the matching `kind` output template.

Exit codes:

- N/A (multi-command workflow; failures surfaced from underlying `git`/`gh` commands)

Failure modes:

- Dirty working tree with unrelated changes that cannot be isolated safely.
- Missing `gh` auth, wrong GitHub host/repo, or insufficient push/PR permissions.
- Missing PR outcome, kind, source branch, base branch, or testing notes.
- Missing kind-specific context needed to write an outcome-oriented PR body.
- PR title/body follows a housekeeping commit subject (for example `Add plan file`) instead of the intended outcome.
- PR body missing required sections for the selected kind.

## Entrypoint

- `$AGENT_HOME/skills/workflows/pr/github/create-github-pr/scripts/render_github_pr.sh`

## Preflight (mandatory)

1. Confirm the target GitHub repository and remote host.
2. Confirm PR intent:
   - `kind`: `feature` or `bug`.
   - source branch and base branch.
   - draft by default, ready only when the user explicitly requests it.
3. Collect kind-specific context before PR creation:
   - `feature`: feature summary and acceptance criteria.
   - `bug`: bug summary, expected behavior, actual behavior, impact, and reproduction notes when available.
4. Collect testing notes before PR creation. If tests were not run, state `not run (reason)`.
5. Do not derive the PR title/body from `git log -1 --pretty=%B`; commits like `Add plan file` are not valid PR narratives.

## Branch Naming

- Reuse the current source branch when it already contains the intended work and has a clear name.
- For new branches, use the closest stable prefix:
  - `feature`: `feat/`
  - `bug`: `fix/`
- Build the slug from the outcome summary: lowercase, replace non-alphanumeric characters with hyphens, collapse duplicate hyphens,
  and trim to 3-6 words.
- If a ticket ID like `ABC-123` appears, prefix the slug with the lowercased ticket ID.

## Workflow

1. Run preflight and stop if required PR context remains missing.
2. Confirm working tree scope. Commit only intended changes, using `semantic-commit-autostage` when Codex owns the full change set or
   `semantic-commit` when the user has staged a reviewed subset.
3. Generate the PR body:
   - `$AGENT_HOME/skills/workflows/pr/github/create-github-pr/scripts/render_github_pr.sh --kind feature --pr`
   - `$AGENT_HOME/skills/workflows/pr/github/create-github-pr/scripts/render_github_pr.sh --kind bug --pr`
4. Push the source branch.
5. Create the PR with the audited marker. Open draft PRs by default:

   ```bash
   AGENT_KIT_PR_SKILL=create-github-pr gh pr create \
     --draft \
     --base "$base_branch" \
     --head "$source_branch" \
     --title "$pr_title" \
     --body-file "$pr_body_file"
   ```

6. Use ready PR creation only when the user explicitly requests it.
7. Update the PR body or discussion with final testing notes if validation changes after creation.

## PR Rules

- Title: capitalize the first word, describe the intended outcome, and never mirror a housekeeping commit subject.
- Replace the first H1 line in the rendered PR template with the PR title.
- `feature` bodies must include Summary, Changes, Testing, and Risk/Notes sections.
- `bug` bodies must include Summary, Problem, Reproduction, Issues Found, Fix Approach, Testing, and Risk/Notes sections.
- If tests are not run, state `not run (reason)`.
- Do not include tokens, auth headers, cookies, or other secrets in body, commands, tests, or final output.

## Output

- Use the matching kind output template:
  - `$AGENT_HOME/skills/workflows/pr/github/create-github-pr/scripts/render_github_pr.sh --kind feature --output`
  - `$AGENT_HOME/skills/workflows/pr/github/create-github-pr/scripts/render_github_pr.sh --kind bug --output`
