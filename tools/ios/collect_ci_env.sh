#!/usr/bin/env bash
set -euo pipefail

out_dir="${1:-ci-env-probe}"
mkdir -p "$out_dir"

capture() {
  local name="$1"
  shift

  {
    printf '$'
    printf ' %q' "$@"
    printf '\n'
    "$@"
  } >"$out_dir/$name.txt" 2>&1 || true
}

write_summary() {
  local summary_path="$out_dir/SUMMARY.md"

  {
    printf '# iOS Environment Probe\n\n'
    printf -- '- Generated at: %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    printf -- '- Hostname: %s\n' "$(hostname 2>/dev/null || printf 'unknown')"
    printf -- '- Runner OS: %s\n' "${RUNNER_OS:-unknown}"
    printf -- '- Runner arch: %s\n' "${RUNNER_ARCH:-unknown}"
    printf -- '- Runner name: %s\n' "${RUNNER_NAME:-unknown}"
    printf -- '- Runner image: %s %s\n' "${ImageOS:-unknown}" "${ImageVersion:-unknown}"
    printf -- '- GitHub repository: %s\n' "${GITHUB_REPOSITORY:-unknown}"
    printf -- '- GitHub ref: %s\n' "${GITHUB_REF:-unknown}"
    printf -- '- GitHub SHA: %s\n' "${GITHUB_SHA:-unknown}"
    printf -- '- Xcode developer dir: %s\n' "$(xcode-select -p 2>/dev/null || printf 'unavailable')"
    printf -- '- iPhoneOS SDK version: %s\n' "$(xcrun --sdk iphoneos --show-sdk-version 2>/dev/null || printf 'unavailable')"
    printf -- '- iPhoneSimulator SDK version: %s\n' "$(xcrun --sdk iphonesimulator --show-sdk-version 2>/dev/null || printf 'unavailable')"
  } >"$summary_path"
}

capture system-uname uname -a
capture system-sw-vers sw_vers
capture system-hostname hostname
capture system-xcode-select xcode-select -p
capture xcode-version xcodebuild -version
capture xcode-sdks xcodebuild -showsdks
capture sdk-iphoneos-path xcrun --sdk iphoneos --show-sdk-path
capture sdk-iphoneos-version xcrun --sdk iphoneos --show-sdk-version
capture sdk-iphonesimulator-path xcrun --sdk iphonesimulator --show-sdk-path
capture sdk-iphonesimulator-version xcrun --sdk iphonesimulator --show-sdk-version
capture tool-git git --version
capture tool-python python3 --version
capture tool-cmake cmake --version
capture tool-clang clang --version
capture tool-xcodebuild xcodebuild -version -sdk
capture filesystem-developer-dir ls -la /Applications
capture filesystem-xcode-sdks ls -la "$(xcode-select -p 2>/dev/null || printf /Applications)/Platforms"
capture env-all printenv

python3 - <<'PY' "$out_dir"
import json
import os
import sys

out_dir = sys.argv[1]
interesting = [
    "CI",
    "DEVELOPER_DIR",
    "GITHUB_ACTION",
    "GITHUB_ACTIONS",
    "GITHUB_ACTOR",
    "GITHUB_EVENT_NAME",
    "GITHUB_REF",
    "GITHUB_REPOSITORY",
    "GITHUB_RUN_ATTEMPT",
    "GITHUB_RUN_ID",
    "GITHUB_RUN_NUMBER",
    "GITHUB_SHA",
    "ImageOS",
    "ImageVersion",
    "RUNNER_ARCH",
    "RUNNER_NAME",
    "RUNNER_OS",
    "RUNNER_TEMP",
    "RUNNER_TOOL_CACHE",
]

data = {key: os.environ.get(key, "") for key in interesting}
with open(os.path.join(out_dir, "env-selected.json"), "w", encoding="ascii") as handle:
    json.dump(data, handle, indent=2, sort_keys=True)
    handle.write("\n")
PY

write_summary
