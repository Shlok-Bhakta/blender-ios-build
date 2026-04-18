#!/usr/bin/env bash
# Run the full Apple cross-deps chain with per-dependency GitHub Release cache.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd -P)"
cd "$ROOT"

: "${APPLE_TARGET_DEVICE:?Set APPLE_TARGET_DEVICE}"
: "${IOS_DEPS_BUILD_DIR:?Set IOS_DEPS_BUILD_DIR}"
: "${IOS_DEPS_INSTALL_DIR:?Set IOS_DEPS_INSTALL_DIR}"
: "${IOS_HOST_BUILD_DIR:?Set IOS_HOST_BUILD_DIR}"
: "${IOS_HOST_INSTALL_DIR:?Set IOS_HOST_INSTALL_DIR}"
: "${GITHUB_REF_NAME:?Set GITHUB_REF_NAME}"
: "${GITHUB_REPOSITORY:?Set GITHUB_REPOSITORY}"

case "${APPLE_TARGET_DEVICE}" in
  ios|ios-simulator)
    deps_mode="${APPLE_TARGET_DEVICE}"
    ;;
  *)
    printf 'APPLE_TARGET_DEVICE must be ios or ios-simulator, got %s\n' "${APPLE_TARGET_DEVICE}" >&2
    exit 2
    ;;
esac

ARTIFACT_ROOT="${IOS_DEPS_ARTIFACT_ROOT:-artifacts/ios-deps}"
RESTORE_ROOT="${ARTIFACT_ROOT}/batch-restore"
RESTORE_DOWNLOAD_DIR="${RESTORE_ROOT}/download"
RELEASE_ASSETS_FILE="${RESTORE_ROOT}/release-assets.txt"
MAX_EXTRACT_JOBS="${DEP_EXTRACT_JOBS:-8}"

mkdir -p "$ARTIFACT_ROOT"
rm -rf "$RESTORE_ROOT"
mkdir -p "$RESTORE_DOWNLOAD_DIR"

PY=(python3 "$ROOT/tools/ios/build_deps.py" --mode "$deps_mode"
  --generator Ninja
  --build-dir "$IOS_DEPS_BUILD_DIR"
  --install-dir "$IOS_DEPS_INSTALL_DIR"
  --host-build-dir "$IOS_HOST_BUILD_DIR"
  --host-install-dir "$IOS_HOST_INSTALL_DIR")

if [[ "${WITH_COMPILER_CCACHE:-}" == "ON" ]] || [[ "${WITH_COMPILER_CCACHE:-}" == "YES" ]]; then
  PY+=(--cmake-arg=-DWITH_COMPILER_CCACHE=ON)
fi

json_field() {
  python3 - "$1" "$2" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="ascii"))
value = payload.get(sys.argv[2], "")
if value is None:
    value = ""
print(value)
PY
}

metadata_fields() {
  python3 - "$1" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="ascii"))
fields = (
    "release_tag",
    "asset_name",
    "legacy_asset_name",
    "manifest_asset_name",
    "key",
    "source_hash_type",
    "source_hash",
    "source_file",
)
print("\t".join(str(payload.get(field, "")) for field in fields))
PY
}

cache_log_line() {
  local cache_log=$1
  shift
  printf '%s\n' "$*" | tee -a "$cache_log"
}

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

asset_exists() {
  local asset_name=$1
  if [ ! -f "$RELEASE_ASSETS_FILE" ]; then
    return 1
  fi
  grep -Fxq -- "$asset_name" "$RELEASE_ASSETS_FILE"
}

batch_download_assets() {
  local download_dir=$1
  shift
  if [ "$#" -eq 0 ]; then
    return 0
  fi

  local cmd=(gh release download "$release_tag" -R "$GITHUB_REPOSITORY" -D "$download_dir" --clobber)
  while [ "$#" -gt 0 ]; do
    cmd+=(-p "$1")
    shift
  done
  "${cmd[@]}" >/dev/null 2>&1
}

deps=()
targets=()
while read -r short target; do
  [ -z "$short" ] && continue
  case "$short" in
    \#*)
      continue
      ;;
  esac
  deps+=("$short")
  targets+=("$target")
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
zstd external_zstd
sse2neon external_sse2neon
embree external_embree
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
openimagedenoise external_openimagedenoise
haru external_haru
xr_openxr_sdk external_xr_openxr_sdk
abseil external_abseil
eigen external_eigen
ceres external_ceres
rubberband external_rubberband
pybind11 external_pybind11
nanobind external_nanobind
manifold external_manifold
cython external_cython
numpy external_numpy
libheif external_libheif
opencolorio external_opencolorio
openimageio external_openimageio
openvdb external_openvdb
potrace external_potrace
shaderc external_shaderc
spirv-reflect external_spirv_reflect
DEPS

metadata_paths=()
cache_logs=()
asset_names=()
legacy_asset_names=()
manifest_asset_names=()
cache_keys=()

release_tag=""

index=0
while [ "$index" -lt "${#deps[@]}" ]; do
  dep="${deps[$index]}"
  cache_dir="${ARTIFACT_ROOT}/${dep}-cache"
  download_dir="${cache_dir}/download"
  upload_dir="${cache_dir}/upload"
  metadata_path="${cache_dir}/metadata.json"
  cache_log="${cache_dir}/cache.log"

  mkdir -p "$cache_dir" "$download_dir" "$upload_dir"
  python3 tools/ios/dep_bootstrap.py metadata \
    --branch "$GITHUB_REF_NAME" \
    --dep "$dep" \
    --output "$metadata_path"

  IFS=$'\t' read -r dep_release_tag asset_name legacy_asset_name manifest_asset_name cache_key source_hash_type source_hash source_file <<EOF
$(metadata_fields "$metadata_path")
EOF

  if [ -z "$release_tag" ]; then
    release_tag="$dep_release_tag"
  elif [ "$release_tag" != "$dep_release_tag" ]; then
    printf 'Mismatched release tags: %s vs %s\n' "$release_tag" "$dep_release_tag" >&2
    exit 2
  fi

  {
    printf '[dep-cache][%s] release_tag=%s\n' "$dep" "$dep_release_tag"
    printf '[dep-cache][%s] asset_name=%s\n' "$dep" "$asset_name"
    printf '[dep-cache][%s] key=%s\n' "$dep" "$cache_key"
    printf '[dep-cache][%s] source=%s:%s (%s)\n' "$dep" "$source_hash_type" "$source_hash" "$source_file"
  } | tee "$cache_log"

  metadata_paths+=("$metadata_path")
  cache_logs+=("$cache_log")
  asset_names+=("$asset_name")
  legacy_asset_names+=("$legacy_asset_name")
  manifest_asset_names+=("$manifest_asset_name")
  cache_keys+=("$cache_key")

  index=$((index + 1))
done

release_available=0
if gh release view "$release_tag" -R "$GITHUB_REPOSITORY" --json assets --jq '.assets[].name' > "$RELEASE_ASSETS_FILE" 2>/dev/null; then
  release_available=1
fi

manifest_downloads=()
if [ "$release_available" -eq 1 ]; then
  index=0
  while [ "$index" -lt "${#deps[@]}" ]; do
    if asset_exists "${manifest_asset_names[$index]}"; then
      manifest_downloads+=("${manifest_asset_names[$index]}")
    fi
    index=$((index + 1))
  done

  if [ "${#manifest_downloads[@]}" -gt 0 ]; then
    echo "[dep-cache][batch] downloading ${#manifest_downloads[@]} manifest(s)"
    batch_download_assets "$RESTORE_DOWNLOAD_DIR" "${manifest_downloads[@]}"
  fi
fi

hit_assets=()
hit_logs=()
hit_deps=()
hit_match_types=()
hit_cached_keys=()
hit_current_keys=()
legacy_assets=()
legacy_logs=()
legacy_deps=()
miss_indices=()

index=0
while [ "$index" -lt "${#deps[@]}" ]; do
  dep="${deps[$index]}"
  metadata_path="${metadata_paths[$index]}"
  cache_log="${cache_logs[$index]}"
  manifest_asset_name="${manifest_asset_names[$index]}"
  manifest_path="${RESTORE_DOWNLOAD_DIR}/${manifest_asset_name}"
  asset_name="${asset_names[$index]}"
  legacy_asset_name="${legacy_asset_names[$index]}"
  cache_key="${cache_keys[$index]}"

  if [ "$release_available" -eq 1 ] && [ -f "$manifest_path" ]; then
    cached_key="$(json_field "$manifest_path" key)"
    match_type="$({ python3 tools/ios/dep_bootstrap.py matches --expected "$metadata_path" --cached "$manifest_path"; } 2>/dev/null || true)"

    if [ -n "$match_type" ]; then
      if asset_exists "$asset_name"; then
        hit_assets+=("$asset_name")
        hit_logs+=("$cache_log")
        hit_deps+=("$dep")
        hit_match_types+=("$match_type")
        hit_cached_keys+=("$cached_key")
        hit_current_keys+=("$cache_key")
      else
        cache_log_line "$cache_log" "[dep-cache][${dep}] manifest-hit asset-miss"
        miss_indices+=("$index")
      fi
    else
      cache_log_line "$cache_log" "[dep-cache][${dep}] manifest-stale cached_key=${cached_key:-missing} current_key=${cache_key}"
      miss_indices+=("$index")
    fi
  elif [ "$release_available" -eq 1 ] && asset_exists "$legacy_asset_name"; then
    legacy_assets+=("$legacy_asset_name")
    legacy_logs+=("$cache_log")
    legacy_deps+=("$dep")
  else
    cache_log_line "$cache_log" "[dep-cache][${dep}] restore-miss"
    miss_indices+=("$index")
  fi

  index=$((index + 1))
done

if [ "${#hit_assets[@]}" -gt 0 ]; then
  echo "[dep-cache][batch] downloading ${#hit_assets[@]} tarball(s)"
  batch_download_assets "$RESTORE_DOWNLOAD_DIR" "${hit_assets[@]}"
fi

extract_failed_file="${RESTORE_ROOT}/extract.failed"
rm -f "$extract_failed_file"
active_extract_jobs=0

index=0
while [ "$index" -lt "${#hit_assets[@]}" ]; do
  dep="${hit_deps[$index]}"
  cache_log="${hit_logs[$index]}"
  asset_name="${hit_assets[$index]}"
  match_type="${hit_match_types[$index]}"
  cached_key="${hit_cached_keys[$index]}"
  current_key="${hit_current_keys[$index]}"

  (
    if python3 tools/ios/dep_bootstrap.py extract --input "${RESTORE_DOWNLOAD_DIR}/${asset_name}"; then
      if [ "$match_type" = "compatible" ] && [ -n "$cached_key" ] && [ "$cached_key" != "$current_key" ]; then
        printf '[dep-cache][%s] restore-hit-compatible cached_key=%s current_key=%s\n' "$dep" "$cached_key" "$current_key" | tee -a "$cache_log"
      else
        printf '[dep-cache][%s] restore-hit\n' "$dep" | tee -a "$cache_log"
      fi
    else
      printf '[dep-cache][%s] extract-failed\n' "$dep" | tee -a "$cache_log"
      : > "$extract_failed_file"
      exit 1
    fi
  ) &

  active_extract_jobs=$((active_extract_jobs + 1))
  if [ "$active_extract_jobs" -ge "$MAX_EXTRACT_JOBS" ]; then
    wait
    active_extract_jobs=0
  fi

  index=$((index + 1))
done
wait

if [ -f "$extract_failed_file" ]; then
  exit 1
fi

if [ "${#legacy_assets[@]}" -gt 0 ]; then
  echo "[dep-cache][batch] downloading ${#legacy_assets[@]} legacy tarball(s)"
  batch_download_assets "$RESTORE_DOWNLOAD_DIR" "${legacy_assets[@]}"
fi

rm -f "$extract_failed_file"
active_extract_jobs=0

index=0
while [ "$index" -lt "${#legacy_assets[@]}" ]; do
  dep="${legacy_deps[$index]}"
  cache_log="${legacy_logs[$index]}"
  asset_name="${legacy_assets[$index]}"

  (
    if python3 tools/ios/dep_bootstrap.py extract --input "${RESTORE_DOWNLOAD_DIR}/${asset_name}"; then
      printf '[dep-cache][%s] restore-hit-legacy\n' "$dep" | tee -a "$cache_log"
    else
      printf '[dep-cache][%s] extract-failed\n' "$dep" | tee -a "$cache_log"
      : > "$extract_failed_file"
      exit 1
    fi
  ) &

  active_extract_jobs=$((active_extract_jobs + 1))
  if [ "$active_extract_jobs" -ge "$MAX_EXTRACT_JOBS" ]; then
    wait
    active_extract_jobs=0
  fi

  index=$((index + 1))
done
wait

if [ -f "$extract_failed_file" ]; then
  exit 1
fi

index=0
while [ "$index" -lt "${#miss_indices[@]}" ]; do
  miss_index="${miss_indices[$index]}"
  run_one "${deps[$miss_index]}" "${targets[$miss_index]}"
  index=$((index + 1))
done
