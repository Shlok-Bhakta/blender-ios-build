#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -lt 3 ]; then
  printf 'usage: %s <dep> <artifact-root> <command> [args...]\n' "$0" >&2
  exit 2
fi

dep="$1"
artifact_root="$2"
shift 2

if [ -z "${GITHUB_REF_NAME:-}" ] || [ -z "${GITHUB_REPOSITORY:-}" ]; then
  printf 'GITHUB_REF_NAME and GITHUB_REPOSITORY are required\n' >&2
  exit 2
fi

cache_dir="${artifact_root}/${dep}-cache"
download_dir="${cache_dir}/download"
upload_dir="${cache_dir}/upload"
metadata_path="${cache_dir}/metadata.json"
cache_log="${cache_dir}/cache.log"

mkdir -p "${cache_dir}" "${download_dir}" "${upload_dir}"

python3 tools/ios/dep_bootstrap.py metadata \
  --branch "${GITHUB_REF_NAME}" \
  --dep "${dep}" \
  --output "${metadata_path}"

metadata_field() {
  python3 - "${metadata_path}" "$1" <<'PY'
import json
import sys
from pathlib import Path

metadata = json.loads(Path(sys.argv[1]).read_text(encoding="ascii"))
print(metadata[sys.argv[2]])
PY
}

release_tag="$(metadata_field release_tag)"
asset_name="$(metadata_field asset_name)"
manifest_asset_name="$(metadata_field manifest_asset_name)"
source_hash_type="$(metadata_field source_hash_type)"
source_hash="$(metadata_field source_hash)"
source_file="$(metadata_field source_file)"

{
  printf '[dep-cache][%s] release_tag=%s\n' "${dep}" "${release_tag}"
  printf '[dep-cache][%s] asset_name=%s\n' "${dep}" "${asset_name}"
  printf '[dep-cache][%s] source=%s:%s (%s)\n' "${dep}" "${source_hash_type}" "${source_hash}" "${source_file}"
} | tee "${cache_log}"

if gh release view "${release_tag}" -R "${GITHUB_REPOSITORY}" >/dev/null 2>&1; then
  if gh release download "${release_tag}" -R "${GITHUB_REPOSITORY}" -p "${asset_name}" -D "${download_dir}" >/dev/null 2>&1; then
    python3 tools/ios/dep_bootstrap.py extract --input "${download_dir}/${asset_name}"
    printf '[dep-cache][%s] restore-hit\n' "${dep}" | tee -a "${cache_log}"
    exit 0
  fi
fi

printf '[dep-cache][%s] restore-miss\n' "${dep}" | tee -a "${cache_log}"

printf '[dep-cache][%s] command=' "${dep}" | tee -a "${cache_log}" "${artifact_root}/${dep}-console.log"
printf '%q ' "$@" | tee -a "${cache_log}" "${artifact_root}/${dep}-console.log"
printf '\n' | tee -a "${cache_log}" "${artifact_root}/${dep}-console.log"

set +e
"$@" 2>&1 | tee -a "${cache_log}" "${artifact_root}/${dep}-console.log"
command_rc=${PIPESTATUS[0]}
set -e

if [ "${command_rc}" -ne 0 ]; then
  exit "${command_rc}"
fi

bundle_path="${upload_dir}/${asset_name}"
manifest_path="${upload_dir}/bundle-metadata.json"

python3 tools/ios/dep_bootstrap.py bundle \
  --branch "${GITHUB_REF_NAME}" \
  --dep "${dep}" \
  --output "${bundle_path}" \
  --metadata-output "${manifest_path}"

if ! gh release view "${release_tag}" -R "${GITHUB_REPOSITORY}" >/dev/null 2>&1; then
  gh release create "${release_tag}" \
    -R "${GITHUB_REPOSITORY}" \
    --target "${GITHUB_SHA}" \
    --title "${release_tag}" \
    --notes "Branch-scoped dependency bundles for ${GITHUB_REF_NAME}." \
    --prerelease
fi

gh release upload "${release_tag}" -R "${GITHUB_REPOSITORY}" --clobber \
  "${bundle_path}" \
  "${manifest_path}#${manifest_asset_name}"

printf '[dep-cache][%s] uploaded %s\n' "${dep}" "${asset_name}" | tee -a "${cache_log}"
