#!/usr/bin/env -S zsh -f

if [[ -n ${_tun_mssql_loaded-} ]]; then
  return 0 2>/dev/null || exit 0
fi
typeset -gr _tun_mssql_loaded=1

typeset -gr _tun_mssql_file="${${(%):-%x}:A}"
typeset -gr _tun_mssql_dir="${_tun_mssql_file:h}"
typeset -gr _tun_mssql_project_dir="${_tun_mssql_dir:h}"
typeset -gr _tun_mssql_env="${_tun_mssql_project_dir}/tun-mssql.env"

if [[ -z "${CODEX_HOME:-}" ]]; then
  export CODEX_HOME="${_tun_mssql_project_dir:h:h:h}"
fi

if ! typeset -f codex_mssql_run >/dev/null 2>&1; then
  source "${CODEX_HOME%/}/scripts/db-connect/mssql.zsh"
fi

tun-mssql() {
  emulate -L zsh
  setopt localoptions pipe_fail nounset

  codex_mssql_run 'TUN' "$_tun_mssql_env" "$@"
}
