#!/usr/bin/env -S zsh -f

if [[ -n ${_qb_mysql_loaded-} ]]; then
  return 0 2>/dev/null || exit 0
fi
typeset -gr _qb_mysql_loaded=1

typeset -gr _qb_mysql_file="${${(%):-%x}:A}"
typeset -gr _qb_mysql_dir="${_qb_mysql_file:h}"
typeset -gr _qb_mysql_project_dir="${_qb_mysql_dir:h}"
typeset -gr _qb_mysql_env="${_qb_mysql_project_dir}/qb-mysql.env"

if [[ -z "${CODEX_HOME:-}" ]]; then
  export CODEX_HOME="${_qb_mysql_project_dir:h:h:h}"
fi

if ! typeset -f codex_mysql_run >/dev/null 2>&1; then
  source "${CODEX_HOME%/}/scripts/db/_codex-mysql.zsh"
fi

qb-mysql() {
  emulate -L zsh
  setopt localoptions pipe_fail nounset

  codex_mysql_run 'QB' "$_qb_mysql_env" "$@"
}
