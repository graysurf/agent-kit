#!/usr/bin/env bash

CHECK_MODES=(
  lint
  lint-shell
  lint-python
  markdown
  third-party
  contracts
  skills-layout
  env-bools
  docs
  entrypoint-ownership
  tests
  semgrep
  all
  pre-commit
)

check_mode_is_known() {
  local candidate="${1:-}"
  local mode=''
  for mode in "${CHECK_MODES[@]}"; do
    if [[ "$mode" == "$candidate" ]]; then
      return 0
    fi
  done
  return 1
}

check_mode_flag() {
  local mode="${1:-}"
  printf -- "--%s" "$mode"
}

check_print_modes() {
  printf '%s\n' "${CHECK_MODES[@]}"
}

