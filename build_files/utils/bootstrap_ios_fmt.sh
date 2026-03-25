#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
  printf 'This script must run on macOS.\n' >&2
  exit 1
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../.." && pwd)"
target_dir="${1:-${repo_root}/lib/ios_arm64/fmt}"

fmt_version="${FMT_VERSION:-12.1.0}"
ios_deployment_target="${IOS_DEPLOYMENT_TARGET:-16.0}"
work_dir="${FMT_BOOTSTRAP_WORK_DIR:-${repo_root}/build_fmt_ios_bootstrap}"
source_dir="${work_dir}/fmt-${fmt_version}"
build_dir="${source_dir}/build_ios"
install_dir="${work_dir}/out"

rm -rf "${source_dir}" "${install_dir}"
mkdir -p "${work_dir}" "${target_dir}"

curl -L "https://github.com/fmtlib/fmt/archive/refs/tags/${fmt_version}.tar.gz" | tar xz -C "${work_dir}"

cmake -S "${source_dir}" -B "${build_dir}" \
  -DCMAKE_SYSTEM_NAME=iOS \
  -DCMAKE_OSX_ARCHITECTURES=arm64 \
  -DCMAKE_OSX_DEPLOYMENT_TARGET="${ios_deployment_target}" \
  -DCMAKE_INSTALL_PREFIX="${install_dir}" \
  -DFMT_TEST=OFF \
  -DFMT_DOC=OFF \
  -DBUILD_SHARED_LIBS=OFF

cmake --build "${build_dir}" --config Release --parallel "${FMT_BUILD_JOBS:-$(sysctl -n hw.logicalcpu)}"
cmake --install "${build_dir}" --config Release

rm -rf "${target_dir}/include" "${target_dir}/lib"
mkdir -p "${target_dir}"
cp -R "${install_dir}/include" "${target_dir}/include"
cp -R "${install_dir}/lib" "${target_dir}/lib"
