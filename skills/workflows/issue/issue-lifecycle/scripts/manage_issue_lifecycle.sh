#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "${script_dir}/.." && pwd)"
default_issue_template="${skill_dir}/references/ISSUE_BODY_TEMPLATE.md"

die() {
  echo "error: $*" >&2
  exit 1
}

require_cmd() {
  local cmd="${1:-}"
  command -v "$cmd" >/dev/null 2>&1 || die "$cmd is required"
}

print_cmd() {
  local out=""
  local arg=''
  for arg in "$@"; do
    out+=" $(printf '%q' "$arg")"
  done
  printf '%s\n' "${out# }"
}

run_cmd() {
  if [[ "${dry_run}" == "1" ]]; then
    echo "dry-run: $(print_cmd "$@")" >&2
    return 0
  fi
  "$@"
}

usage() {
  cat <<'USAGE'
Usage:
  manage_issue_lifecycle.sh <open|update|decompose|comment|close|reopen> [options]

Subcommands:
  open       Create a new issue owned by the main agent
  update     Update title/body/labels/assignees/projects for an issue
  decompose  Render task split markdown from a TSV and optionally comment on issue
  comment    Add an issue progress comment
  close      Close an issue with optional completion comment
  reopen     Reopen an issue with optional comment

Common options:
  --repo <owner/repo>    Target repository (passed to gh with -R)
  --dry-run              Print actions without calling gh

open options:
  --title <text>                 Issue title (required)
  --body <text>                  Inline issue body
  --body-file <path>             Issue body file path
  --use-template                 Use references/ISSUE_BODY_TEMPLATE.md when body not set
  --label <name>                 Repeatable label flag
  --assignee <login>             Repeatable assignee flag
  --project <title>              Repeatable project title flag
  --milestone <name>             Milestone title

update options:
  --issue <number>               Issue number (required)
  --title <text>                 New title
  --body <text>                  New body
  --body-file <path>             New body file
  --add-label <name>             Repeatable add-label flag
  --remove-label <name>          Repeatable remove-label flag
  --add-assignee <login>         Repeatable add-assignee flag
  --remove-assignee <login>      Repeatable remove-assignee flag
  --add-project <title>          Repeatable add-project flag
  --remove-project <title>       Repeatable remove-project flag

Decompose options:
  --issue <number>               Issue number (required)
  --spec <path>                  TSV spec with task split (required)
  --header <text>                Heading text (default: "Task Decomposition")
  --comment                      Post decomposition to issue (default: print only)

Comment options:
  --issue <number>               Issue number (required)
  --body <text>                  Comment body
  --body-file <path>             Comment body file

Close/Reopen options:
  --issue <number>               Issue number (required)
  --reason <completed|not planned>
                                Close reason (close only, default: completed)
  --comment <text>               Comment text for close/reopen
  --comment-file <path>          Comment body file for close/reopen
USAGE
}

render_decompose_markdown() {
  local spec_path="${1:-}"
  local header="${2:-Task Decomposition}"

  python3 - "$spec_path" "$header" <<'PY'
import csv
import pathlib
import sys

spec_path = pathlib.Path(sys.argv[1])
header = sys.argv[2]

if not spec_path.is_file():
    raise SystemExit(f"error: spec file not found: {spec_path}")

rows = []
with spec_path.open("r", encoding="utf-8") as handle:
    reader = csv.reader(handle, delimiter="\t")
    for line_no, row in enumerate(reader, start=1):
        if not row:
            continue
        if row[0].strip().startswith("#"):
            continue
        if len(row) < 4:
            raise SystemExit(
                f"error: invalid spec line {line_no}: expected at least 4 tab-separated fields "
                "(task_id, summary, branch, worktree[, owner][, notes])"
            )
        task_id = row[0].strip()
        summary = row[1].strip()
        branch = row[2].strip()
        worktree = row[3].strip()
        owner = row[4].strip() if len(row) >= 5 else "TBD"
        notes = row[5].strip() if len(row) >= 6 else ""

        if not task_id or not summary or not branch or not worktree:
            raise SystemExit(
                f"error: invalid spec line {line_no}: task_id, summary, branch, and worktree must be non-empty"
            )

        rows.append((task_id, summary, branch, worktree, owner, notes))

if not rows:
    raise SystemExit("error: no task rows found in spec")

print(f"## {header}")
print("")
print("| Task | Summary | Branch | Worktree | Owner | Notes |")
print("| --- | --- | --- | --- | --- | --- |")
for task_id, summary, branch, worktree, owner, notes in rows:
    notes_value = notes if notes else "-"
    print(f"| {task_id} | {summary} | `{branch}` | `{worktree}` | {owner} | {notes_value} |")

print("")
print("## Subagent Dispatch")
print("")
for task_id, summary, branch, worktree, owner, notes in rows:
    notes_value = notes if notes else "none"
    print(f"- [ ] {task_id}: {summary}")
    print(f"  - owner: {owner}")
    print(f"  - branch: `{branch}`")
    print(f"  - worktree: `{worktree}`")
    print(f"  - notes: {notes_value}")
PY
}

subcommand="${1:-}"
if [[ -z "$subcommand" ]]; then
  usage >&2
  exit 1
fi
shift || true

dry_run="0"
repo_arg=""

case "$subcommand" in
  open)
    title=""
    body=""
    body_file=""
    use_template="0"
    milestone=""
    labels=()
    assignees=()
    projects=()

    while [[ $# -gt 0 ]]; do
      case "${1:-}" in
        --title)
          title="${2:-}"
          shift 2
          ;;
        --body)
          body="${2:-}"
          shift 2
          ;;
        --body-file)
          body_file="${2:-}"
          shift 2
          ;;
        --use-template)
          use_template="1"
          shift
          ;;
        --label)
          labels+=("${2:-}")
          shift 2
          ;;
        --assignee)
          assignees+=("${2:-}")
          shift 2
          ;;
        --project)
          projects+=("${2:-}")
          shift 2
          ;;
        --milestone)
          milestone="${2:-}"
          shift 2
          ;;
        --repo)
          repo_arg="${2:-}"
          shift 2
          ;;
        --dry-run)
          dry_run="1"
          shift
          ;;
        -h|--help)
          usage
          exit 0
          ;;
        *)
          die "unknown option for open: $1"
          ;;
      esac
    done

    [[ -n "$title" ]] || die "--title is required for open"

    if [[ -n "$body" && -n "$body_file" ]]; then
      die "use either --body or --body-file, not both"
    fi

    if [[ "$use_template" == "1" && -z "$body" && -z "$body_file" ]]; then
      body_file="$default_issue_template"
    fi

    if [[ -z "$body" && -z "$body_file" ]]; then
      die "issue body is required: provide --body, --body-file, or --use-template"
    fi

    if [[ -n "$body_file" && ! -f "$body_file" ]]; then
      die "body file not found: $body_file"
    fi

    require_cmd gh

    cmd=(gh issue create --title "$title")
    if [[ -n "$repo_arg" ]]; then
      cmd+=(-R "$repo_arg")
    fi
    if [[ -n "$body" ]]; then
      cmd+=(--body "$body")
    else
      cmd+=(--body-file "$body_file")
    fi

    for item in "${labels[@]}"; do
      cmd+=(--label "$item")
    done
    for item in "${assignees[@]}"; do
      cmd+=(--assignee "$item")
    done
    for item in "${projects[@]}"; do
      cmd+=(--project "$item")
    done
    if [[ -n "$milestone" ]]; then
      cmd+=(--milestone "$milestone")
    fi

    if [[ "$dry_run" == "1" ]]; then
      run_cmd "${cmd[@]}"
      echo "DRY-RUN-ISSUE-URL"
      exit 0
    fi

    run_cmd "${cmd[@]}"
    ;;

  update)
    issue_number=""
    title=""
    body=""
    body_file=""
    add_labels=()
    remove_labels=()
    add_assignees=()
    remove_assignees=()
    add_projects=()
    remove_projects=()

    while [[ $# -gt 0 ]]; do
      case "${1:-}" in
        --issue)
          issue_number="${2:-}"
          shift 2
          ;;
        --title)
          title="${2:-}"
          shift 2
          ;;
        --body)
          body="${2:-}"
          shift 2
          ;;
        --body-file)
          body_file="${2:-}"
          shift 2
          ;;
        --add-label)
          add_labels+=("${2:-}")
          shift 2
          ;;
        --remove-label)
          remove_labels+=("${2:-}")
          shift 2
          ;;
        --add-assignee)
          add_assignees+=("${2:-}")
          shift 2
          ;;
        --remove-assignee)
          remove_assignees+=("${2:-}")
          shift 2
          ;;
        --add-project)
          add_projects+=("${2:-}")
          shift 2
          ;;
        --remove-project)
          remove_projects+=("${2:-}")
          shift 2
          ;;
        --repo)
          repo_arg="${2:-}"
          shift 2
          ;;
        --dry-run)
          dry_run="1"
          shift
          ;;
        -h|--help)
          usage
          exit 0
          ;;
        *)
          die "unknown option for update: $1"
          ;;
      esac
    done

    [[ -n "$issue_number" ]] || die "--issue is required for update"

    if [[ -n "$body" && -n "$body_file" ]]; then
      die "use either --body or --body-file, not both"
    fi

    if [[ -n "$body_file" && ! -f "$body_file" ]]; then
      die "body file not found: $body_file"
    fi

    if [[ -z "$title" && -z "$body" && -z "$body_file" && ${#add_labels[@]} -eq 0 && ${#remove_labels[@]} -eq 0 && ${#add_assignees[@]} -eq 0 && ${#remove_assignees[@]} -eq 0 && ${#add_projects[@]} -eq 0 && ${#remove_projects[@]} -eq 0 ]]; then
      die "update requires at least one edit flag"
    fi

    require_cmd gh

    cmd=(gh issue edit "$issue_number")
    if [[ -n "$repo_arg" ]]; then
      cmd+=(-R "$repo_arg")
    fi
    if [[ -n "$title" ]]; then
      cmd+=(--title "$title")
    fi
    if [[ -n "$body" ]]; then
      cmd+=(--body "$body")
    elif [[ -n "$body_file" ]]; then
      cmd+=(--body-file "$body_file")
    fi

    for item in "${add_labels[@]}"; do
      cmd+=(--add-label "$item")
    done
    for item in "${remove_labels[@]}"; do
      cmd+=(--remove-label "$item")
    done
    for item in "${add_assignees[@]}"; do
      cmd+=(--add-assignee "$item")
    done
    for item in "${remove_assignees[@]}"; do
      cmd+=(--remove-assignee "$item")
    done
    for item in "${add_projects[@]}"; do
      cmd+=(--add-project "$item")
    done
    for item in "${remove_projects[@]}"; do
      cmd+=(--remove-project "$item")
    done

    run_cmd "${cmd[@]}"
    ;;

  decompose)
    issue_number=""
    spec_file=""
    header="Task Decomposition"
    post_comment="0"

    while [[ $# -gt 0 ]]; do
      case "${1:-}" in
        --issue)
          issue_number="${2:-}"
          shift 2
          ;;
        --spec)
          spec_file="${2:-}"
          shift 2
          ;;
        --header)
          header="${2:-}"
          shift 2
          ;;
        --comment)
          post_comment="1"
          shift
          ;;
        --repo)
          repo_arg="${2:-}"
          shift 2
          ;;
        --dry-run)
          dry_run="1"
          shift
          ;;
        -h|--help)
          usage
          exit 0
          ;;
        *)
          die "unknown option for decompose: $1"
          ;;
      esac
    done

    [[ -n "$issue_number" ]] || die "--issue is required for decompose"
    [[ -n "$spec_file" ]] || die "--spec is required for decompose"
    [[ -f "$spec_file" ]] || die "spec file not found: $spec_file"

    require_cmd python3

    tmp_body="$(mktemp)"
    render_decompose_markdown "$spec_file" "$header" >"$tmp_body"

    if [[ "$post_comment" == "0" ]]; then
      cat "$tmp_body"
      rm -f "$tmp_body"
      exit 0
    fi

    require_cmd gh
    cmd=(gh issue comment "$issue_number")
    if [[ -n "$repo_arg" ]]; then
      cmd+=(-R "$repo_arg")
    fi
    cmd+=(--body-file "$tmp_body")

    if [[ "$dry_run" == "1" ]]; then
      run_cmd "${cmd[@]}"
      cat "$tmp_body"
      rm -f "$tmp_body"
      exit 0
    fi

    run_cmd "${cmd[@]}"
    rm -f "$tmp_body"
    ;;

  comment)
    issue_number=""
    body=""
    body_file=""

    while [[ $# -gt 0 ]]; do
      case "${1:-}" in
        --issue)
          issue_number="${2:-}"
          shift 2
          ;;
        --body)
          body="${2:-}"
          shift 2
          ;;
        --body-file)
          body_file="${2:-}"
          shift 2
          ;;
        --repo)
          repo_arg="${2:-}"
          shift 2
          ;;
        --dry-run)
          dry_run="1"
          shift
          ;;
        -h|--help)
          usage
          exit 0
          ;;
        *)
          die "unknown option for comment: $1"
          ;;
      esac
    done

    [[ -n "$issue_number" ]] || die "--issue is required for comment"

    if [[ -n "$body" && -n "$body_file" ]]; then
      die "use either --body or --body-file, not both"
    fi

    if [[ -z "$body" && -z "$body_file" ]]; then
      die "comment body is required"
    fi

    if [[ -n "$body_file" && ! -f "$body_file" ]]; then
      die "body file not found: $body_file"
    fi

    require_cmd gh

    cmd=(gh issue comment "$issue_number")
    if [[ -n "$repo_arg" ]]; then
      cmd+=(-R "$repo_arg")
    fi
    if [[ -n "$body" ]]; then
      cmd+=(--body "$body")
    else
      cmd+=(--body-file "$body_file")
    fi

    run_cmd "${cmd[@]}"
    ;;

  close)
    issue_number=""
    reason="completed"
    comment=""
    comment_file=""

    while [[ $# -gt 0 ]]; do
      case "${1:-}" in
        --issue)
          issue_number="${2:-}"
          shift 2
          ;;
        --reason)
          reason="${2:-}"
          shift 2
          ;;
        --comment)
          comment="${2:-}"
          shift 2
          ;;
        --comment-file)
          comment_file="${2:-}"
          shift 2
          ;;
        --repo)
          repo_arg="${2:-}"
          shift 2
          ;;
        --dry-run)
          dry_run="1"
          shift
          ;;
        -h|--help)
          usage
          exit 0
          ;;
        *)
          die "unknown option for close: $1"
          ;;
      esac
    done

    [[ -n "$issue_number" ]] || die "--issue is required for close"

    if [[ "$reason" != "completed" && "$reason" != "not planned" ]]; then
      die "--reason must be one of: completed, not planned"
    fi

    if [[ -n "$comment" && -n "$comment_file" ]]; then
      die "use either --comment or --comment-file, not both"
    fi

    if [[ -n "$comment_file" && ! -f "$comment_file" ]]; then
      die "comment file not found: $comment_file"
    fi

    require_cmd gh

    cmd=(gh issue close "$issue_number")
    if [[ -n "$repo_arg" ]]; then
      cmd+=(-R "$repo_arg")
    fi
    cmd+=(--reason "$reason")

    if [[ -n "$comment" ]]; then
      cmd+=(--comment "$comment")
    elif [[ -n "$comment_file" ]]; then
      comment_text="$(cat "$comment_file")"
      cmd+=(--comment "$comment_text")
    fi

    run_cmd "${cmd[@]}"
    ;;

  reopen)
    issue_number=""
    comment=""
    comment_file=""

    while [[ $# -gt 0 ]]; do
      case "${1:-}" in
        --issue)
          issue_number="${2:-}"
          shift 2
          ;;
        --comment)
          comment="${2:-}"
          shift 2
          ;;
        --comment-file)
          comment_file="${2:-}"
          shift 2
          ;;
        --repo)
          repo_arg="${2:-}"
          shift 2
          ;;
        --dry-run)
          dry_run="1"
          shift
          ;;
        -h|--help)
          usage
          exit 0
          ;;
        *)
          die "unknown option for reopen: $1"
          ;;
      esac
    done

    [[ -n "$issue_number" ]] || die "--issue is required for reopen"

    if [[ -n "$comment" && -n "$comment_file" ]]; then
      die "use either --comment or --comment-file, not both"
    fi

    if [[ -n "$comment_file" && ! -f "$comment_file" ]]; then
      die "comment file not found: $comment_file"
    fi

    require_cmd gh

    cmd=(gh issue reopen "$issue_number")
    if [[ -n "$repo_arg" ]]; then
      cmd+=(-R "$repo_arg")
    fi

    if [[ -n "$comment" ]]; then
      cmd+=(--comment "$comment")
    elif [[ -n "$comment_file" ]]; then
      comment_text="$(cat "$comment_file")"
      cmd+=(--comment "$comment_text")
    fi

    run_cmd "${cmd[@]}"
    ;;

  -h|--help)
    usage
    ;;

  *)
    die "unknown subcommand: $subcommand"
    ;;
esac
