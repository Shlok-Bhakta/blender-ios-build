#!/usr/bin/env bash
set -euo pipefail

workflow="${1:-build-blender-ios.yml}"
branch="${2:-main}"
repo="${3:-${GH_REPO:-}}"
interval="${POLL_INTERVAL_SECONDS:-300}"

get_latest_run() {
  local gh_args=(
    run list
    --workflow "$workflow"
    --branch "$branch"
    --limit 1
    --json databaseId,status,conclusion,url,displayTitle,createdAt
  )

  if [[ -n "$repo" ]]; then
    gh_args+=(--repo "$repo")
  fi

  gh "${gh_args[@]}"
}

parse_field() {
  local field="$1"
  python3 -c 'import json,sys; data=json.load(sys.stdin); print(data[0].get(sys.argv[1], "") if data else "")' "$field"
}

run_json="$(get_latest_run)"
run_id="$(printf '%s' "$run_json" | parse_field databaseId)"

if [[ -z "$run_id" ]]; then
  if [[ -n "$repo" ]]; then
    printf 'No runs found for %s on %s in %s\n' "$workflow" "$branch" "$repo"
  else
    printf 'No runs found for %s on %s\n' "$workflow" "$branch"
  fi
  exit 2
fi

while true; do
  run_json="$(get_latest_run)"
  current_id="$(printf '%s' "$run_json" | parse_field databaseId)"
  status="$(printf '%s' "$run_json" | parse_field status)"
  conclusion="$(printf '%s' "$run_json" | parse_field conclusion)"
  url="$(printf '%s' "$run_json" | parse_field url)"
  title="$(printf '%s' "$run_json" | parse_field displayTitle)"
  created_at="$(printf '%s' "$run_json" | parse_field createdAt)"

  if [[ "$current_id" != "$run_id" ]]; then
    run_id="$current_id"
  fi

  if [[ "$status" == "completed" ]]; then
    printf 'Run %s finished: %s (%s)\n%s\nStarted: %s\n' "$run_id" "$title" "$conclusion" "$url" "$created_at"
    if [[ "$conclusion" == "success" ]]; then
      exit 0
    fi
    exit 1
  fi

  sleep "$interval"
done
