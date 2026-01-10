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

typeset -g _codex_env_file="${CODEX_HOME%/}/scripts/env.zsh"
if [[ -f "$_codex_env_file" ]]; then
  # shellcheck disable=SC1090
  source "$_codex_env_file" || _codex_tools_die "failed to source ${_codex_env_file}"
fi

typeset -g _codex_bin_dir="${CODEX_HOME%/}/scripts/commands"
if [[ ! -d "$_codex_bin_dir" ]]; then
  _codex_tools_note "missing tools bin dir: ${_codex_bin_dir} (creating)"
  mkdir -p -- "$_codex_bin_dir" || _codex_tools_die "failed to create tools bin dir: ${_codex_bin_dir}"
fi

if [[ ":${PATH}:" != *":${_codex_bin_dir}:"* ]]; then
  export PATH="${_codex_bin_dir}:${PATH}"
fi

typeset -g ZDOTDIR="${ZDOTDIR:-$HOME/.config/zsh}"
export ZDOTDIR
export ZSH_CACHE_DIR="${ZSH_CACHE_DIR:-$ZDOTDIR/cache}"

typeset -g _codex_wrapper_dir="${ZSH_CACHE_DIR%/}/wrappers/bin"
typeset -g _codex_bundler="${CODEX_HOME%/}/scripts/build/bundle-wrapper.zsh"

_codex_tools_bundle() {
  emulate -L zsh
  setopt err_return no_unset

  local name="${1-}"
  local entry="${2-}"
  local wrapper="${_codex_wrapper_dir%/}/${name}"
  local output="${_codex_bin_dir%/}/${name}"

  [[ -n "$name" && -n "$entry" ]] || return 1
  [[ -x "$output" ]] && return 0
  [[ -f "$wrapper" ]] || return 1

  if [[ ! -f "$_codex_bundler" ]]; then
    _codex_tools_die "missing bundler: ${_codex_bundler}"
  fi

  _codex_tools_note "bundling ${name} from ${wrapper}"
  zsh -f "$_codex_bundler" --input "$wrapper" --output "$output" --entry "$entry" \
    || _codex_tools_die "failed to bundle ${name}"
}

_codex_tools_require() {
  emulate -L zsh
  setopt err_return no_unset

  local name="${1-}"
  local entry="${2-}"
  local output="${_codex_bin_dir%/}/${name}"

  if ! command -v "$name" >/dev/null 2>&1; then
    _codex_tools_bundle "$name" "$entry" || {
      _codex_tools_note "hint: expected executable: ${output}"
      _codex_tools_note "hint: fix: chmod +x \"${output}\""
      _codex_tools_die "required tool missing: ${name}"
    }
  fi
}

# Validate required commands/functions are present after loading tools.
_codex_tools_require "git-tools" "git-tools"
_codex_tools_require "git-scope" "git-scope"

if ! command -v git >/dev/null 2>&1; then
  _codex_tools_die "required tool missing: git"
fi
