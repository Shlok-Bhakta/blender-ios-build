#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
  printf 'This script must run on macOS.\n' >&2
  exit 1
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../.." && pwd)"
target_dir="${1:-${repo_root}/lib/ios_arm64/eigen}"

eigen_version="${EIGEN_VERSION:-8a1083e9bf41b91fdea6546681f806154efdc25a}"
work_dir="${EIGEN_BOOTSTRAP_WORK_DIR:-${repo_root}/build_eigen_ios_bootstrap}"
source_dir="${work_dir}/eigen-${eigen_version}"
config_dir="${target_dir}/share/eigen3/cmake"

rm -rf "${source_dir}"
mkdir -p "${work_dir}" "${target_dir}/include/eigen3" "${config_dir}"

curl -L "https://gitlab.com/libeigen/eigen/-/archive/${eigen_version}/eigen-${eigen_version}.tar.gz" | tar xz -C "${work_dir}"

rm -rf "${target_dir}/include/eigen3/Eigen" "${target_dir}/include/eigen3/unsupported"
cp -R "${source_dir}/Eigen" "${target_dir}/include/eigen3/Eigen"
if [[ -d "${source_dir}/unsupported" ]]; then
  cp -R "${source_dir}/unsupported" "${target_dir}/include/eigen3/unsupported"
fi
if [[ -f "${source_dir}/signature_of_eigen3_matrix_library" ]]; then
  cp "${source_dir}/signature_of_eigen3_matrix_library" "${target_dir}/include/eigen3/"
fi

cat > "${config_dir}/Eigen3Config.cmake" <<'EOF'
get_filename_component(PACKAGE_PREFIX_DIR "${CMAKE_CURRENT_LIST_DIR}/../../.." ABSOLUTE)
if(NOT TARGET Eigen3::Eigen)
  add_library(Eigen3::Eigen INTERFACE IMPORTED)
  set_target_properties(Eigen3::Eigen PROPERTIES
    INTERFACE_INCLUDE_DIRECTORIES "${PACKAGE_PREFIX_DIR}/include/eigen3")
endif()
set(Eigen3_FOUND TRUE)
EOF

cat > "${config_dir}/Eigen3ConfigVersion.cmake" <<'EOF'
set(PACKAGE_VERSION "5.0.1")
set(PACKAGE_VERSION_COMPATIBLE TRUE)
set(PACKAGE_VERSION_EXACT TRUE)
EOF
