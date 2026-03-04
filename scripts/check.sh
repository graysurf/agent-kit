#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd "${script_dir}/.." && pwd -P)"
export CHECK_REPO_ROOT="$repo_root"

source "${repo_root}/scripts/lib/check/dispatch.sh"
source "${repo_root}/scripts/lib/check/tasks.sh"

check_main "$@"
