#!/usr/bin/env -S zsh -f

# repo_root_from_script_path <script_path>
# Resolve repo root from a script path. Falls back to the script parent-parent.
repo_root_from_script_path() {
  emulate -L zsh
  setopt pipe_fail nounset

  typeset script_path="${1:-}"
  [[ -n "$script_path" ]] || {
    print -u2 -r -- "error: repo_root_from_script_path requires <script_path>"
    return 2
  }

  typeset script_dir='' root_dir='' git_root=''
  script_dir="${script_path:A:h}"
  root_dir="${script_dir:h}"

  if command -v git >/dev/null 2>&1; then
    git_root="$(command git -C "$root_dir" rev-parse --show-toplevel 2>/dev/null || true)"
    if [[ -n "$git_root" ]]; then
      print -r -- "$git_root"
      return 0
    fi
  fi

  print -r -- "$root_dir"
}
