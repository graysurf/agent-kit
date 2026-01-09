---
name: open-changed-files-review
description: Open files edited by Codex in VSCode after making changes, using open-changed-files (silent no-op when unavailable).
---

# Open Changed Files Review

Use this skill when Codex has edited files and you want to immediately open the touched files in Visual Studio Code for human review.

## Inputs

- A list of file paths that were modified/added in this Codex run (preferred; does not require git).

## Workflow

1. Build a de-duplicated list of existing files from the touched paths.
2. Determine the cap:
   - Default: `CODEX_OPEN_CHANGED_FILES_MAX_FILES=50`
   - If there are more files than the cap: open the first N and mention that it was truncated.
3. Prefer running:
   - `open-changed-files --max-files "$max" --workspace-mode pwd -- <files...>`
4. If `open-changed-files` is not available, fall back to:
   - `${ZDOTDIR:-$HOME/.config/zsh}/tools/open-changed-files.zsh --max-files "$max" --workspace-mode pwd -- <files...>`
5. If VSCode CLI `code` (or the tool) is unavailable: silent no-op (exit `0`, no errors), but still print a paste-ready manual command plus the file list for the user.

## Paste-ready command template

```zsh
open-changed-files --max-files "${CODEX_OPEN_CHANGED_FILES_MAX_FILES:-50}" --workspace-mode pwd -- <files...>
```
