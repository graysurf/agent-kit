#!/usr/bin/env bash

lint_run_shell() {
  echo "lint: shell (bash/zsh)" >&2

  if ! command -v git >/dev/null 2>&1; then
    echo "error: git is required (for git ls-files)" >&2
    return 1
  fi
  if ! command -v zsh >/dev/null 2>&1; then
    echo "error: zsh is required (for zsh -n syntax checks)" >&2
    return 1
  fi

  local rc=0
  local -a bash_scripts=()
  local -a zsh_scripts=()
  local -a sh_missing_shebang=()
  local file=''
  local first_line=''

  while IFS= read -r -d '' file; do
    [[ -n "$file" ]] || continue
    case "$file" in
      shell_snapshots/*)
        continue
        ;;
    esac

    [[ -f "$file" ]] || continue

    first_line=''
    if ! IFS= read -r first_line <"$file"; then
      first_line=''
    fi

    if [[ "$file" == *.zsh ]]; then
      if ! lint_contains_path "$file" "${zsh_scripts[@]}"; then
        zsh_scripts+=("$file")
      fi
    fi

    if [[ "$first_line" == '#!'* ]]; then
      if [[ "$first_line" == *zsh* ]]; then
        if ! lint_contains_path "$file" "${zsh_scripts[@]}"; then
          zsh_scripts+=("$file")
        fi
      elif [[ "$first_line" == *bash* ]]; then
        if ! lint_contains_path "$file" "${bash_scripts[@]}"; then
          bash_scripts+=("$file")
        fi
      fi
    else
      if [[ "$file" == *.sh ]]; then
        sh_missing_shebang+=("$file")
      fi
    fi
  done < <(git ls-files -z)

  if [[ ${#sh_missing_shebang[@]} -gt 0 ]]; then
    echo "warning: skipping .sh without shebang (cannot infer bash vs zsh):" >&2
    printf '  - %s\n' "${sh_missing_shebang[@]}" >&2
  fi

  if [[ ${#bash_scripts[@]} -gt 0 ]]; then
    if ! command -v shellcheck >/dev/null 2>&1; then
      echo "error: shellcheck not found (required for bash lint)" >&2
      echo "hint: macOS: brew install shellcheck" >&2
      echo "hint: Ubuntu: sudo apt-get install -y shellcheck" >&2
      return 1
    fi

    echo "lint: shellcheck (bash scripts)" >&2
    set +e
    shellcheck -S error "${bash_scripts[@]}"
    local shellcheck_rc=$?
    set -e
    if [[ "$shellcheck_rc" -ne 0 ]]; then
      rc=1
    fi

    echo "lint: bash -n (syntax)" >&2
    for file in "${bash_scripts[@]}"; do
      set +e
      bash -n "$file"
      local bash_n_rc=$?
      set -e
      if [[ "$bash_n_rc" -ne 0 ]]; then
        rc=1
      fi
    done
  fi

  if [[ ${#zsh_scripts[@]} -gt 0 ]]; then
    echo "lint: zsh -n (syntax)" >&2
    for file in "${zsh_scripts[@]}"; do
      set +e
      zsh -n "$file"
      local zsh_n_rc=$?
      set -e
      if [[ "$zsh_n_rc" -ne 0 ]]; then
        rc=1
      fi
    done
  fi

  return "$rc"
}
