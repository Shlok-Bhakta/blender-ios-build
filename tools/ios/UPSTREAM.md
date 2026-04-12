# tools/ios — upstream provenance

Scripts are vendored from the Blender iOS fork for CI dependency caching:

- **Repository:** [Shlok-Bhakta/blender-ios-build](https://github.com/Shlok-Bhakta/blender-ios-build)
- **Branch:** `blender-v5.1-release-IOSPATCH-round2`
- **Files:** `build_deps.py`, `run_release_cached_dep.sh`, `dep_bootstrap.py` (base)

Local changes in this tree:

- `dep_bootstrap.py` — `iphonesimulator` vs `iphoneos`, configurable `APPLE_IOS_DEPS_BUILD_ROOT`, `IOS_DEPS_RELEASE_TAG`, skip missing key files, `PYSTRING` / `ffmpeg` prefix fixes.
- `run_cached_deps_all.sh` — batch driver for GitHub Actions.
