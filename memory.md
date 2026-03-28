# iOS Forward-Port Memory

Last updated: 2026-03-28

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

1. Complete phase 1 tracking and guardrails.
2. Add an observable iOS environment probe workflow.
3. Prove the local `gh workflow run` / poll / logs loop.
4. Start a thin `tools/ios/` dependency orchestration scaffold only after phase 2 is usable.

## Workflow History

- Last successful workflow: none yet in this session.
- Last failed workflow: `Build Blender iOS IPA` run `23631466279` on fork branch `IOS5.1-round2`; failed at final iOS link because macOS `OpenEXR` dylibs were linked into an iOS target.
- Latest known workflow in repo before changes: `.github/workflows/close-prs.yml` only.
- Exploratory dispatches in this session: `23691855752` and `23691861803`, both manually cancelled after confirming `gh workflow run` worked.
- Mistake repaired: accidental merge/push from legacy branch was fully rewound; cancelled run `23692208885` is historical only and must be ignored.

## Next Hypothesis

- Keep all real work on `blender-v5.1-release-IOSPATCH-round2`, add a compatibility driver at `.github/workflows/build-blender-ios.yml`, and use that driver to dispatch the branch's temporary workflows without relying on any legacy branch.

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
- Local `origin` points at upstream `blender/blender`, where current GitHub permission is `READ` only.
- Writable Actions live in fork repo `Shlok-Bhakta/blender-ios-build`, where current GitHub permission is `ADMIN`.
- Current working branch already exists on the fork as `blender-v5.1-release-IOSPATCH-round2` and is the only fork branch to use for this effort.
- Legacy fork branch `IOS5.1-round2` is off-limits even if useful-looking data exists there; archaeology comes only from read-only `ios`.
- `.github/poll-build-run.sh` now supports an optional repo argument or `GH_REPO` environment variable so polling can target the writable fork.
- Existing fork workflow evidence confirms GitHub-hosted macOS ARM runners are available: `macos-15-arm64`, image `20260325.0234.1`, macOS `15.7.4`.
- Existing failed run `23631466279` shows `Xcode 16.4`, `iPhoneOS18.5.sdk`, and multiple installed Apple runtimes; the failure point is device linking against macOS `OpenEXR` dylibs.

## Local Workflow Additions

- Added workflow: `.github/workflows/ios-env-probe.yml`
- Workflow display name: `iOS Env Probe`
- Uploaded artifact name: `ios-env-probe-${github.run_id}`
- Helper script: `tools/ios/collect_ci_env.sh`
- Added workflow: `.github/workflows/ios-host-configure.yml`
- Workflow display name: `iOS Host Configure`
- Uploaded artifact name: `ios-host-configure-${github.run_id}`
- Added compatibility driver: `.github/workflows/build-blender-ios.yml`
- Dependency entrypoint: `tools/ios/build_deps.py`
- Local validation: `bash -n tools/ios/collect_ci_env.sh`, local env-probe dry run, `bash -n .github/poll-build-run.sh`, `python3 -m py_compile tools/ios/build_deps.py`, host and iOS dry runs for `tools/ios/build_deps.py`, and YAML parse via `nix-shell -p python3Packages.pyyaml`.

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
- [ ] Capture relevant env vars.
- [ ] Upload a small artifact containing environment metadata.
- [x] Prove local `gh workflow run` / poll / log-inspection loop works.
- [x] Document the workflow name and output artifact names.

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
- [ ] Once configure works, create a second temporary workflow/job that builds only the host prerequisites needed by iOS.
- [ ] Start with likely minimal host prerequisites such as host Python and host LLVM tools if needed.
- [x] Confirm the old branch expectations around `CMAKE_DEPS_CROSSCOMPILE_BUILDDIR`.
- [x] Confirm where host tools land and how iOS recipes expect to find them.
- [ ] Artifact-upload the host tool output layout.
- [x] Document exact expected host output paths.

## Parity Checklist

### Build / Toolchain

- [ ] Apple target selection
- [ ] `ios` target handling
- [ ] host/target split
- [ ] host tools pathing
- [ ] bundle layout routing
- [ ] archive support

### Dependencies

- [ ] dependency script exists
- [ ] manifest generation exists
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
