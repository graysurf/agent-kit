#!/usr/bin/env bash
set -euo pipefail

die() {
	echo "$1" >&2
	exit 1
}

trim() {
	local s="$1"
	s="${s#"${s%%[![:space:]]*}"}"
	s="${s%"${s##*[![:space:]]}"}"
	printf "%s" "$s"
}

usage() {
	cat >&2 <<'EOF'
Usage:
  gql.sh [--env <name> | --url <url>] <operation.graphql> [variables.json]

Options:
  -e, --env <name>       Use endpoint preset from endpoints.env (e.g. local/staging/dev)
  -u, --url <url>        Use an explicit GraphQL endpoint URL
      --config-dir <dir> Directory that contains endpoints.env (defaults to operation file's directory)
      --list-envs         Print available env names from endpoints.env, then exit

Environment variables:
  GQL_URL        Explicit GraphQL endpoint URL (overridden by --env/--url)
  ACCESS_TOKEN   If set, sends Authorization: Bearer <token>

Notes:
  - Project presets live under: setup/graphql/endpoints.env (+ optional endpoints.local.env overrides).
  - Prefers xh or HTTPie if available; falls back to curl (requires jq).
  - Prints response body only.
EOF
}

env_name=""
explicit_url=""
config_dir=""
list_envs=false

while [[ $# -gt 0 ]]; do
	case "$1" in
		-h|--help)
			usage
			exit 0
			;;
		-e|--env)
			env_name="${2:-}"
			[[ -n "$env_name" ]] || die "Missing value for --env"
			shift 2
			;;
		-u|--url)
			explicit_url="${2:-}"
			[[ -n "$explicit_url" ]] || die "Missing value for --url"
			shift 2
			;;
		--config-dir)
			config_dir="${2:-}"
			[[ -n "$config_dir" ]] || die "Missing value for --config-dir"
			shift 2
			;;
		--list-envs)
			list_envs=true
			shift
			;;
		--)
			shift
			break
			;;
		-*)
			die "Unknown option: $1"
			;;
		*)
			break
			;;
	esac
done

operation_file="${1:-}"
variables_file="${2:-}"

declare -A endpoint_map=()
gql_env_default=""

parse_endpoints_file() {
	local file="$1"
	[[ -f "$file" ]] || return 0

	while IFS= read -r raw_line || [[ -n "$raw_line" ]]; do
		raw_line="${raw_line%$'\r'}"
		local line
		line="$(trim "$raw_line")"
		[[ -z "$line" ]] && continue
		[[ "$line" == \#* ]] && continue

		if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
			local key="${BASH_REMATCH[1]}"
			local value
			value="$(trim "${BASH_REMATCH[2]}")"

			if [[ "$value" =~ ^\"(.*)\"$ ]]; then
				value="${BASH_REMATCH[1]}"
			elif [[ "$value" =~ ^\'(.*)\'$ ]]; then
				value="${BASH_REMATCH[1]}"
			fi

			case "$key" in
				GQL_ENV_DEFAULT)
					gql_env_default="$value"
					;;
				GQL_URL_*)
					local env_key="${key#GQL_URL_}"
					env_key="${env_key,,}"
					endpoint_map["$env_key"]="$value"
					;;
			esac
		fi
	done < "$file"
}

list_available_envs() {
	local file="$1"
	[[ -f "$file" ]] || return 0

	while IFS= read -r raw_line || [[ -n "$raw_line" ]]; do
		raw_line="${raw_line%$'\r'}"
		local line
		line="$(trim "$raw_line")"
		[[ "$line" =~ ^GQL_URL_([A-Za-z0-9_]+)= ]] || continue
		printf "%s\n" "${BASH_REMATCH[1],,}"
	done < "$file" | sort -u
}

resolve_endpoints_dir() {
	if [[ -n "$config_dir" ]]; then
		printf "%s" "$config_dir"
		return 0
	fi

	if [[ -n "$operation_file" ]]; then
		local op_dir
		if op_dir="$(cd "$(dirname "$operation_file")" 2>/dev/null && pwd -P)"; then
			printf "%s" "$op_dir"
			return 0
		fi
	fi

	if [[ -d "setup/graphql" ]]; then
		printf "%s" "setup/graphql"
		return 0
	fi

	return 1
}

endpoints_dir="$(resolve_endpoints_dir 2>/dev/null || true)"
endpoints_file=""
endpoints_local_file=""

if [[ -n "$endpoints_dir" && -f "$endpoints_dir/endpoints.env" ]]; then
	endpoints_file="$endpoints_dir/endpoints.env"
	endpoints_local_file="$endpoints_dir/endpoints.local.env"
elif [[ -f "setup/graphql/endpoints.env" ]]; then
	endpoints_file="setup/graphql/endpoints.env"
	endpoints_local_file="setup/graphql/endpoints.local.env"
fi

if [[ "$list_envs" == "true" ]]; then
	[[ -n "$endpoints_file" ]] || die "endpoints.env not found (expected under setup/graphql/)"
	list_available_envs "$endpoints_file"
	exit 0
fi

if [[ -z "$operation_file" ]]; then
	usage
	exit 1
fi

if [[ ! -f "$operation_file" ]]; then
	die "Operation file not found: $operation_file"
fi

if [[ -n "$variables_file" && ! -f "$variables_file" ]]; then
	die "Variables file not found: $variables_file"
fi

if [[ -n "$endpoints_file" ]]; then
	parse_endpoints_file "$endpoints_file"
	if [[ -f "$endpoints_local_file" ]]; then
		parse_endpoints_file "$endpoints_local_file"
	fi
fi

access_token="${ACCESS_TOKEN:-}"
gql_url=""

if [[ -n "$explicit_url" ]]; then
	gql_url="$explicit_url"
elif [[ "$env_name" =~ ^https?:// ]]; then
	gql_url="$env_name"
elif [[ -n "$env_name" ]]; then
	env_key="${env_name,,}"
	gql_url="${endpoint_map[$env_key]:-}"
	if [[ -z "$gql_url" ]]; then
		available_envs="$(list_available_envs "${endpoints_file:-/dev/null}" | tr '\n' ' ')"
		available_envs="$(trim "$available_envs")"
		die "Unknown --env '$env_name' (available: ${available_envs:-none})"
	fi
elif [[ -n "${GQL_URL:-}" ]]; then
	gql_url="$GQL_URL"
elif [[ -n "$gql_env_default" ]]; then
	env_key="${gql_env_default,,}"
	gql_url="${endpoint_map[$env_key]:-}"
	[[ -n "$gql_url" ]] || die "GQL_ENV_DEFAULT is '$gql_env_default' but no matching GQL_URL_* was found."
else
	gql_url="http://localhost:6700/graphql"
fi

if command -v xh >/dev/null 2>&1; then
	args=(--check-status --pretty=none --print=b --json POST "$gql_url")

	if [[ -n "$access_token" ]]; then
		args+=("Authorization:Bearer $access_token")
	fi

	args+=("query=@$operation_file")

	if [[ -n "$variables_file" ]]; then
		args+=("variables:=@$variables_file")
	fi

	xh "${args[@]}"
	exit 0
fi

if command -v http >/dev/null 2>&1; then
	args=(--check-status --pretty=none --print=b --json POST "$gql_url")

	if [[ -n "$access_token" ]]; then
		args+=("Authorization:Bearer $access_token")
	fi

	args+=("query=@$operation_file")

	if [[ -n "$variables_file" ]]; then
		args+=("variables:=@$variables_file")
	fi

	http "${args[@]}"
	exit 0
fi

if ! command -v curl >/dev/null 2>&1; then
	echo "Missing HTTP client: xh, http, or curl is required." >&2
	exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
	echo "curl fallback requires jq." >&2
	exit 1
fi

query="$(cat "$operation_file")"

if [[ -n "$variables_file" ]]; then
	payload="$(jq -n --arg query "$query" --argjson variables "$(cat "$variables_file")" '{query:$query,variables:$variables}')"
else
	payload="$(jq -n --arg query "$query" '{query:$query}')"
fi

curl_args=(-sS -H "Content-Type: application/json")
if [[ -n "$access_token" ]]; then
	curl_args+=(-H "Authorization: Bearer $access_token")
fi

curl "${curl_args[@]}" -d "$payload" "$gql_url"
