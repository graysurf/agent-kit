#!/usr/bin/env -S zsh -f

# codex-tools loader (single source of truth)
#
# Usage (from anywhere):
#   source "$CODEX_HOME/scripts/codex-tools.sh"
#
# Contract:
# - Hard-fails with actionable errors when required tools are unavailable.
# - Sets/exports CODEX_HOME (if missing) and ensures repo-local tools are on PATH.

if [[ -n "${_codex_tools_loader_loaded-}" ]]; then
  return 0 2>/dev/null || exit 0
fi
typeset -gr _codex_tools_loader_loaded=1

_codex_tools_die() {
  emulate -L zsh
  setopt err_return no_unset

  local message="${1-}"
  if [[ -z "$message" ]]; then
    message="unknown error"
  fi

  print -u2 -r -- "error: ${message}"
  return 1 2>/dev/null || exit 1
}

_codex_tools_note() {
  emulate -L zsh
  setopt err_return no_unset
  print -u2 -r -- "$*"
}

if [[ -z "${ZSH_VERSION:-}" ]]; then
  _codex_tools_die "must be sourced in zsh (try: zsh -lc 'source <path>/scripts/codex-tools.sh')"
fi

# Resolve CODEX_HOME from this file location if missing.
if [[ -z "${CODEX_HOME:-}" ]]; then
  export CODEX_HOME="${${(%):-%x}:A:h:h}"
fi

if [[ -z "${CODEX_HOME:-}" || ! -d "${CODEX_HOME:-}" ]]; then
  _codex_tools_die "CODEX_HOME is not set or invalid; set CODEX_HOME to your codex-kit path (e.g. export CODEX_HOME=\"$HOME/.config/codex-kit\")"
fi

export CODEX_HOME

typeset -g _codex_bin_dir="${CODEX_HOME%/}/scripts/bin"
if [[ ! -d "$_codex_bin_dir" ]]; then
  _codex_tools_die "missing tools bin dir: ${_codex_bin_dir} (reinstall/update codex-kit)"
fi

if [[ ":${PATH}:" != *":${_codex_bin_dir}:"* ]]; then
  export PATH="${_codex_bin_dir}:${PATH}"
fi

# Validate required commands/functions are present after loading tools.
if ! command -v git-tools >/dev/null 2>&1; then
  _codex_tools_note "hint: expected executable: ${_codex_bin_dir}/git-tools"
  _codex_tools_note "hint: fix: chmod +x \"${_codex_bin_dir}/git-tools\""
  _codex_tools_die "required tool missing: git-tools"
fi

if ! command -v git-scope >/dev/null 2>&1; then
  _codex_tools_note "hint: expected executable: ${_codex_bin_dir}/git-scope"
  _codex_tools_note "hint: fix: chmod +x \"${_codex_bin_dir}/git-scope\""
  _codex_tools_die "required tool missing: git-scope"
fi

if ! command -v git >/dev/null 2>&1; then
  _codex_tools_die "required tool missing: git"
fi
