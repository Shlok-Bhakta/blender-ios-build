#!/usr/bin/env bash

set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This smoke loop requires macOS with Xcode command line tools." >&2
  exit 1
fi

if ! command -v xcrun >/dev/null 2>&1; then
  echo "xcrun not found. Install Xcode command line tools first." >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD_DIR="${BUILD_DIR:-${ROOT_DIR}/../build_ios-simulator}"
BUNDLE_PATH="${BUNDLE_PATH:-${BUILD_DIR}/bin/Blender.app}"
BUNDLE_ID="${BUNDLE_ID:-org.blenderfoundation.blender}"
SIM_DEVICE="${SIM_DEVICE:-booted}"
LAUNCH_WAIT_SECONDS="${LAUNCH_WAIT_SECONDS:-5}"
LOG_LOOKBACK_SECONDS="${LOG_LOOKBACK_SECONDS:-15}"
SURVIVAL_CHECKS="${SURVIVAL_CHECKS:-1 3 ${LAUNCH_WAIT_SECONDS}}"
BUILD_CMAKE_ARGS_DEFAULT='-G Ninja -DWITH_COMPILER_CCACHE=YES'
BUILD_CMAKE_ARGS_VALUE="${BUILD_CMAKE_ARGS:-${BUILD_CMAKE_ARGS_DEFAULT}}"

plist_read_raw() {
  local key="$1"
  plutil -extract "${key}" raw -o - "$2" 2>/dev/null || true
}

require_path() {
  local path="$1"
  if [[ ! -e "${path}" ]]; then
    echo "Required bundle path missing: ${path}" >&2
    exit 1
  fi
}

require_storyboard_resource() {
  local bundle_root="$1"
  local storyboard_name="$2"

  if [[ -z "${storyboard_name}" ]]; then
    return 0
  fi

  if [[ -e "${bundle_root}/${storyboard_name}.storyboardc" || -e "${bundle_root}/${storyboard_name}.storyboard" ]]; then
    return 0
  fi

  echo "Required storyboard resource missing: ${storyboard_name}" >&2
  exit 1
}

process_is_alive() {
  local sim_device="$1"
  local pid="$2"
  local snapshot

  snapshot="$(xcrun simctl spawn "${sim_device}" ps -axo pid,comm || true)"
  if [[ "${snapshot}" == *"${pid}"*"Blender"* ]]; then
    printf '%s' "${snapshot}"
    return 0
  fi

  printf '%s' "${snapshot}"
  return 1
}

if [[ "${SKIP_BUILD:-0}" != "1" ]]; then
  make -C "${ROOT_DIR}" ios-simulator all BUILD_CMAKE_ARGS="${BUILD_CMAKE_ARGS_VALUE}"
fi

if [[ ! -d "${BUNDLE_PATH}" ]]; then
  echo "Bundle not found: ${BUNDLE_PATH}" >&2
  exit 1
fi

info_plist="${BUNDLE_PATH}/Info.plist"
plutil -lint "${info_plist}"

require_path "${info_plist}"
require_path "${BUNDLE_PATH}/Assets/blender_icon.icns"
require_path "${BUNDLE_PATH}/Blender"

bundle_id_from_plist="$(plist_read_raw CFBundleIdentifier "${info_plist}")"
bundle_executable="$(plist_read_raw CFBundleExecutable "${info_plist}")"
launch_storyboard="$(plist_read_raw UILaunchStoryboardName "${info_plist}")"
main_storyboard="$(plist_read_raw UIMainStoryboardFile "${info_plist}")"

if [[ -n "${bundle_id_from_plist}" && "${bundle_id_from_plist}" != "${BUNDLE_ID}" ]]; then
  echo "Bundle identifier mismatch: expected ${BUNDLE_ID}, found ${bundle_id_from_plist}" >&2
  exit 1
fi

if [[ -n "${bundle_executable}" ]]; then
  require_path "${BUNDLE_PATH}/${bundle_executable}"
fi

require_storyboard_resource "${BUNDLE_PATH}" "${launch_storyboard}"
require_storyboard_resource "${BUNDLE_PATH}" "${main_storyboard}"

if [[ "${SIM_DEVICE}" == "booted" ]]; then
  if ! xcrun simctl bootstatus booted -b >/dev/null 2>&1; then
    echo "No booted simulator found. Set SIM_DEVICE to a device name or UDID first." >&2
    exit 1
  fi
else
  xcrun simctl boot "${SIM_DEVICE}" >/dev/null 2>&1 || true
  xcrun simctl bootstatus "${SIM_DEVICE}" -b >/dev/null
fi

xcrun simctl install "${SIM_DEVICE}" "${BUNDLE_PATH}"
xcrun simctl terminate "${SIM_DEVICE}" "${BUNDLE_ID}" >/dev/null 2>&1 || true

launch_output="$(xcrun simctl launch "${SIM_DEVICE}" "${BUNDLE_ID}")"
printf '%s\n' "${launch_output}"

launch_pid="${launch_output##*: }"
if [[ "${launch_pid}" =~ ^[0-9]+$ ]]; then
  last_check=0
  for check_at in ${SURVIVAL_CHECKS}; do
    if (( check_at <= last_check )); then
      continue
    fi

    sleep "$((check_at - last_check))"
    last_check="${check_at}"

    if process_snapshot="$(process_is_alive "${SIM_DEVICE}" "${launch_pid}")"; then
      echo "Blender stayed alive for ${check_at}s after launch."
    else
      echo "Blender exited before ${check_at}s elapsed." >&2
      printf '%s\n' "${process_snapshot}" >&2
      exit 1
    fi
  done
fi

if [[ "${SKIP_LOG_STREAM:-0}" != "1" ]]; then
  log_snapshot="$(xcrun simctl spawn "${SIM_DEVICE}" log show --last "${LOG_LOOKBACK_SECONDS}s" \
    --style compact --predicate 'process == "Blender"' || true)"
  printf '%s\n' "${log_snapshot}"

  if [[ "${log_snapshot}" == *"Blender iOS bootstrap:"* ]]; then
    echo "Found iOS bootstrap startup marker in logs."
  else
    echo "Did not find the iOS bootstrap startup marker in logs." >&2
  fi
fi

if [[ "${STREAM_LOGS:-0}" == "1" ]]; then
  xcrun simctl spawn "${SIM_DEVICE}" log stream --style compact --level debug \
    --predicate 'process == "Blender"'
fi
