#!/usr/bin/env -S zsh -f

if [[ -n ${_tun_psql_loaded-} ]]; then
  return 0 2>/dev/null || exit 0
fi
typeset -gr _tun_psql_loaded=1

typeset -gr _tun_psql_file="${${(%):-%x}:A}"
typeset -gr _tun_psql_dir="${_tun_psql_file:h}"
typeset -gr _tun_psql_project_dir="${_tun_psql_dir:h}"
typeset -gr _tun_psql_env="${_tun_psql_project_dir}/tun-psql.env"

if [[ -z "${CODEX_HOME:-}" ]]; then
  export CODEX_HOME="${_tun_psql_project_dir:h:h:h}"
fi

if ! typeset -f codex_psql_run >/dev/null 2>&1; then
  source "${CODEX_HOME%/}/scripts/db/_codex-psql.zsh"
fi

tun-psql() {
  emulate -L zsh
  setopt localoptions pipe_fail nounset

  codex_psql_run 'TUN' "$_tun_psql_env" "$@"
}
