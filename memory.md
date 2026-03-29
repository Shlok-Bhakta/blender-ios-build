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

1. Keep the branch-scoped GitHub Release assets as the durable source of truth for reusable host tools and simple iPhoneOS dependency bundles.
2. Preserve the now-green `ios-deps-basic` path as the baseline proof for low-pain dependency reuse on Actions.
3. Start phase 7 by bringing up the next medium-pain iOS dependencies, beginning with the ones most likely to unblock a first Blender-side configure.
4. Only then start porting deeper Apple target selection and target-side Blender build logic for real `ios` app builds.

## Workflow History

- Last successful workflow: `Build Blender iOS IPA` run `23718530852` on `blender-v5.1-release-IOSPATCH-round2` in `ios-deps-basic` mode; `zlib`, `png`, `jpeg`, `deflate`, `fmt`, `robinmap`, and `pugixml` all completed successfully, artifact collection succeeded, and the workflow exited green end-to-end.
- Last failed workflow: `Build Blender iOS IPA` run `23718363006` on `blender-v5.1-release-IOSPATCH-round2` in `ios-deps-basic` mode; all simple deps including `pugixml` built successfully, but artifact collection failed afterward with a Python `UnicodeEncodeError` because tree listings were still written with ASCII.
- Latest cancelled workflow: `Build Blender iOS IPA` run `23714036934` on `blender-v5.1-release-IOSPATCH-round2` in `ios-deps-basic` mode reached the `Build jpeg` step on commit `db26746f401` before cancellation.
- Latest dispatched workflow: `23718530852`, sent after the UTF-8 artifact-output fix on commit `c84c2137f93`.
- Latest known workflow in repo before changes: `.github/workflows/close-prs.yml` only.
- Exploratory dispatches in this session: `23691855752` and `23691861803`, both manually cancelled after confirming `gh workflow run` worked.
- Mistake repaired: accidental merge/push from legacy branch was fully rewound; cancelled run `23692208885` is historical only and must be ignored.
- Older relevant failure for IPA path: `23631466279` on legacy branch `IOS5.1-round2` failed at final iOS link because macOS `OpenEXR` dylibs were linked into an iOS target.
- Historical env-probe failure still worth remembering: run `23692652257` failed because `artifacts/ios-env-probe/` was not created before piping through `tee`; that was fixed by creating the nested directory first.

## Next Hypothesis

- The low-pain iOS dependency batch is now stable and green, so the next narrow win is to start the medium-pain tier rather than spend more time on the already-proven simple deps.
- Iteration speed should continue to come from per-dependency release bundles: before each dep step, attempt a release restore keyed by branch + dep + source tarball hash + recipe/helper/Xcode/SDK/config hash; on a miss, build and immediately publish that dep bundle.

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
- `ios-deps-basic` run `23714880013` proved the release-backed dep cache flow end to end: `zlib`, `png`, `jpeg`, `deflate`, and `fmt` all built successfully and uploaded new per-dep release assets under `blender-v5.1-release-IOSPATCH-round2-deps`.
- `robinmap` is the next blocker. Its failure is again version drift, not missed archaeology: read-only `ios` history shows no `robinmap.cmake` delta at all, and CMake `4.3` explicitly suggests `-DCMAKE_POLICY_VERSION_MINIMUM=3.5`.
- Follow-up correction after that experiment: do not share the policy shim with `jpeg`. Restoring `jpeg_ios.cmake` to its standalone helper keeps the previously proven `jpeg` path isolated, and `robinmap_ios.cmake` now carries its own tiny policy-compat flag instead.
- `ios-deps-basic` run `23717838750` proved broad reuse for the simple dependency cache: `zlib`, `png`, `jpeg`, `deflate`, `fmt`, and `robinmap` all restored successfully, leaving `pugixml` as the only remaining blocker in that batch.
- `pugixml` was fixed by adding `build_files/build_environment/cmake/platform/ios/pugixml_ios.cmake` and wiring it from `build_files/build_environment/cmake/pugixml.cmake`; the helper injects `-DCMAKE_POLICY_VERSION_MINIMUM=3.5` only for `APPLE` + `WITH_APPLE_CROSSPLATFORM`, matching the already-proven narrow-fix pattern used for other CMake-4 drift cases.
- `ios-deps-basic` run `23718363006` proved that `pugixml` now builds and publishes correctly under the release-backed cache flow; the only remaining failure in that run was artifact collection writing tree listings with `encoding='ascii'`.
- The artifact-collection failure was fixed by switching workflow-generated tree listings and JSON summaries to UTF-8 in `.github/workflows/ios-deps-basic.yml`, `.github/workflows/ios-deps-configure.yml`, `.github/workflows/ios-host-configure.yml`, and `.github/workflows/ios-host-tools.yml`.
- `ios-deps-basic` run `23718530852` is now the key baseline run: fully green, all simple deps successful, artifact collection/upload successful, and no remaining blocker in the low-pain batch.
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
- Added helper: `build_files/build_environment/cmake/platform/ios/pugixml_ios.cmake`
- `build_files/build_environment/cmake/pugixml.cmake` now patches `PUGIXML_EXTRA_ARGS` through that helper so the CMake 4 compatibility flag stays isolated to the iOS cross-platform case.
- Workflow artifact tree dumps and host-tool summary JSON now write UTF-8 instead of ASCII, preventing Unicode path failures during artifact collection on Actions.
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
- The current practical state is good enough to move attention to medium-pain target deps; host bootstrap is no longer the critical path for low-pain iPhoneOS validation.

## iOS Dependency Checklist

Checkbox format: `[x]` = proven green on Actions, `[ ]` = not yet validated. Items within each dep are the specific fix/helper files needed when the base recipe fails on iOS.

### Host Bootstrap (macOS arm64 — seeds the iOS build)

These run on the macOS runner and produce host-side tools used by the iOS cross-compile.

- [x] **python** — `23795801764`; released as `host-python-macos-arm64.tar.gz`
- [x] **llvm** — `23795801764`; released as `host-llvm-macos-arm64.tar.gz`
- [x] **ispc** — `23798420837`; released as `host-ispc-macos-arm64-v1.29.1.tar.gz`; note: currently source-built with known libc++ incompatibility that is bypassed via the release asset restore path
- [x] **host bootstrap bundle** — `23795801764`; `host-python-llvm-buildtree-macos-arm64.tar.gz` bundles python+llvm together for fast restore

### iOS Target Dependencies

Built for `iphoneos-arm64`. Each dep that has needed an iOS-specific helper file is marked with the helper.

#### Low-Pain Batch (already green on Actions)

- [x] **zlib** — `23714880013`
- [x] **png** — `23714880013`
- [x] **jpeg** — `23714880013`; helper: `build_files/build_environment/cmake/platform/ios/options_apple_ios.cmake` (`-DCMAKE_SYSTEM_PROCESSOR:STRING=arm64`)
- [x] **deflate** — `23714880013`; helper: `build_files/build_environment/cmake/platform/ios/deflate_ios.cmake` (`-DLIBDEFLATE_BUILD_GZIP=OFF`)
- [x] **fmt** — `23714880013`
- [x] **robinmap** — `23717838750`; helper: `build_files/build_environment/cmake/platform/ios/robinmap_ios.cmake` (`-DCMAKE_POLICY_VERSION_MINIMUM=3.5`)
- [x] **pugixml** — `23718363006`; helper: `build_files/build_environment/cmake/platform/ios/pugixml_ios.cmake` (`-DCMAKE_POLICY_VERSION_MINIMUM=3.5`)

#### Medium-Pain Batch (proven via `ios-opensubdiv` probe)

- [x] **tbb** — `23719392429` (restore-hit in `ios-opensubdiv` workflow)
- [x] **opensubdiv** — `23719392429`; helper: `build_files/build_environment/cmake/platform/ios/opensubdiv_ios.cmake` (`-DNO_OPENGL=ON`)

#### Not Yet Validated

- [ ] **ssl** — `OPENSSL` — not yet attempted on iOS
- [ ] **openal** — `openal.cmake` — not yet attempted; old iOS branch keeps this
- [ ] **blosc** — `blosc.cmake` — not yet attempted
- [ ] **pthreads** — `pthreads.cmake` — not yet attempted
- [ ] **imath** — `imath.cmake` — not yet attempted; old iOS branch keeps this
- [ ] **openexr** — `openexr.cmake` — not yet attempted; old iOS branch keeps this
- [ ] **brotli** — `brotli.cmake` — old iOS branch adds iOS-specific patch and cross-compile brotli tool path
- [ ] **freetype** — `freetype.cmake` — old iOS branch wires brotli paths
- [ ] **alembic** — `alembic.cmake` — old iOS branch adds Imath path override
- [ ] **sdl** — `sdl.cmake` — old iOS branch may keep (verify if SDL is needed for iOS input)
- [ ] **nasm** — `nasm.cmake` — not yet attempted
- [ ] **tiff** — `tiff.cmake` — not yet attempted
- [ ] **flexbison** — `flexbison.cmake` — not yet attempted
- [ ] **python** — `python.cmake` — not yet attempted; very likely needs iOS-specific work
- [ ] **llvm** — `llvm.cmake` — not needed for iOS target deps (host-side only)
- [ ] **osl** — `osl.cmake` — old iOS branch disables `WITH_CYCLES_OSL` in final app build, but OSL dep may still be needed for OpenImageIO
- [ ] **cython** — `cython.cmake` — not yet attempted
- [ ] **numpy** — `numpy.cmake` — not yet attempted
- [ ] **zstandard** — `zstandard.cmake` — old iOS branch disables for iOS in `build_environment/CMakeLists.txt` — skip unless needed by python
- [ ] **python_site_packages** — not yet attempted
- [ ] **package_python** — not yet attempted
- [ ] **openimageio** — `openimageio.cmake` — old iOS branch keeps but disables many USE_* flags; likely medium-hard
- [ ] **usd** — `usd.cmake` — old iOS branch disables `WITH_USD` in final app build — skip for now
- [ ] **materialx** — `materialx.cmake` — not yet attempted; may be needed by Hydra which is disabled
- [ ] **openvdb** — `openvdb.cmake` — likely medium pain; old iOS branch keeps, disables python module
- [ ] **potrace** — `potrace.cmake` — not yet attempted
- [ ] **haru** — `haru.cmake` — not yet attempted
- [ ] **fribidi** — `fribidi.cmake` — not yet attempted
- [ ] **harfbuzz** — `harfbuzz.cmake` — not yet attempted
- [ ] **xr_openxr** — `xr_openxr.cmake` — old iOS branch disables for Apple — skip
- [ ] **hiprt** — `hiprt.cmake` — skip; CUDA/HIP related
- [ ] **dpcpp** — skip; Intel DPC++ compiler, not relevant for iOS
- [ ] **dpcpp_deps** — skip; DPC++ related
- [ ] **emhash** — skip; hash map lib, desktop-only
- [ ] **parallelhashmap** — skip; desktop-only
- [ ] **igc** — skip; Intel graphics compiler
- [ ] **gmmlib** — skip; Intel GPU lib
- [ ] **ocloc** — skip; Intel GPU tool
- [ ] **openpgl** — skip; Path Guidance lib, desktop-only
- [ ] **embree** — `embree.cmake` — old iOS branch keeps and adds iOS-specific TBB/Imath paths; likely medium pain
- [ ] **xml2** — `xml2.cmake` — not yet attempted
- [ ] **expat** — `expat.cmake` — not yet attempted
- [ ] **pystring** — `pystring.cmake` — not yet attempted
- [ ] **yamlcpp** — `yamlcpp.cmake` — not yet attempted
- [ ] **minizipng** — `minizipng.cmake` — not yet attempted
- [ ] **opencolorio** — `opencolorio.cmake` — old iOS branch keeps but disables python; likely medium pain
- [ ] **openjph** — skip; old iOS branch omits from dep list
- [ ] **thorvg** — skip; old iOS branch omits from dep list
- [ ] **libheif** — skip; old iOS branch omits from dep list
- [ ] **ffi** — `ffi.cmake` — old iOS branch adds iOS cross-compile flags
- [ ] **webp** — `webp.cmake` — not yet attempted
- [ ] **level-zero** — skip; not relevant for iOS
- [ ] **gmp** — `gmp.cmake` — not yet attempted
- [ ] **openjpeg** — `openjpeg.cmake` — not yet attempted
- [ ] **sqlite** — `sqlite.cmake` — not yet attempted
- [ ] **fftw** — `fftw.cmake` — not yet attempted; old iOS branch adds cross-compile flags
- [ ] **aom** — `aom.cmake` — old iOS branch keeps but adds iOS-specific flags
- [ ] **openimagedenoise** — `openimagedenoise.cmake` — skip; OIDN desktop-only
- [ ] **lame** — `lame.cmake` — not yet attempted
- [ ] **ogg** — `ogg.cmake` — not yet attempted
- [ ] **vorbis** — `vorbis.cmake` — not yet attempted
- [ ] **theora** — `theora.cmake` — not yet attempted
- [ ] **opus** — `opus.cmake` — not yet attempted
- [ ] **vpx** — `vpx.cmake` — not yet attempted; old iOS branch keeps
- [ ] **x264** — `x264.cmake` — not yet attempted
- [ ] **x265** — `x265.cmake` — old iOS branch keeps; likely hard
- [ ] **ffmpeg** — `ffmpeg.cmake` — old iOS branch keeps but uses iOS-specific flags and patches; likely hard
- [ ] **flac** — `flac.cmake` — old iOS branch adds cross-compile flags
- [ ] **sndfile** — `sndfile.cmake` — not yet attempted
- [ ] **spnav** — skip; desktop Linux only
- [ ] **bzip2** — `bzip2.cmake` — not yet attempted; old iOS branch adds iOS flags
- [ ] **lzma** — `lzma.cmake` — not yet attempted
- [ ] **libglu** — skip; OpenGL utility lib, desktop-only
- [ ] **mesa** — skip; desktop OpenGL
- [ ] **wayland_protocols** — skip; Linux desktop only
- [ ] **wayland** — skip; Linux desktop only
- [ ] **wayland_weston** — skip; Linux desktop only
- [ ] **shaderc_deps** — `shaderc_deps.cmake` — not yet attempted
- [ ] **shaderc** — `shaderc.cmake` — not yet attempted; Vulkan shader compiler
- [ ] **vulkan** — `vulkan.cmake` — old iOS branch disables `WITH_VULKAN_BACKEND` — skip
- [ ] **vulkan-memory-allocator** — `vulkan-memory-allocator.cmake` — skip; Vulkan only
- [ ] **spirv-reflect** — `spirv-reflect.cmake` — not yet attempted
- [ ] **pybind11** — `pybind11.cmake` — not yet attempted; may be needed by openvdb/python path
- [ ] **nanobind** — `nanobind.cmake` — not yet attempted
- [ ] **manifold** — `manifold.cmake` — not yet attempted
- [ ] **rubberband** — skip; old iOS branch omits
- [ ] **abseil** — skip; old iOS branch omits
- [ ] **eigen** — skip; old iOS branch omits
- [ ] **ceres** — skip; old iOS branch omits

### Old Branch iOS-Specific Dep Helpers Reference

When a dep fails on iOS, check if the old `ios` branch has a helper file here before inventing a fix from scratch:

- `build_files/build_environment/cmake/platform/ios/options_apple_ios.cmake`
- `build_files/build_environment/cmake/platform/ios/jpeg_ios.cmake`
- `build_files/build_environment/cmake/platform/ios/robinmap_ios.cmake`
- `build_files/build_environment/cmake/platform/ios/pugixml_ios.cmake`
- `build_files/build_environment/cmake/platform/ios/deflate_ios.cmake`
- `build_files/build_environment/cmake/platform/ios/opensubdiv_ios.cmake`
- `build_files/build_environment/patches/ios/` — iOS-specific source patches

### Dep Build Strategy Going Forward

1. Work through the not-yet-validated list in rough dependency order (foundational libs first, then consumers)
2. Use narrow probe workflows per dep or small cluster, similar to `ios-opensubdiv.yml`
3. When a dep fails, first check `build_files/build_environment/patches/ios/` for an existing patch, then look at `build_files/build_environment/cmake/platform/ios/` for a helper, then diagnose the actual configure failure
4. After validating, update the checkbox and record the run ID and helper files used

## Post-Deps Blender-Side Porting Work

After deps are done, the real Blender-side iOS platform port begins. This is the GHOST / creator / Apple build-glue work that makes an actual iOS app compile and run. Each bucket has concrete files and commits from the old `ios` branch as reference.

### Build-System / Toolchain

Must be done before a full Xcode build can succeed:

- [ ] **Apple target selection**: add `APPLE_TARGET_DEVICE` handling to main Blender CMake, routing `ios` and `ios-simulator` into the cross-compile path
- [ ] **`ios` target handling**: ensure Blender's main `CMakeLists.txt` can generate an Xcode project for iOS; this is the configure equivalent of what deps configure does for the dep graph
- [ ] **host/target split**: Blender needs to find cross-compiled tools (`makesdna`, `makesrna`, `msgfmt`, `datatoc`, `glsl_preprocess`) under `${CMAKE_SOURCE_DIR}/../build_ios/build_darwin_tools/${CMAKE_BUILD_TYPE}/bin/` — the old `GNUmakefile` wired this
- [ ] **host tools pathing**: `${CMAKE_DEPS_CROSSCOMPILE_BUILDDIR}/deps_arm64/Release/` must supply `python/bin/python`, `llvm/bin/llvm-config`, `ispc/bin/ispc`, and `brotli/bin/brotli`; these must be reachable during the iOS configure and build
- [ ] **bundle layout routing**: iOS app bundle layout differs from macOS; `source/creator/CMakeLists.txt` and `release/ios/` control this
- [ ] **archive support**: `f3f86474a56` on the old branch added Xcode archiving support; this is for distribution builds

Key files (old branch):
- `CMakeLists.txt`
- `GNUmakefile`
- `build_files/cmake/platform/platform_apple.cmake`
- `build_files/cmake/platform/platform_apple_xcode.cmake`
- `build_files/cmake/platform/ios/`
- `source/creator/CMakeLists.txt`

Key old commits: `dff9c1c75ac`, `f3f86474a56`

### GHOST / Runtime

The iOS windowing and app lifecycle layer. Must exist before the app can start:

- [ ] **`GHOST_SystemIOS`**: new backend in `intern/ghost/intern/GHOST_SystemIOS.mm`; manages iOS app lifecycle, event loop, and system-level coordination
- [ ] **`GHOST_WindowIOS`**: window management in `intern/ghost/intern/GHOST_WindowIOS.mm`; handles window creation, sizing, and display association
- [ ] **`GHOST_ContextIOS`**: Metal/OpenGL context setup in `intern/ghost/intern/GHOST_ContextIOS.mm`; creates and manages the rendering context
- [ ] **main entry refactor**: `source/creator/creator.cc` needs iOS entry point routing; the old branch refactored from `WindowIOS`-centric to `SystemIOS`-centric entry (commit `cc08ff2b7c7`)
- [ ] **app delegate flow**: iOS `UIApplicationDelegate` integration; needs proper app delegate initialization early in startup
- [ ] **orientation handling**: portrait/landscape orientation routing in GHOST
- [ ] **home indicator behavior**: auto-hide home indicator on iOS, handled via `preferredScreenEdgesDeferringSystemGestures` or equivalent

Key files (old branch):
- `intern/ghost/intern/GHOST_SystemIOS.mm`
- `intern/ghost/intern/GHOST_WindowIOS.mm`
- `intern/ghost/intern/GHOST_ContextIOS.mm`
- `source/creator/creator.cc`
- `source/creator/CMakeLists.txt`

Key old commits: `cc08ff2b7c7`, `ae62cddbf04`, `4c6874685d1`

### Input / Touch

Touch event plumbing from iOS into Blender's event system:

- [ ] **touch event types**: `source/blender/windowmanager/wm_event_types.hh` must include iOS touch event definitions
- [ ] **multi-finger taps**: 2/3/4 finger tap detection; `c129d785346` on old branch
- [ ] **edge swipe gestures**: inward edge swipe from screen edges; `bbd3bb5ce16` on old branch
- [ ] **Pencil tap**: Apple Pencil input; `bcce1e82520` on old branch
- [ ] **touch offset fixes**: coordinate translation fixes when iOS is not in fullscreen or has inset areas; `a8fc93e3b09`
- [ ] **window switching fixes**: portrait mode window switching; `4f61bdd181b`
- [ ] **browser/asset-shelf multi-finger scroll**: requires multi-finger pan for file browser and asset shelf; `4f40068f951`, `918ed1da796`
- [ ] **editor interaction shims**: touch routing into `interface_handlers.cc`, `view2d_ops.cc`, `view3d_navigate_view_move.cc`, `view3d_navigate_view_rotate.cc`

Key files (old branch):
- `source/blender/windowmanager/wm_event_types.hh`
- `source/blender/windowmanager/intern/wm_event_system.cc`
- `source/blender/makesrna/intern/rna_wm.cc`
- `source/blender/makesrna/intern/rna_screen.cc`
- `source/blender/editors/interface/interface_handlers.cc`
- `source/blender/editors/interface/view2d/view2d_ops.cc`
- `source/blender/editors/space_view3d/view3d_navigate_view_move.cc`
- `source/blender/editors/space_view3d/view3d_navigate_view_rotate.cc`
- `scripts/presets/keyconfig/keymap_data/blender_default.py`
- `scripts/startup/bl_operators/touch.py`

Key old commits: `c129d785346`, `bbd3bb5ce16`, `bcce1e82520`, `4f40068f951`, `918ed1da796`, `a8fc93e3b09`, `4f61bdd181b`

### File / Sandbox

iOS document and file access plumbing:

- [ ] **`Info.plist` document types**: `release/ios/Blender.app/Info.plist` must declare support for `.blend` file type so iOS can open documents
- [ ] **security-scoped file access**: iOS sandbox requires security-scoped bookmarks for accessing files outside the app container; `4c6874685d1` on old branch
- [ ] **storage wrapper behavior**: `source/blender/blenlib/intern/storage_apple.mm` handles iOS-specific storage paths
- [ ] **appdir/resource path logic**: `source/blender/blenkernel/intern/appdir.cc` must return correct iOS bundle/resource paths
- [ ] **file browser integration**: `source/blender/editors/space_file/fsmenu_system.mm` may need iOS-specific additions for document browser

Key files (old branch):
- `release/ios/Blender.app/Info.plist`
- `source/blender/windowmanager/intern/wm_files.cc`
- `source/blender/blenkernel/intern/appdir.cc`
- `source/blender/blenlib/intern/storage_apple.mm`
- `source/blender/editors/space_file/fsmenu_system.mm`

Key old commits: `4c6874685d1`, `860884466d3`

### Rendering / GPU

Metal backend and Cycles Metal work for iOS GPU rendering:

- [ ] **Metal guards and fixes**: `source/blender/gpu/metal/` needs iOS-compatible guards and Metal shader compilation for iOS targets; `f867de5303e`, `e351133c24a` on old branch
- [ ] **Cycles Metal fixes**: `intern/cycles/device/metal/` needs fixes for iOS target compatibility
- [ ] **HDR/EDR**: `9f8e5860bcb` on old branch enabled HDR/EDR rendering support
- [ ] **ProMotion**: `ae62cddbf04` on old branch added ProMotion (120fps) support

Key files (old branch):
- `source/blender/gpu/metal/`
- `intern/cycles/device/metal/`

Key old commits: `ae62cddbf04`, `9f8e5860bcb`, `f867de5303e`, `e351133c24a`

### Packaging / Distribution

iOS app bundle assembly:

- [ ] **storyboard**: `release/ios/Blender.app/Main.storyboard` defines launch screen and initial UI
- [ ] **entitlements**: `release/ios/entitlements.plist` for app sandbox, keychain access, etc.
- [ ] **archive support**: Xcode archive generation for TestFlight/App Store distribution; `f3f86474a56` on old branch
- [ ] **version string handling**: `d9b6fe34ddc` on old branch corrected `CFBundleVersion` in `Info.plist`
- [ ] **signing/export strategy documented**: must decide whether to target unsigned CI validation or signed distribution; certificate/profile strategy must be explicit

Key files (old branch):
- `release/ios/Blender.app/Main.storyboard`
- `release/ios/entitlements.plist`
- `source/creator/CMakeLists.txt`
- `release/ios/Blender.app/Info.plist`

Key old commits: `f3f86474a56`, `d9b6fe34ddc`

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
- [x] host tools built in CI
- [x] device deps bundle strategy defined
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
