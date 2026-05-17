#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
local_setup="${script_dir}/scripts/setup-macos.sh"

if [[ -x "$local_setup" ]]; then
  exec "$local_setup" "$@"
fi

install_ref="${AGENT_KIT_INSTALL_REF:-main}"
setup_url="${AGENT_KIT_SETUP_URL:-https://raw.githubusercontent.com/graysurf/agent-kit/${install_ref}/scripts/setup-macos.sh}"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

curl -fsSL "$setup_url" -o "${tmp_dir}/setup-macos.sh"
chmod +x "${tmp_dir}/setup-macos.sh"
exec "${tmp_dir}/setup-macos.sh" "$@"
