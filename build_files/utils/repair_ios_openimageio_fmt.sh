#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../.." && pwd)"
oiio_detail_dir="${1:-${repo_root}/lib/ios_arm64/openimageio/include/OpenImageIO/detail/fmt}"

if [[ ! -d "${oiio_detail_dir}" ]]; then
  printf 'OpenImageIO fmt detail directory not found: %s\n' "${oiio_detail_dir}" >&2
  exit 0
fi

mkdir -p "${oiio_detail_dir}"

headers=(
  base.h
  chrono.h
  core.h
  format.h
  format-inl.h
  ostream.h
  printf.h
  ranges.h
  std.h
)

for header in "${headers[@]}"; do
  cat > "${oiio_detail_dir}/${header}" <<EOF
#pragma once
#include <fmt/${header}>
EOF
done
