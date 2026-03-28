#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -lt 4 ]; then
  printf 'usage: %s <label> <interval-seconds> <log-path> <command> [args...]\n' "$0" >&2
  exit 2
fi

label="$1"
interval_seconds="$2"
log_path="$3"
shift 3

mkdir -p "$(dirname "$log_path")"

timestamp() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

printf '[start][%s] %s\n' "$label" "$(timestamp)" | tee "$log_path"
printf '[command][%s] ' "$label" | tee -a "$log_path"
printf '%q ' "$@" | tee -a "$log_path"
printf '\n' | tee -a "$log_path"

heartbeat() {
  while true; do
    sleep "$interval_seconds"
    printf '[heartbeat][%s] %s still running\n' "$label" "$(timestamp)"
  done
}

heartbeat | tee -a "$log_path" &
heartbeat_pid=$!

set +e
"$@" 2>&1 | tee -a "$log_path"
command_rc=${PIPESTATUS[0]}
set -e

kill "$heartbeat_pid" >/dev/null 2>&1 || true
wait "$heartbeat_pid" 2>/dev/null || true

printf '[end][%s] %s exit=%s\n' "$label" "$(timestamp)" "$command_rc" | tee -a "$log_path"
exit "$command_rc"
