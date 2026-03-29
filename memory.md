# iOS Forward-Port Memory

Last updated: 2026-03-29

## Session Snapshot

- Working repo: `/home/shlok/Documents/Programming/Sandbox/blender-patchplan`
- Working branch: `blender-v5.1-release-IOSPATCH-round2`
- Read-only archaeology repo: `/home/shlok/Documents/Programming/Sandbox/blender-READONLY`
- Read-only branch to study: `ios`
- Release base branch: `blender-v5.1-release`
- Common divergence point: `5c2f06bfc`

## Hard Rules

- Do all code changes only in `/home/shlok/Documents/Programming/Sandbox/blender-patchplan`.
- Do not modify `/home/shlok/Documents/Programming/Sandbox/blender-READONLY`.
- Work only on branch `blender-v5.1-release-IOSPATCH-round2`.
- Do not create side branches unless absolutely unavoidable.
- Do not touch `ios`, `blender-v5.1-release`, or other branches.
- Treat fork branch `IOS5.1-round2` as nonexistent for this port; never merge from it, diff against it, or run workflows on it.
- Prefer additive, isolated changes over invasive edits.
- Prefer new files plus small shims over large rewrites of shared files.
- Keep future `v5.2+` forward-ports in mind.

## Current Goals

1. Finish phase 4 host-tool reuse so GitHub Actions can restore host `python`, `llvm`, and `ispc` without another multi-hour source build.
2. Keep the branch-scoped GitHub Release assets as the durable source of truth for reusable host tools.
3. Start phase 5 by wiring an iPhoneOS dependency-configure workflow that consumes the seeded host tools.
4. Only then start porting deeper Apple target selection and target-side dependency fixes for real `ios` builds.

## Workflow History

- Last successful workflow: `Build Blender iOS IPA` run `23702135538` on `blender-v5.1-release-IOSPATCH-round2` in `ios-deps-configure` mode; iPhoneOS dependency configure completed successfully with `APPLE_TARGET_DEVICE=ios`, `WITH_APPLE_CROSSPLATFORM=ON`, and detected `iPhoneOS18.5.sdk` on Xcode `16.4`.
- Last failed workflow: `Build Blender iOS IPA` run `23714629713` on `blender-v5.1-release-IOSPATCH-round2` in `ios-deps-basic` mode; the first cache-enabled `Restore or Build zlib` step failed immediately because `tools/ios/run_release_cached_dep.sh` used `readarray`, which was not available in that runner shell context.
- Latest cancelled workflow: `Build Blender iOS IPA` run `23714036934` on `blender-v5.1-release-IOSPATCH-round2` in `ios-deps-basic` mode reached the `Build jpeg` step on commit `db26746f401` before cancellation.
- Latest dispatched workflow: the next post-`deflate` fix rerun still needs to be sent from the current local branch state.
- Latest known workflow in repo before changes: `.github/workflows/close-prs.yml` only.
- Exploratory dispatches in this session: `23691855752` and `23691861803`, both manually cancelled after confirming `gh workflow run` worked.
- Mistake repaired: accidental merge/push from legacy branch was fully rewound; cancelled run `23692208885` is historical only and must be ignored.
- Older relevant failure for IPA path: `23631466279` on legacy branch `IOS5.1-round2` failed at final iOS link because macOS `OpenEXR` dylibs were linked into an iOS target.
- Historical env-probe failure still worth remembering: run `23692652257` failed because `artifacts/ios-env-probe/` was not created before piping through `tee`; that was fixed by creating the nested directory first.

## Next Hypothesis

- The next narrow win is to rerun `ios-deps-basic` after the cache-wrapper portability fix and the stronger dep-source hash naming, then continue through `deflate`, `fmt`, `robinmap`, and `pugixml`.
- Iteration speed should now come from per-dependency release bundles: before each dep step, attempt a release restore keyed by branch + dep + source tarball hash + recipe/helper/Xcode/SDK/config hash; on a miss, build and immediately publish that dep bundle.

## GitHub Actions Commands

Run a workflow:

```bash
nix-shell -p gh --run 'gh workflow run build-blender-ios.yml -R Shlok-Bhakta/blender-ios-build --ref blender-v5.1-release-IOSPATCH-round2'
```

Poll a workflow:

```bash
POLL_INTERVAL_SECONDS=60 nix-shell -p gh --run '.github/poll-build-run.sh build-blender-ios.yml blender-v5.1-release-IOSPATCH-round2 Shlok-Bhakta/blender-ios-build'
```

Inspect failed logs:

```bash
nix-shell -p gh --run 'gh run view <run-id> -R Shlok-Bhakta/blender-ios-build --log-failed'
```

List recent runs:

```bash
nix-shell -p gh --run 'gh run list -R Shlok-Bhakta/blender-ios-build --workflow build-blender-ios.yml --branch blender-v5.1-release-IOSPATCH-round2 -L 5'
```

## CI Observations

- `gh` is not installed directly in the shell; the documented `nix-shell -p gh --run ...` wrapper is required.
- Local `origin` now points at the writable SSH fork `git@github.com:Shlok-Bhakta/blender-ios-build.git`.
- Local `upstream` now points at read-only `https://github.com/blender/blender.git`.
- Writable Actions live in fork repo `Shlok-Bhakta/blender-ios-build`, where current GitHub permission is `ADMIN`.
- Current working branch already exists on the fork as `blender-v5.1-release-IOSPATCH-round2` and is the only fork branch to use for this effort.
- Legacy fork branch `IOS5.1-round2` is off-limits even if useful-looking data exists there; archaeology comes only from read-only `ios`.
- `.github/poll-build-run.sh` now supports an optional repo argument or `GH_REPO` environment variable so polling can target the writable fork.
- Existing fork workflow evidence confirms GitHub-hosted macOS ARM runners are available: `macos-15-arm64`, image `20260325.0234.1`, macOS `15.7.4`.
- Existing failed run `23631466279` shows `Xcode 16.4`, `iPhoneOS18.5.sdk`, and multiple installed Apple runtimes; the failure point is device linking against macOS `OpenEXR` dylibs.
- Fresh-port env probe success `23692682459` confirms branch-local dispatch works on `blender-v5.1-release-IOSPATCH-round2` using the compatibility driver workflow.
- Env probe artifact `ios-env-probe-23692682459` contains summary, selected env JSON, Xcode/SDK outputs, tool versions, and filesystem listings.
- Fresh-port host configure failure `23692720328` is narrow and actionable: CMake reached compiler detection successfully, then stopped in `check_software.cmake` before real dependency configuration because the runner did not have the expected Homebrew helper packages.
- The host configure artifact `ios-host-configure-23692720328` contains `manifest.json`, `host-configure-console.log`, `logs/configure.log`, and a build-tree snapshot; the key failure is in `logs/configure.log` rather than the console log.
- Fresh-port host configure success `23693130442` proves the workflow-environment fixes plus Blender mirror fallback are enough for a clean host configure on GitHub Actions.
- A new `host-tools` workflow exists and is intended to bootstrap the first real host tool outputs (`python`, `llvm`, `ispc`, `brotli`) while artifacting intermediate state.
- `host-tools` run `23693330218` confirms the expensive `python` and `llvm` stages already succeed on CI; the first real code blocker after that is ISPC vs current Xcode libc++ headers, not LLVM buildability.
- `host-tools` artifact `ios-host-tools-23693330218` confirms the expected host outputs already exist for `python/bin/python3.13`, `python/bin/meson`, `llvm/bin/llvm-config`, `clang`, `clang++`, `llvm-as`, `llvm-dis`, and `llvm-tblgen`.
- `host-tools` run `23693330218` failed in `ispc-logs/build.log` at `build/ios-deps/host/build/ispc/src/external_ispc/src/util.cpp:51` with an exception-specification mismatch against `/usr/include/c++/v1/__verbose_abort` from Xcode 16.4.
- `host-tools` run `23695801764` successfully published the first branch-scoped release bootstrap bundle under tag `blender-v5.1-release-IOSPATCH-round2-deps`, then failed again at `external_ispc`.
- `host-tools` run `23698420837` confirmed the bootstrap restore path works: the job reused the published `python`+`llvm` host bundle, skipped the LLVM rebuild, reached `external_ispc` quickly, and produced an artifact showing `ispc` still missing while `python` and `llvm` were present.
- `ios-deps-configure` run `23702135538` proved the new Apple target plumbing is live in CI: `APPLE_TARGET_DEVICE=ios`, `WITH_APPLE_CROSSPLATFORM=ON`, `CMAKE_DEPS_CROSSCOMPILE_BUILDDIR=build/ios-deps/host`, and the runner detected `iPhoneOS18.5.sdk`.
- `ios-deps-basic` run `23702360631` proved `external_zlib` and exposed a `png.cmake` version-drift bug: quoting `-DCMAKE_SYSTEM_PROCESSOR=\"aarch64\"` breaks nested CMake configure under CMake `4.3`.
- `ios-deps-basic` run `23702716309` proved `external_png` after the quote fix, then failed at `jpeg`; archaeology confirmed there was no old `ios`-branch `jpeg.cmake` delta to port.
- `ios-deps-basic` run `23713811661` proved the new log-tail observability path works; the `jpeg` failure is now visible directly in the job log rather than only in the uploaded artifact.
- Current `jpeg` root cause is narrower than the earlier policy drift: libjpeg-turbo now gets past the `< 3.5` policy failure and instead trips on an empty `CMAKE_SYSTEM_PROCESSOR` under iPhoneOS configure.
- The iOS helper layer now carries `-DCMAKE_SYSTEM_PROCESSOR:STRING=arm64` in `build_files/build_environment/cmake/platform/ios/options_apple_ios.cmake`, which should fix that class of failure generically for Apple cross-platform dependency recipes.
- `ios-deps-basic` run `23714250530` confirmed that fix: `Build jpeg` succeeded, moving the batch forward to `Build deflate`.
- `deflate` now fails at install rather than configure/build. libdeflate builds `libdeflate.a`, then tries to install `libdeflate-gzip.app` and hard-link `bin/libdeflate-gzip`, which is invalid for the iPhoneOS dependency target layout.
- Old-branch archaeology for `build_files/build_environment/cmake/deflate.cmake` is relevant: the read-only `ios` branch disabled `LIBDEFLATE_BUILD_GZIP` for `WITH_APPLE_CROSSPLATFORM`.
- `tools/ios/build_deps.py` now prints the tail of failing `configure.log` or `build.log` into the Actions step log, which materially improves CI iteration speed.
- `ios-deps-basic` run `23714629713` was the first cache-enabled workflow on commit `c204652f357`; it failed before any dep restore/build because `run_release_cached_dep.sh` used `readarray`, which is not safe to assume in the Actions shell context here.
- `tools/ios/dep_bootstrap.py` now computes per-dependency bundle metadata using explicit source-package identity from `versions.cmake` instead of hashing the whole file. Asset names now include the primary source hash, such as `ios-dep-png-sha256-<hash>-iphoneos-arm64-<configkey>.tar.gz`.
- For dependency bundles with transitive inputs, metadata now records all relevant source packages, for example `png` carries both `PNG` and `ZLIB` source identities so a changed zlib tarball invalidates the png bundle too.
- `tools/ios/run_release_cached_dep.sh` now reads metadata fields without `readarray`, logs the source package identity, and still wraps each dep step with `restore-hit -> skip`, `restore-miss -> build with heartbeat`, and `publish-on-success`.
- `.github/workflows/ios-deps-basic.yml` now routes each dep through that wrapper and grants `contents: write` so the workflow can publish reusable dep bundles to the existing branch-scoped release tag.
- A separate local clone at `/home/shlok/Documents/Programming/Sandbox/blender-full-readonly` now has `lib/macos_arm64` materialized; it provides reusable host `python` and `llvm` trees, but not `ispc`.
- The branch release `blender-v5.1-release-IOSPATCH-round2-deps` now also contains readable seed assets: `host-python-macos-arm64.tar.gz`, `host-llvm-macos-arm64.tar.gz`, `host-ispc-macos-arm64-v1.29.1.tar.gz`, `host-python-llvm-buildtree-macos-arm64.tar.gz`, and `host-tool-seeds.json`.
- User preference: long-running Actions must stay visibly alive. Future workflows should emit clear progress markers and heartbeat-style log lines before/after each expensive stage so a 60-90 minute compile does not look dead from the UI.
- User preference: do not keep polling in the CLI unless explicitly asked; use GitHub Actions logs/artifacts as the primary visible progress surface while the run is active.

## Local Workflow Additions

- Added workflow: `.github/workflows/ios-env-probe.yml`
- Workflow display name: `iOS Env Probe`
- Uploaded artifact name: `ios-env-probe-${github.run_id}`
- Helper script: `tools/ios/collect_ci_env.sh`
- Added workflow: `.github/workflows/ios-host-configure.yml`
- Workflow display name: `iOS Host Configure`
- Uploaded artifact name: `ios-host-configure-${github.run_id}`
- Added workflow: `.github/workflows/ios-host-tools.yml`
- Workflow display name: `iOS Host Tools`
- Uploaded artifact name: `ios-host-tools-${github.run_id}`
- Added compatibility driver: `.github/workflows/build-blender-ios.yml`
- Dependency entrypoint: `tools/ios/build_deps.py`
- `.github/workflows/ios-host-configure.yml` now installs the missing Homebrew configure prerequisites before invoking `tools/ios/build_deps.py`.
- `.github/workflows/ios-host-tools.yml` now has a release-backed bootstrap path for host `python`+`llvm`, and a local follow-up is prepared to restore a prebuilt `host-ispc-macos-arm64-v1.29.1.tar.gz` asset before configure.
- `build_files/build_environment/cmake/ispc.cmake` now has a local follow-up prepared to treat `${LIBDIR}/ispc/bin/ispc` as a valid preseeded tool and skip the expensive source build when that binary already exists.
- Local validation: `bash -n tools/ios/collect_ci_env.sh`, local env-probe dry run, `bash -n .github/poll-build-run.sh`, `python3 -m py_compile tools/ios/build_deps.py`, host and iOS dry runs for `tools/ios/build_deps.py`, and YAML parse via `nix-shell -p python3Packages.pyyaml`.

## Planned Bootstrap Storage

- Preferred durable storage is GitHub Releases assets on the writable fork, not git-committed binaries and not Actions cache as the canonical source.
- Active convention: one branch-scoped prerelease tag such as `blender-v5.1-release-IOSPATCH-round2-deps`.
- Active asset naming: readable tarballs such as `host-python-llvm-buildtree-macos-arm64.tar.gz`, `host-python-macos-arm64.tar.gz`, `host-llvm-macos-arm64.tar.gz`, `host-ispc-macos-arm64-v1.29.1.tar.gz`, plus per-dep bundles such as `ios-dep-png-sha256-<sourcehash>-iphoneos-arm64-<configkey>.tar.gz`.
- Current selection key for per-dep bundles includes: dependency source hash, relevant transitive source hashes, recipe/helper hashes, runner arch, Xcode version, SDK version, and a short config digest.
- Current workflow behavior: compute key, log tag/asset/source identity, try release download first, unpack into the expected iOS dep layout, rebuild only on a cache miss or stale bundle, then upload replacement assets back to the same branch release.
- Current practical split is: reuse release-seeded host `python`+`llvm`+`ispc`, and still build real iPhoneOS target libraries separately.

## Dependency Entrypoint Notes

- `tools/ios/build_deps.py` currently supports explicit `host` and `ios` modes for the active plan, with fail-fast behavior for unsupported target-selection work.
- It prints key input paths and tool availability, emits a manifest JSON, and writes configure/build logs to a caller-selected log directory.
- `host` mode dry-run works locally.
- `ios` mode beyond dry-run currently depends on first porting `APPLE_TARGET_DEVICE` support into `build_files/build_environment/CMakeLists.txt` on this branch.

## Old Branch Host-Tool Expectations

- Old `GNUmakefile` passed `-DCMAKE_DEPS_CROSSCOMPILE_BUILDDIR=$(CROSSCOMPILE_BUILD_DIR)` into dependency builds.
- Old dependency recipes expected host-built tools under `${CMAKE_DEPS_CROSSCOMPILE_BUILDDIR}/deps_arm64/Release/`.
- Observed target-side expectations in the old branch:
  - Python: `${CMAKE_DEPS_CROSSCOMPILE_BUILDDIR}/deps_arm64/Release/python/bin/python${PYTHON_SHORT_VERSION}`
  - Meson: `${CMAKE_DEPS_CROSSCOMPILE_BUILDDIR}/deps_arm64/Release/python/bin/meson`
  - LLVM tools: `${CMAKE_DEPS_CROSSCOMPILE_BUILDDIR}/deps_arm64/Release/llvm/bin/llvm-config`, `clang`, `clang++`, `llvm-dis`, `llvm-as`, `llvm-tblgen`
  - ISPC consumer path: `${CMAKE_DEPS_CROSSCOMPILE_BUILDDIR}/deps_arm64/Release/ispc/bin/ispc`
  - Brotli tool: `${CMAKE_DEPS_CROSSCOMPILE_BUILDDIR}/deps_arm64/Release/brotli/bin/brotli`
- Old Blender-side imported cross-tools were expected under `${CMAKE_SOURCE_DIR}/../build_ios/build_darwin_tools/${CMAKE_BUILD_TYPE}/bin/`.
- Imported app-build tool paths in the old branch were:
  - `makesdna`
  - `makesrna`
  - `msgfmt`
  - `datatoc`
  - `glsl_preprocess`

## Commit History Reference

- Full 41 non-merge commit list: see `plan.md` section 8.
- Tier-1 commits to study first: `dff9c1c75ac`, `ae62cddbf04`, `40308c619a9`, `cc08ff2b7c7`, `4c6874685d1`, `f3f86474a56`.

## Phase Tracker

### Phase 1 - Tracking And Guardrails

- [x] Confirm branch is `blender-v5.1-release-IOSPATCH-round2`.
- [x] Confirm no work is being done in `blender-READONLY`.
- [x] Create or update `memory.md` in the working repo root.
- [x] Record current goals, last successful workflow, last failed workflow, and next hypothesis.
- [x] Create a parity checklist section mapping old iOS features to new implementation status.
- [x] Record the 41 non-merge commit list or link back to it.
- [x] Record the do-not-use-other-branches rule.
- [x] Record the Actions commands.

Gate status:

- [x] progress ledger exists and is up to date.
- [x] parity tracker exists.

### Phase 2 - Build Observability Before Build Logic

- [x] Create a tiny temporary workflow that only prints environment/tool versions.
- [x] Verify `gh auth status`, Actions permissions, and macOS runner availability.
- [x] Capture Xcode version.
- [x] Capture SDK list/version.
- [x] Capture runner image details.
- [x] Capture relevant env vars.
- [x] Upload a small artifact containing environment metadata.
- [x] Prove local `gh workflow run` / poll / log-inspection loop works.
- [x] Document the workflow name and output artifact names.

Gate status:

- [x] workflow can be manually triggered on `blender-v5.1-release-IOSPATCH-round2`.
- [x] auth/permissions/runners are confirmed good enough for repeated CI iteration.
- [x] polling works.
- [x] failed log retrieval works.
- [x] artifacts are visible and useful.

### Phase 3 - Prototype The Dependency Build Entry Point

- [x] Decide on script location, likely under `tools/ios/`.
- [x] Make the script print every important input path and version.
- [x] Add explicit modes for `host` and `ios`.
- [x] Make the script fail fast with clear messages.
- [x] Keep the script small; let CMake orchestrate actual dependency order.
- [x] Add manifest generation for the resulting artifact bundle.
- [x] Make sure script logs are easy to artifact-upload.

Gate status:

- [x] script shape is stable enough to call from temporary workflows.

### Phase 4 - Host Tools First, Not Full iOS Build First

- [x] Create a temporary workflow that only configures the dependency project for host macOS ARM.
- [x] Upload `CMakeCache.txt`, configure logs, and full console log.
- [x] Once configure works, create a second temporary workflow/job that builds only the host prerequisites needed by iOS.
- [x] Start with likely minimal host prerequisites such as host Python and host LLVM tools if needed.
- [x] Confirm the old branch expectations around `CMAKE_DEPS_CROSSCOMPILE_BUILDDIR`.
- [x] Confirm where host tools land and how iOS recipes expect to find them.
- [x] Artifact-upload the host tool output layout.
- [x] Document exact expected host output paths.
- [x] Switch repeated host-tool reuse over to GitHub Releases bootstrap assets after the first clean source build.

Current note:

- Run `23693130442` proved that host configure now passes on the fresh-port branch after installing the missing Homebrew prerequisites and preferring the Blender mirror for dependency tarballs.
- Run `23693330218` proved the host bootstrap path much further: `external_python_site_packages` and `ll` complete successfully, then `external_ispc` fails quickly on a real source-level incompatibility with Xcode 16.4 libc++.
- Run `23698420837` proved the release restore path is already worth it: it reused the published `python`+`llvm` bundle and reached the ISPC blocker without recompiling LLVM.
- The current local follow-up is to seed `ispc` from a readable release asset and then move phase 5 bring-up onto real `iphoneos` dependency configure.

## Parity Checklist

### Build / Toolchain

- [ ] Apple target selection
- [ ] `ios` target handling
- [ ] host/target split
- [ ] host tools pathing
- [ ] bundle layout routing
- [ ] archive support

### Dependencies

- [x] dependency script exists
- [x] manifest generation exists
- [ ] host tools built in CI
- [ ] device deps bundle strategy defined
- [ ] LFS/submodule path deprecated or removed for iOS

### GHOST / Runtime

- [ ] `GHOST_SystemIOS`
- [ ] `GHOST_WindowIOS`
- [ ] `GHOST_ContextIOS`
- [ ] main entry refactor
- [ ] app delegate flow
- [ ] orientation handling
- [ ] home indicator behavior

### Input

- [ ] touch event types
- [ ] multi-finger taps
- [ ] edge swipe gestures
- [ ] Pencil tap
- [ ] touch offset fixes
- [ ] window switching fixes
- [ ] browser/asset-shelf multi-finger scroll
- [ ] editor interaction shims

### Rendering

- [ ] Metal guards and fixes
- [ ] Cycles Metal fixes
- [ ] HDR/EDR
- [ ] ProMotion

### File / Sandbox

- [ ] `Info.plist` document types
- [ ] security-scoped file access
- [ ] storage wrapper behavior
- [ ] appdir/resource path logic
- [ ] file browser integration

### Packaging

- [ ] storyboard
- [ ] entitlements
- [ ] archive support
- [ ] version string handling
- [ ] signing/export strategy documented
