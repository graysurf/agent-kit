#!/usr/bin/env -S zsh -f

setopt pipe_fail err_exit nounset

typeset -gr SCRIPT_PATH="${0:A}"
typeset -gr SCRIPT_NAME="${SCRIPT_PATH:t}"
typeset -gr SCRIPT_HINT="scripts/$SCRIPT_NAME"
typeset -gr SCRIPT_DIR="${SCRIPT_PATH:h}"
typeset -gr COMMON_LIB="${SCRIPT_DIR}/lib/zsh-common.zsh"

[[ -f "$COMMON_LIB" ]] || {
  print -u2 -r -- "error: missing shared zsh library: $COMMON_LIB"
  exit 2
}
source "$COMMON_LIB"

# print_usage: Print CLI usage/help.
print_usage() {
  emulate -L zsh
  setopt pipe_fail nounset

  print -r -- "Usage: $SCRIPT_HINT [-h|--help] [--check|--write]"
  print -r -- ""
  print -r -- "Runs repo-local shell style fixers (check or write)."
  print -r -- ""
  print -r -- "Modes:"
  print -r -- "  --check: Exit 1 if any fixer would change files (default)"
  print -r -- "  --write: Apply changes in-place"
}

# main [args...]
main() {
  emulate -L zsh
  setopt pipe_fail err_return nounset

  typeset -A opts=()
  zparseopts -D -E -A opts -- h -help -check -write || return 2

  if (( ${+opts[-h]} || ${+opts[--help]} )); then
    print_usage
    return 0
  fi

  typeset mode='check'
  if (( ${+opts[--write]} )); then
    mode='write'
  elif (( ${+opts[--check]} )); then
    mode='check'
  fi

  typeset root_dir=''
  root_dir="$(repo_root_from_script_path "$SCRIPT_PATH")"
  builtin cd "$root_dir" || return 1

  typeset quotes_fixer="$root_dir/scripts/fix-typeset-empty-string-quotes.zsh"
  typeset init_fixer="$root_dir/scripts/fix-zsh-typeset-initializers.zsh"

  [[ -x "$quotes_fixer" ]] || { print -u2 -r -- "error: missing fixer: $quotes_fixer"; return 2 }
  [[ -x "$init_fixer" ]] || { print -u2 -r -- "error: missing fixer: $init_fixer"; return 2 }

  typeset rc=0
  if [[ "$mode" == "write" ]]; then
    if ! "$quotes_fixer" --write; then
      rc=1
    fi
    if ! "$init_fixer" --write; then
      rc=1
    fi
    return "$rc"
  fi

  if ! "$quotes_fixer" --check; then
    rc=1
  fi
  if ! "$init_fixer" --check; then
    rc=1
  fi

  return "$rc"
}

main "$@"
