#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd "${script_dir}/.." && pwd -P)"
export LINT_REPO_ROOT="$repo_root"

source "${repo_root}/scripts/lib/lint/common.sh"
source "${repo_root}/scripts/lib/lint/shell.sh"
source "${repo_root}/scripts/lib/lint/python.sh"
source "${repo_root}/scripts/lib/lint/dispatch.sh"

lint_main "$@"
