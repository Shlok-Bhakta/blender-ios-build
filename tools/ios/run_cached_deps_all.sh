#!/usr/bin/env bash
# Run the full Apple cross-deps chain with per-dependency GitHub Release cache
# (run_release_cached_dep.sh). Intended for CI; requires gh, cmake, ninja.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd -P)"
cd "$ROOT"

: "${IOS_DEPS_BUILD_DIR:?Set IOS_DEPS_BUILD_DIR}"
: "${IOS_DEPS_INSTALL_DIR:?Set IOS_DEPS_INSTALL_DIR}"
: "${IOS_HOST_BUILD_DIR:?Set IOS_HOST_BUILD_DIR}"
: "${IOS_HOST_INSTALL_DIR:?Set IOS_HOST_INSTALL_DIR}"

ARTIFACT_ROOT="${IOS_DEPS_ARTIFACT_ROOT:-artifacts/ios-deps}"
mkdir -p "$ARTIFACT_ROOT"

PY=(python3 "$ROOT/tools/ios/build_deps.py" --mode ios-simulator
  --generator Ninja
  --build-dir "$IOS_DEPS_BUILD_DIR"
  --install-dir "$IOS_DEPS_INSTALL_DIR"
  --host-build-dir "$IOS_HOST_BUILD_DIR"
  --host-install-dir "$IOS_HOST_INSTALL_DIR")

if [[ "${WITH_COMPILER_CCACHE:-}" == "ON" ]] || [[ "${WITH_COMPILER_CCACHE:-}" == "YES" ]]; then
  PY+=(--cmake-arg=-DWITH_COMPILER_CCACHE=ON)
fi

run_one() {
  local short=$1
  local target=$2
  local logdir="${ARTIFACT_ROOT}/${short}-logs"
  local manifest="${ARTIFACT_ROOT}/${short}-manifest.json"
  mkdir -p "$logdir"
  echo ""
  echo "============================================"
  echo "[dep] === Building ${short} (${target}) ==="
  echo "============================================"
  bash "$ROOT/tools/ios/run_release_cached_dep.sh" "$short" "$ARTIFACT_ROOT" \
    "${PY[@]}" \
    --build-target "$target" \
    --log-dir "$logdir" \
    --manifest-path "$manifest"
}

# Order matches upstream ios-deps.yml (dependency order).
while read -r short target; do
  [[ -z "$short" || "$short" == \#* ]] && continue
  run_one "$short" "$target"
done <<'DEPS'
zlib external_zlib
openal external_openal
blosc external_blosc
png external_png
jpeg external_jpeg
tiff external_tiff
imath external_imath
openjph external_openjph
openexr external_openexr
brotli external_brotli
freetype external_freetype
bzip2 external_bzip2
lzma external_lzma
deflate external_deflate
fmt external_fmt
robinmap external_robinmap
pugixml external_pugixml
xml2 external_xml2
expat external_expat
pystring external_pystring
yamlcpp external_yamlcpp
minizipng external_minizipng
ffi external_ffi
alembic external_alembic
openjpeg external_openjpeg
webp external_webp
gmp external_gmp
tbb external_tbb
opensubdiv external_opensubdiv
ogg external_ogg
opus external_opus
vorbis external_vorbis
flac external_flac
sndfile external_sndfile
ffmpeg external_ffmpeg
x264 external_x264
x265 external_x265
vpx external_vpx
lame external_lame
aom external_aom
fftw external_fftw
python external_python
pybind11 external_pybind11
nanobind external_nanobind
manifold external_manifold
cython external_cython
numpy external_numpy
libheif external_libheif
opencolorio external_opencolorio
openimageio external_openimageio
openvdb external_openvdb
shaderc external_shaderc
spirv-reflect external_spirv_reflect
DEPS
