# Blender iOS v5.1 Forward-Port Plan

This document is the hand-off spec for the next agent working in:

- working repo: `/home/shlok/Documents/Programming/Sandbox/blender-patchplan`
- working branch: `blender-v5.1-release-IOSPATCH-round2`
- archaeology/source-of-truth repo: `/home/shlok/Documents/Programming/Sandbox/blender-READONLY`
- archaeology branch to study: `ios`
- release base branch to port onto: `blender-v5.1-release`
- common divergence point: `5c2f06bfc`

This spec is intentionally detailed and redundant. Assume context may compact. When that happens, this file is the source of truth.

## 0. Hard Rules

- Do not modify `/home/shlok/Documents/Programming/Sandbox/blender-READONLY`.
- Do all code changes only in `/home/shlok/Documents/Programming/Sandbox/blender-patchplan`.
- Work only on branch `blender-v5.1-release-IOSPATCH-round2`.
- Do not create side branches unless absolutely unavoidable.
- If a branch rewrite becomes absolutely necessary, only force-push `blender-v5.1-release-IOSPATCH-round2`.
- Do not touch `ios`, `blender-v5.1-release`, or any other branch.
- Treat fork branch `IOS5.1-round2` as nonexistent for this effort; do not read from it, diff against it, merge from it, or run workflows on it.
- Prefer additive, isolated changes over invasive edits.
- Prefer new files plus small shims over large rewrites of shared files.
- Keep future `v5.2`, `v5.3`, and later forward-ports in mind at all times.
- Treat the old `ios` branch as the feature-parity source of truth, not as the implementation style to copy blindly.

## 1. What This Project Is Trying To Do

The goal is not to reproduce the old `ios` branch exactly. The goal is to port every iOS feature and build capability from `ios` onto `blender-v5.1-release`, while doing it in a way that is:

- less invasive
- less coupled to giant shared files
- more CI-driven
- less dependent on Blender LFS/submodule binary pulls
- more maintainable across `v5.2`, `v5.3`, and later

In short:

- preserve all iOS functionality
- reduce long-term maintenance cost
- move iOS dependency production toward CI-generated artifacts
- keep shared upstream files as untouched as possible

## 2. Key Conclusions From Investigation

### 2.1 Size Of The Existing iOS Branch

From `5c2f06bfc..ios`:

- total commits: `49`
- non-merge commits: `41`
- files changed: `208`
- insertions: `10245`
- deletions: `624`

This is a real platform branch, not a small patch set.

### 2.2 Conflict Surface Against `blender-v5.1-release`

- `ios`-changed files since split: `208`
- `blender-v5.1-release`-changed files since split: `9650`
- overlapping changed files: `118`
- synthetic merge analysis: roughly `113` files are changed on both sides in directly conflicting ways

Implication:

- this is not a good candidate for blind cherry-picking
- this must be treated as a subsystem-by-subsystem forward-port

### 2.3 Major Hotspots In The Old iOS Branch

Largest changed areas on `ios` by count of changed files:

- `build_files/build_environment/cmake/` - 23.0%
- `build_files/build_environment/patches/` - 6.2%
- `intern/ghost/intern/` - 6.7%
- `source/blender/gpu/metal/` - 9.1%
- `release/ios/Blender.app/Assets/` - 9.1%
- `intern/cycles/device/metal/` - 2.8%
- `source/blender/windowmanager/` - 3.4%
- `source/blender/editors/space_file/` - 1.4%
- `source/creator/` - 0.9%

By changed-line volume, `intern/ghost/intern/` is the dominant hotspot, so runtime/windowing work is likely harder than file-count percentages alone suggest.

Path-level commit concentration including merge commits:

- `build_files`: `14` commits touch it
- `intern/ghost`: `32` commits touch it
- `source/creator`: `10` commits touch it
- `source/blender/gpu/metal`: `12` commits touch it
- `intern/cycles/device/metal`: `10` commits touch it
- `source/blender/windowmanager`: `13` commits touch it
- `source/blender/editors/space_file`: `10` commits touch it
- `source/blender/blenkernel/intern/appdir.cc`: `3` commits touch it
- `release/ios`: `4` commits touch it

### 2.4 Dependency Reality

Important: the old iOS branch does not primarily add lots of brand-new iOS-only third-party dependencies. It mostly adapts existing Blender deps to cross-compile for iOS.

That is good news.

But it still has substantial iOS-specific dependency glue and source patching.

The iOS branch patches or special-cases external builds for things including:

- Python
- LLVM
- ISPC
- OpenImageIO
- OSL
- OpenColorIO
- USD
- FFmpeg
- Embree
- XML2
- Brotli
- x265
- probably several related support libs through flags and patch selection

This means:

- Python is not the only difficult dependency
- the branch is more patch-heavy than dependency-heavy
- the port is easier than inventing a whole new dependency stack
- but not easy enough to be considered trivial

### 2.5 CI And LFS Conclusion

Recommended direction:

- move away from `lib/ios_arm64` as the long-term source of truth
- replace that with CI-produced dependency bundles/artifacts
- use GitHub Actions on macOS runners as the build authority
- use caches only as acceleration, not as the canonical storage model

Do not try to replace the Apple-native iOS toolchain flow with Nix.

Use Nix only as a local wrapper for `gh` commands if needed, not as the actual build solution.

## 3. Repos, Branches, And How To Look At History

### 3.1 Working Repo

Make changes here:

- `/home/shlok/Documents/Programming/Sandbox/blender-patchplan`

Use branch:

- `blender-v5.1-release-IOSPATCH-round2`

### 3.2 Read-Only Archaeology Repo

Inspect history here:

- `/home/shlok/Documents/Programming/Sandbox/blender-READONLY`

Do not modify it.

### 3.3 Canonical History Command

Use this exact pattern when reviewing iOS branch history:

```bash
cd /home/shlok/Documents/Programming/Sandbox/blender-READONLY; git log 5c2f06bfc..ios --oneline --graph --no-merges; cd -
```

### 3.4 Other Useful Read-Only Commands

Compare all changed files:

```bash
cd /home/shlok/Documents/Programming/Sandbox/blender-READONLY; git diff --name-status 5c2f06bfc..ios; cd -
```

Look at a specific commit:

```bash
cd /home/shlok/Documents/Programming/Sandbox/blender-READONLY; git show dff9c1c75ac; cd -
```

Compare old iOS branch to release branch in a hotspot:

```bash
cd /home/shlok/Documents/Programming/Sandbox/blender-READONLY; git diff blender-v5.1-release..ios -- build_files/ intern/ghost/ source/creator/ source/blender/windowmanager/ source/blender/gpu/metal/; cd -
```

## 4. GitHub Actions Interaction Model

These are the expected local commands for interacting with Actions from the working repo context.

Important repo note discovered during execution:

- local `origin` points at writable fork `git@github.com:Shlok-Bhakta/blender-ios-build.git`
- local `upstream` points at read-only `https://github.com/blender/blender.git`
- writable Actions control currently lives in `Shlok-Bhakta/blender-ios-build`
- the only writable branch to use for this port is `blender-v5.1-release-IOSPATCH-round2`
- treat fork branch `IOS5.1-round2` as a broken legacy branch and ignore it completely
- use `-R Shlok-Bhakta/blender-ios-build` for `gh` commands, or pass that repo as the optional third argument to `.github/poll-build-run.sh`

### 4.1 Run A Workflow

```bash
nix-shell -p gh --run 'gh workflow run build-blender-ios.yml -R Shlok-Bhakta/blender-ios-build --ref blender-v5.1-release-IOSPATCH-round2'
```

### 4.2 Poll Every 60 Seconds

```bash
POLL_INTERVAL_SECONDS=60 nix-shell -p gh --run '.github/poll-build-run.sh build-blender-ios.yml blender-v5.1-release-IOSPATCH-round2 Shlok-Bhakta/blender-ios-build'
```

### 4.3 Inspect Failure Logs

```bash
nix-shell -p gh --run 'gh run view 23421249851 -R Shlok-Bhakta/blender-ios-build --log-failed'
```

Replace the run id with the actual one.

### 4.4 If You Need The Latest Run ID First

```bash
nix-shell -p gh --run 'gh run list -R Shlok-Bhakta/blender-ios-build --workflow build-blender-ios.yml --branch blender-v5.1-release-IOSPATCH-round2 -L 5'
```

### 4.5 Workflow Discipline

- Prefer temporary single-purpose workflows first.
- Do not jump straight into a giant all-in-one workflow.
- Prove one thing at a time.
- Once a temporary workflow proves a concept, either fold it into the durable workflow or preserve it with a narrow purpose and clear name.
- Because GitHub only dispatches workflows that exist on the fork default branch path, keep a compatibility driver at `.github/workflows/build-blender-ios.yml` on `blender-v5.1-release-IOSPATCH-round2` that can call the temporary workflows without using any legacy branch.

## 5. Strategic Principles For The Port

### 5.1 Port Features, Not Old Coupling

The old `ios` branch achieved its goal by deeply coupling itself into existing code. That was understandable, but it is not the model to repeat.

New porting rule:

- keep all features
- keep as little coupling as possible

### 5.2 Prefer New Files And Thin Shims

When touching shared build files or platform files:

- add new iOS-specific helper modules where possible
- add tiny conditional includes/hooks in shared files
- do not duplicate giant recipes unless absolutely necessary

Preferred style:

- `build_files/build_environment/cmake/<shared>.cmake`
- `build_files/build_environment/cmake/platform/ios/<thing>_ios.cmake`
- `build_files/build_environment/patches/ios/<thing>.diff`
- `build_files/cmake/platform/ios/<helper>.cmake`

Avoid this unless divergence is truly huge:

- full fork of `ispc.cmake` into a standalone `ispc-ios.cmake`
- full fork of `python.cmake` into a separate giant recipe
- huge copy-paste platform files

### 5.3 Keep Shared Edits Tiny And Intentional

When a shared file must change, the ideal shape is:

- one small include
- one small variable override
- one small platform branch

Not:

- dozens of iOS-specific lines injected inline across the entire file

### 5.4 Design For Future Release Ports

Every decision should be judged by:

- will this make `v5.2` easier?
- will this make `v5.3` easier?
- can this survive upstream churn in `build_files`, `GHOST`, `Metal`, and `windowmanager`?

If the answer is no, redesign it before proceeding.

## 6. What The Old iOS Branch Actually Contains

The `ios` branch is a full platform port across these buckets:

### 6.1 Build-System And Toolchain Enablement

- Apple target selection for `macos` and `ios`
- cross-compile host/target split
- iOS dependency selection and iOS-specific patches
- support for `lib/ios_arm64`
- partial alternate Apple target path handling
- bundle layout differences for iOS app packaging

Key files:

- `CMakeLists.txt`
- `GNUmakefile`
- `build_files/cmake/platform/platform_apple.cmake`
- `build_files/cmake/platform/platform_apple_xcode.cmake`
- `build_files/build_environment/CMakeLists.txt`
- `build_files/build_environment/cmake/ios_defines.cmake`
- `build_files/utils/make_update.py`

### 6.2 Runtime / Windowing / App Lifecycle

- new iOS GHOST backend
- iOS app entrypoint handling
- app delegate logic
- window lifecycle and event translation
- orientation and display behavior

Key files:

- `intern/ghost/intern/GHOST_SystemIOS.mm`
- `intern/ghost/intern/GHOST_WindowIOS.mm`
- `intern/ghost/intern/GHOST_ContextIOS.mm`
- `source/creator/creator.cc`
- `source/creator/CMakeLists.txt`

### 6.3 Input And UI Behavior

- touch event types
- multi-finger taps
- inward edge swipes
- Pencil tap
- file browser/asset shelf multi-finger scroll behavior
- window switching and portrait handling

Key files:

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

### 6.4 File Access / Sandbox / Document Flow

- security-scoped file access
- document browser support
- `.blend` document registration in Info.plist
- appdir changes for iOS bundle/resource layout
- file menu integration

Key files:

- `release/ios/Blender.app/Info.plist`
- `source/blender/windowmanager/intern/wm_files.cc`
- `source/blender/blenkernel/intern/appdir.cc`
- `source/blender/blenlib/intern/storage_apple.mm`
- `source/blender/editors/space_file/fsmenu_system.mm`

### 6.5 GPU / Rendering / Cycles / Metal

- Metal backend fixes and platform checks
- Cycles Metal fixes
- platform guards for reduced Apple targets
- HDR/EDR enablement
- ProMotion handling

Key files:

- `source/blender/gpu/metal/`
- `intern/cycles/device/metal/`

### 6.6 Packaging And Distribution

- iOS app bundle content
- storyboard
- entitlements
- archive support for distribution
- bundle versioning corrections

Key files:

- `release/ios/Blender.app/Main.storyboard`
- `release/ios/entitlements.plist`
- `source/creator/CMakeLists.txt`

## 7. Most Important Commits To Study First

These are the first commits to deeply inspect before implementing anything major.

### 7.1 Tier 1 Study Commits

- `dff9c1c75ac` - initial build support for iOS/iPad; foundational branch shape
- `ae62cddbf04` - screen update fixes and ProMotion; important runtime correctness
- `cc08ff2b7c7` - refactors iOS entrypoint/app delegate from `WindowIOS` to `SystemIOS`; architectural cleanup
- `4c6874685d1` - external file support; critical for sandbox/document behavior
- `f3f86474a56` - Xcode archiving support; important for distribution path

### 7.2 Tier 2 Study Commits

- `c129d785346` - touch events for 2/3/4 finger tap
- `1cf99110c3a` and `8ee907a53bf` - portrait mode work
- `bcce1e82520` - Pencil tap
- `bbd3bb5ce16` - inward edge swipe gestures
- `9f8e5860bcb` - HDR/EDR
- `4f40068f951` and `918ed1da796` - multi-finger scroll in file browser / asset shelf

## 8. Full Non-Merge Commit List (Chronological)

Study these in order if reconstructing the branch story:

1. `dff9c1c75ac` - Initial build support for the iOS/iPad platform
2. `5d7ded2cd26` - Cleanup: make format
3. `c129d785346` - IOS: Touch Events: Support 2, 3, 4 finger tap
4. `1cf99110c3a` - Support Portrait mode
5. `8ee907a53bf` - iOS: Portrait mode cleanup
6. `e351133c24a` - Post-merge fix: `GHOST_ContextMTL` macro clashes with renamed class
7. `f867de5303e` - Check for iOS availability in `MTLAccelerationStructureUsagePreferFastIntersection`
8. `b3aeff2cc5a` - Cleanup: Remove prints/TODO
9. `45be993c09c` - IOS: Enable OpenSubdiv build
10. `ae62cddbf04` - Fix missing screen updates and add ProMotion support
11. `9c63598baa4` - IOS: Add/fix missing copyright headers
12. `91a7ab757c1` - Force USD to be off for iPad
14. `0e9cfc0a554` - iOS: Fix cross compile project tweaks for cmake and sbin paths
15. `bcce1e82520` - iOS: Initial support for Pencil tap
16. `a8fc93e3b09` - iOS: fix touch offset in more space display mode
17. `d4af12d11ac` - iOS: Adding missing switch case
19. `240edda8e55` - iOS: Fix `IOS_INPUT_LOG` macro compile issue
20. `8065bd37548` - iOS: Fix View3D wrongly switching out of axis ortho view on dragging
21. `6df62b1a5e5` - make format
22. `3998c94d0cf` - Fix: iOS-only compile error in recent Cycles code after merge
23. `4f61bdd181b` - iOS: Fix window switching
24. `4f40068f951` - iOS: Require multi-finger scroll in File/Asset Browser
25. `918ed1da796` - iOS: Require multi-finger scroll in the Asset Shelf
26. `9f8e5860bcb` - iOS: Enable HDR/EDR rendering support
27. `262c01cf4c7` - iOS: Prefer Auto-Hiding the Home Indicator
28. `a6788f4e758` - Cleanup: make format
29. `bbd3bb5ce16` - iOS: Inward Edge Swipe Gestures
30. `cc08ff2b7c7` - iOS: Refactor iOS entrypoint and app delegate from WindowIOS to SystemIOS
31. `6f30d1491f6` - iOS: Misc include and assert cleanups
32. `2e6992ce443` - iOS: SystemIOS clean-up and fix missing window property
33. `7139c4275f9` - Cleanup: Unify GHOST iOS headers with current style
34. `4c6874685d1` - iOS: Improve external file support
35. `860884466d3` - Fix: Extraneous change in last external file support commit
36. `a6cfcb7fc86` - Apply make format
37. `2b3dfad92b1` - Cleanup: Unused variables
38. `487eb40ea23` - iOS: Double DPI Hint from 144 to 288
39. `f3f86474a56` - iOS: Add Xcode archiving support for distribution
40. `9f8754653b9` - Format: Fix broken formatting in Cycles `kernel.mm`
41. `d9b6fe34ddc` - iOS: Correct `Info.plist` `CFBundleVersion`

## 9. Important Existing Hacks / TODOs In The Old Branch

These are red flags to either improve or consciously preserve as temporary compromises.

- `CMakeLists.txt:123` - TODO/hack around Apple target defaulting
- `GNUmakefile:239` - hardcoded `macos` assumption in cross-compile host path
- `build_files/cmake/platform/platform_apple.cmake:29` - forces `WITH_USD OFF`
- `build_files/cmake/platform/platform_apple.cmake:43` - forces `WITH_HYDRA OFF`
- `build_files/cmake/platform/platform_apple.cmake:44` - forces `WITH_CYCLES_OSL OFF`
- `build_files/cmake/platform/platform_apple.cmake:210` - ugly Python fallback logic
- `build_files/cmake/platform/platform_apple.cmake:725` - bundle id comment says change before release
- `build_files/build_environment/cmake/ispc.cmake` - comments about missing `curses` and `tinfo`
- `build_files/build_environment/cmake/usd.cmake` - Metal support explicitly disabled for iOS
- `intern/ghost/intern/GHOST_WindowIOS.mm` - many `IOS_FIXME` and coordinate/text-edit TODOs
- `release/ios/README.md` - barely useful

Rule: when reproducing an old hack, label it in comments or commit messages as a deliberate temporary compatibility step. Do not accidentally turn hacks into unexplained permanent architecture.

## 10. Recommended End-State Architecture

### 10.1 Build/Dependency Architecture

Target architecture:

- host-tool build stage for macOS arm64 where needed
- target dependency build stage for `ios`
- published dependency bundle artifact keyed by manifest
- app build consumes artifact rather than `lib/ios_arm64` LFS/submodule

Manifest key should include at minimum:

- dependency versions file(s)
- iOS-specific patch files
- Xcode version
- SDK version
- target kind: `ios`

### 10.2 Code Architecture

Goal shape:

- shared file gets a small hook
- iOS-specific implementation goes in new file/module
- avoid spreading `WITH_APPLE_CROSSPLATFORM` branches everywhere unless unavoidable

### 10.3 CI Architecture

Separate workflows/jobs for:

- host tools bootstrap
- iOS dependency bundle build
- Blender iOS configure/build
- package inspection / launch evidence collection if possible

## 11. Dependency Strategy

### 11.1 What Not To Do

- do not redesign the project around Nix
- do not assume generic ARM builds validate iOS
- do not assume Apple Silicon macOS build == iOS build
- do not immediately rebuild the entire heaviest dependency graph if not needed

### 11.2 What To Do

- use the existing Blender dependency system as the orchestrator
- let `ExternalProject_Add` and `add_dependencies` encode most of the graph
- create a thin script/entrypoint that drives host-tools then iOS deps
- move artifact storage to CI outputs/packages instead of LFS/submodule for iOS

### 11.3 Important Dependency Observation

The old branch already disables some heavyweight optional functionality on iOS:

- `USD` disabled
- `Hydra` disabled
- `Cycles OSL` disabled

That is useful. It means the first successful iOS CI path probably does not need the absolute maximum dependency graph.

### 11.4 Probable Risk Ranking For Dependencies

Low or moderate pain:

- zlib
- png
- jpeg
- fmt
- robinmap
- pugixml
- deflate
- pybind11

Medium pain:

- Python
- OpenVDB
- OpenSubdiv
- OpenColorIO

High pain:

- OpenImageIO
- OSL
- FFmpeg
- ISPC

Very high pain:

- USD

### 11.5 Minimal Viable Dependency Strategy

Strong recommendation:

- get a minimal iOS dependency path green first
- defer heavy optional deps unless they block app build parity
- use the current old branch behavior as a guide for what can remain disabled temporarily

## 12. Proposed File Organization For Minimal-Invasive Porting

Use new directories as needed. Example target structure:

- `build_files/build_environment/cmake/platform/ios/`
- `build_files/build_environment/patches/ios/`
- `build_files/cmake/platform/ios/`
- `tools/ios/`
- `.github/workflows/ios-*.yml`

Preferred pattern inside shared dep recipe:

```cmake
if(WITH_APPLE_CROSSPLATFORM)
  include(cmake/platform/ios/ispc_ios.cmake)
endif()
```

Then keep the iOS-specific ugliness in the new helper file, not smeared across the shared recipe.

Only create full standalone `*-ios.cmake` copies when the iOS recipe is fundamentally different, not merely slightly specialized.

## 13. Execution Order

Do the project in this order.

### Phase 1 - Establish Tracking And Guardrails

Checklist:

- [x] Confirm branch is `blender-v5.1-release-IOSPATCH-round2`
- [x] Confirm no work is being done in `blender-READONLY`
- [x] Create or update `memory.md` in the working repo root if the workflow needs a persistent progress ledger
- [x] In `memory.md`, record current goals, last successful workflow, last failed workflow, and next hypothesis
- [x] Create a parity checklist section mapping old iOS features to new implementation status
- [x] Record the 41 non-merge commit list in `memory.md` or link back to this file
- [x] Record the "do not use other branches" rule in `memory.md`
- [x] Record the Actions commands in `memory.md`

Gate before moving on:

- [x] progress ledger exists and is up to date
- [x] parity tracker exists

### Phase 2 - Build Observability Before Build Logic

Do not start by throwing the whole build at CI. First make CI observable.

Checklist:

- [x] Create a tiny temporary workflow that only prints environment/tool versions
- [x] Verify `gh auth status`, Actions permissions, and macOS runner availability before depending on CI for the next phase
- [x] Capture Xcode version
- [x] Capture SDK list/version
- [x] Capture runner image details
- [x] Capture relevant env vars
- [x] Upload a small artifact containing environment metadata
- [x] Prove local `gh workflow run` / poll / log-inspection loop works
- [x] Document the workflow name and output artifact names in `memory.md`

Gate before moving on:

- [x] workflow can be manually triggered on `blender-v5.1-release-IOSPATCH-round2`
- [x] auth/permissions/runners are confirmed good enough for repeated CI iteration
- [x] polling works
- [x] failed log retrieval works
- [x] artifacts are visible and useful

### Phase 3 - Prototype The Dependency Build Entry Point

Build a thin script, not a giant opaque workflow first.

Desired end result:

- one script or narrow command entrypoint that can build host tools and/or iOS deps

Checklist:

- [x] Decide on script location, likely under `tools/ios/`
- [x] Make the script print every important input path and version
- [x] Add explicit modes for `host` and `ios`
- [x] Make the script fail fast with clear messages
- [x] Keep the script small; let CMake orchestrate actual dependency order
- [x] Add manifest generation for the resulting artifact bundle
- [x] Make sure script logs are easy to artifact-upload

Gate before moving on:

- [x] script shape is stable enough to call from temporary workflows

### Phase 4 - Host Tools First, Not Full iOS Build First

The old branch shows that some iOS builds rely on host-built tools and host-side Python/LLVM pieces.

Latest execution note:

- `host-configure` dispatch `23692720328` reached compiler detection and artifact upload successfully, so the driver workflow, checkout path, and dependency entrypoint wiring are already usable.
- The current failure is still workflow-environment setup, not Apple target logic: `build_files/build_environment/cmake/check_software.cmake` stopped on missing Homebrew packages (`autoconf`, `automake`, `glibtoolize`, `yasm`, `dos2unix`, and Homebrew `bison`).
- Keep fixing the runner environment until host configure passes before judging Blender-side dependency CMake behavior.
- Current branch-local `host-tools` workflow intentionally builds real host prerequisites in CI first; it does not yet bootstrap them from a prebuilt bundle.
- After the first successful host-tools build, switch to a GitHub Releases bootstrap model so future runs can download a known-good host-tools bundle instead of recompiling LLVM on every workflow run.
- New evidence from `host-tools` run `23693330218`: `external_python_site_packages` and `ll` both completed successfully on CI, so host Python and host LLVM are now proven buildable on the fresh-port branch.
- The first post-LLVM blocker is `external_ispc`, which fails on Xcode 16.4 with an exception-specification mismatch in ISPC's `util.cpp` against libc++ `__verbose_abort`.
- That makes GitHub Releases bootstrapping immediately worthwhile now: checkpoint the already-good `python`+`llvm` host state so retries reach the ISPC blocker quickly instead of recompiling LLVM for ~2 hours.
- New evidence from `host-tools` run `23695801764`: the branch release tag `blender-v5.1-release-IOSPATCH-round2-deps` is now real and already stores the first successful `python`+`llvm` bootstrap bundle.
- New evidence from `host-tools` run `23698420837`: the restore path works in practice; CI reused the published `python`+`llvm` bundle, skipped the LLVM rebuild, and reached `external_ispc` quickly.
- Practical seed strategy going forward: use readable release assets for host tools (`host-python-macos-arm64.tar.gz`, `host-llvm-macos-arm64.tar.gz`, `host-ispc-macos-arm64-v1.29.1.tar.gz`, `host-python-llvm-buildtree-macos-arm64.tar.gz`) and keep building real iPhoneOS target libraries from source.
- Extra local reference clone now exists at `/home/shlok/Documents/Programming/Sandbox/blender-full-readonly`; it has `lib/macos_arm64` materialized and is useful as a source for host `python` and `llvm`, but it is not the canonical store and does not contain `ispc`.

Checklist:

- [x] Create a temporary workflow that only configures the dependency project for host macOS ARM
- [x] Upload `CMakeCache.txt`, configure logs, and full console log
- [x] Once configure works, create a second temporary workflow/job that builds only the host prerequisites needed by iOS
- [x] Start with likely minimal host prerequisites such as host Python and host LLVM tools if needed
- [x] Confirm the old branch expectations around `CMAKE_DEPS_CROSSCOMPILE_BUILDDIR`
- [x] Confirm where host tools land and how iOS recipes expect to find them
- [x] Artifact-upload the host tool output layout
- [x] Add a branch-scoped GitHub Release bootstrap flow for host-tool bundles
- [x] Download matching host-tool assets from GitHub Releases before falling back to source builds
- [x] Document exact expected host output paths in `memory.md`

Gate before moving on:

- [x] host configure passes
- [x] host tool outputs are discoverable and match the expectations of iOS helper logic

Planned bootstrap convention once the first build is proven:

- Use one prerelease tag per working branch, for example `blender-v5.1-release-IOSPATCH-round2-deps`.
- Store host-tool tarballs as GitHub Release assets, not in git history and not in Actions cache as the source of truth.
- Current readable assets on that tag are `host-python-llvm-buildtree-macos-arm64.tar.gz`, `host-python-macos-arm64.tar.gz`, `host-llvm-macos-arm64.tar.gz`, `host-ispc-macos-arm64-v1.29.1.tar.gz`, and `host-tool-seeds.json`.
- Keep a small manifest asset describing source provenance and reuse intent; `host-tool-seeds.json` now fills that role for the manually seeded assets.
- Future workflows should: restore the readable assets first, unpack them into the expected host-tool layout, and only rebuild/publish when an asset is missing or stale.
- This bootstrap path should preserve observability: log the release tag, asset name, hit/miss result, and unpack destination clearly in the job log.

### Phase 5 - iOS Dependency Bring-Up Before Full Device Build

Because no local Mac is available, CI-first iOS dependency configure/build evidence is the best early proving ground.

Checklist:

- [ ] Create a temporary workflow that configures iOS dependencies only
- [ ] Do not attempt full Blender app build yet
- [ ] Upload config logs and `CMakeCache.txt`
- [ ] Fix path issues, toolchain assumptions, and SDK detection first
- [ ] Keep track of every failing dep in `memory.md`
- [ ] Classify each failure as: missing flag, missing host tool, missing patch, version drift, or unnecessary dep

Gate before moving on:

- [ ] iOS dependency configure is repeatable

Current evidence:

- `23702135538` succeeded for `ios-deps-configure`
- artifact manifest proved `APPLE_TARGET_DEVICE=ios`
- artifact manifest proved `WITH_APPLE_CROSSPLATFORM=ON`
- artifact manifest proved host crosscompile dirs are being passed through
- CI detected `iPhoneOS18.5.sdk` on Xcode `16.4`

### Phase 6 - Easy Dependency Wins Before Hard Dependencies

Do not start with the ugliest deps.

Checklist:

- [ ] Build a first batch of low-pain deps
- [ ] Validate install layout for those deps
- [ ] Artifact-upload the bundle fragment or install tree
- [ ] Confirm include/lib paths match what downstream recipes expect
- [ ] Only after this is stable, move to medium-pain deps

Suggested order:

1. zlib
2. png
3. jpeg
4. fmt
5. robinmap
6. pugixml
7. deflate
8. pybind11

Gate before moving on:

- [ ] several simple deps build reproducibly under iOS mode

Current evidence:

- `23702360631`: `zlib` passed, `png` failed because quoted `CMAKE_SYSTEM_PROCESSOR` broke nested CMake configure under CMake `4.3`
- `23702716309`: `zlib` and `png` passed, `jpeg` failed from new version/toolchain drift rather than a missed archaeology patch
- `23713811661`: `jpeg` failure is now visible directly in the workflow log because `tools/ios/build_deps.py` emits failing log tails
- current follow-up moved `CMAKE_SYSTEM_PROCESSOR:STRING=arm64` into iOS helper `options_apple_ios.cmake` so the fix lives in shared Apple-crossplatform plumbing instead of a `jpeg.cmake` one-off
- `23714250530`: `jpeg` passed after the helper-layer processor fix, and the next blocker moved to `deflate`
- read-only `ios` archaeology shows `deflate.cmake` should disable `LIBDEFLATE_BUILD_GZIP` under `WITH_APPLE_CROSSPLATFORM`; reintroduce that behavior through a helper hook instead of an inline shared-file branch

### Phase 7 - Medium Dependencies

Checklist:

- [ ] Bring up Python carefully
- [ ] Record exactly which cross-compile assumptions are still required from the old branch
- [ ] Minimize invasive Python recipe edits by isolating iOS-specific logic where possible
- [ ] Bring up OpenSubdiv if needed by the app path
- [ ] Bring up OpenColorIO and OpenVDB only when their downstream consumers require them
- [ ] Avoid tackling OSL or USD too early unless they are proven blockers

Gate before moving on:

- [ ] Python path is understood
- [ ] medium deps are either building or explicitly deferred with rationale

### Phase 8 - Hard Dependencies

Checklist:

- [ ] Tackle ISPC with special care around host LLVM tools
- [ ] Tackle OpenImageIO after its upstream dependency stack is stable
- [ ] Tackle OSL only if still required by the chosen iOS feature profile
- [ ] Tackle FFmpeg only when the app build clearly needs it
- [ ] Leave USD disabled initially unless there is a specific reason to revive it early

Gate before moving on:

- [ ] dependency bundle is sufficient for a first Blender iOS configure attempt

### Phase 9 - Blender Build-System Porting

Once dependency path exists, start the Blender-side build-system port.

Checklist:

- [ ] Port Apple target selection logic in the least invasive way possible
- [ ] Add or reintroduce `ios` target handling carefully
- [ ] Keep shared platform file edits minimal
- [ ] Where possible, route iOS special cases into new helper files
- [ ] Add a temporary workflow that only configures Blender for `ios`
- [ ] Upload configure logs and cache files
- [ ] Fix CMake/Xcode integration before attempting full build

Gate before moving on:

- [ ] Blender configure for iOS works or fails in a narrow, understood area

### Phase 10 - Runtime Bootstrap (Entry + GHOST)

This is a major milestone. Do it in small pieces.

Checklist:

- [ ] Port minimal entrypoint path changes from `source/creator/creator.cc`
- [ ] Port minimal build glue from `source/creator/CMakeLists.txt`
- [ ] Bring in `GHOST_SystemIOS`, `GHOST_WindowIOS`, `GHOST_ContextIOS` in the least invasive way possible
- [ ] Prefer new files plus registration hooks rather than mass edits
- [ ] Keep lifecycle logic centralized in `SystemIOS` style, following the later cleanup commit rather than the earlier rougher structure
- [ ] Create a temporary workflow that only tries to compile these targets
- [ ] Upload compile logs on every attempt

Gate before moving on:

- [ ] iOS build reaches app binary/bundle creation or a narrow runtime compile blocker

### Phase 11 - Input, Windowmanager, And UI Parity

Checklist:

- [ ] Port touch event types
- [ ] Port RNA exposure for touch-related event types
- [ ] Port keymap/operator pieces
- [ ] Port multi-finger gesture handling
- [ ] Port file browser and asset shelf multi-finger behavior
- [ ] Port Pencil tap only after the core touch path is solid
- [ ] Keep shared edits thin and localized

Gate before moving on:

- [ ] touch/input-related code compiles cleanly

### Phase 12 - File Access, Sandbox, And Appdir

Checklist:

- [ ] Port `Info.plist` document/browser behavior
- [ ] Port security-scoped file access wrappers
- [ ] Port appdir/resource-path logic
- [ ] Port file menu support
- [ ] Keep app layout assumptions explicit and documented

Gate before moving on:

- [ ] open/save/document behavior compiles and the code path is reviewable

### Phase 13 - Packaging And Archiving

Checklist:

- [ ] Add storyboard and entitlements support
- [ ] Port bundle version handling cleanly
- [ ] Port archive support after basic build works
- [ ] Decide and document whether the current goal is unsigned CI validation or signed distribution/device install
- [ ] Inventory any required Apple signing inputs early: team ownership, bundle-id ownership, certificates/profiles, or explicit decision to defer them
- [ ] Do not optimize for release archive before configure/build/bootstrap work is stable

Gate before moving on:

- [ ] package layout is correct enough for artifact inspection
- [ ] signing scope and missing credentials are explicit

### Phase 14 - Bundle Inspection And Launch Evidence

Checklist:

- [ ] Once build exists, add a temporary workflow to inspect the unsigned app/IPA bundle and collect launch-related evidence where possible
- [ ] Collect logs, crash reports, and bundle info
- [ ] Keep expectations modest; CI proves build/bootstrap and package shape, not final device correctness
- [ ] Record all device-only unknowns explicitly

Gate before moving on:

- [ ] CI artifacts can at least produce actionable package or launch failure info

### Phase 15 - Artifact Production And CI Consolidation

Checklist:

- [ ] Convert temporary dependency workflows into a durable bundle-producing workflow
- [ ] Make artifact naming deterministic
- [ ] Add manifest hashing
- [ ] Split host tools and target bundle logic if useful
- [ ] Keep build and dependency workflows separate enough to debug independently
- [ ] Update `memory.md` with exact bundle contract and consumer steps

Gate before moving on:

- [ ] dependency bundle workflow is reliable enough to serve app builds

## 14. Temporary Workflow Strategy

The next agent should not begin by editing the final production workflow.

Instead use temporary workflows to prove one thing at a time.

Recommended progression:

1. `ios-env-probe.yml`
2. `ios-host-configure.yml`
3. `ios-host-tools.yml`
4. `ios-deps-configure.yml`
5. `ios-deps-basic.yml`
6. `ios-python.yml`
7. `ios-ispc.yml`
8. `ios-blender-configure.yml`
9. `ios-blender-build.yml`
10. `ios-package-inspect.yml`

Rules:

- each workflow should prove exactly one layer or one narrow cluster
- upload artifacts even on failure
- once a temporary workflow becomes stable and useful, either keep it as a narrow tool or merge it into the permanent workflow
- do not lose knowledge: after each success/failure, update `memory.md`

## 15. Observability Requirements For Every Workflow

Every workflow should upload enough information that a future agent can resume without guessing.

Minimum artifact checklist:

- [ ] full console log
- [ ] `CMakeCache.txt`
- [ ] `CMakeFiles/CMakeOutput.log` if present
- [ ] `CMakeFiles/CMakeError.log` if present
- [ ] ExternalProject stamp/log directories if relevant
- [ ] generated manifest if building deps
- [ ] bundle tree or install tree listing if relevant
- [ ] Xcode/SDK version metadata
- [ ] environment summary

If using `xcodebuild`, also capture:

- [ ] raw `xcodebuild` log
- [ ] `.xcresult` if available
- [ ] device or package-inspection logs if a run was attempted

## 16. Easy Wins To Start With

Do these first because they improve velocity without committing to hard architectural choices.

### 16.1 Easy Win Checklist

- [x] Add the progress ledger (`memory.md`) and parity tracker
- [x] Add an environment-probe workflow with strong artifact output
- [x] Add a script scaffold for iOS dependency build orchestration
- [x] Add manifest generation for dependency bundles
- [ ] Add a narrow host-tools configure/build workflow
- [ ] Add an iOS configure-only workflow

These are low-risk and increase visibility immediately.

## 17. Hard Problems To Defer Until Setup Is Good

Do not rush into these before the scaffolding exists.

- full runtime correctness on real devices
- USD re-enablement
- Hydra/Storm support
- OSL parity if still disabled for iOS
- full FFmpeg surface
- final distribution/archive polish
- App Store-grade packaging assumptions

## 18. Concrete Parity Checklist Buckets

Maintain this as a live status tracker in `memory.md` or a dedicated parity file.

### 18.1 Build / Toolchain

- [ ] Apple target selection
- [ ] `ios` target handling
- [ ] host/target split
- [ ] host tools pathing
- [ ] bundle layout routing
- [ ] archive support

### 18.2 Dependencies

- [ ] dependency script exists
- [ ] manifest generation exists
- [ ] host tools built in CI
- [ ] device deps bundle strategy defined
- [ ] LFS/submodule path deprecated or removed for iOS

### 18.3 GHOST / Runtime

- [ ] `GHOST_SystemIOS`
- [ ] `GHOST_WindowIOS`
- [ ] `GHOST_ContextIOS`
- [ ] main entry refactor
- [ ] app delegate flow
- [ ] orientation handling
- [ ] home indicator behavior

### 18.4 Input

- [ ] touch event types
- [ ] multi-finger taps
- [ ] edge swipe gestures
- [ ] Pencil tap
- [ ] touch offset fixes
- [ ] window switching fixes
- [ ] browser/asset-shelf multi-finger scroll
- [ ] editor interaction shims (`interface_handlers`, `view2d_ops`, `view3d_navigate_*`)

### 18.5 Rendering

- [ ] Metal guards and fixes
- [ ] Cycles Metal fixes
- [ ] HDR/EDR
- [ ] ProMotion

### 18.6 File / Sandbox

- [ ] `Info.plist` document types
- [ ] security-scoped file access
- [ ] storage wrapper behavior (`storage_apple.mm` or equivalent)
- [ ] appdir/resource path logic
- [ ] file browser integration

### 18.7 Packaging

- [ ] storyboard
- [ ] entitlements
- [ ] archive support
- [ ] version string handling
- [ ] signing/export strategy documented

## 19. How To Decide Whether To Make A New File Or Edit A Shared File

Use this decision test.

Make a new iOS-specific file if:

- the logic is mostly iOS-only
- the shared file would otherwise grow a large iOS-only branch
- the behavior is likely to change across releases
- the old branch hacked around version-specific behavior

Edit the shared file directly only if:

- the required hook is tiny
- the behavior is truly generic
- the edit benefits future platforms too
- creating a separate file would add complexity without reducing coupling

## 20. How To Treat External Library Patches

Important concept:

- the old iOS branch patches external library source builds at build time
- these are not just flags; some deps genuinely require patching

Recommended treatment:

- keep patches isolated under iOS-oriented patch paths where possible
- keep shared recipe edits to patch selection and a few arguments
- if an old patch no longer applies because upstream moved, do not force it; re-evaluate the intent and reimplement only the still-needed change
- do not assume every old patch is still necessary on `v5.1`

## 21. Testing Philosophy

Because there is no local Mac or iPad available, testing must be layered.

### 21.1 What CI Can Reliably Prove

- toolchain setup correctness
- dependency build correctness
- iOS build correctness
- at least some bootstrap/runtime evidence from CI artifacts
- artifact shape and packaging quality

### 21.2 What CI Cannot Fully Prove

- real iPad touch feel
- device-specific Metal capabilities
- sandbox/document interactions under real user flows
- actual shipping behavior on physical hardware

Therefore:

- use CI build/package evidence as the main automated proving ground
- keep a list of device-only unknowns
- do not pretend CI package success equals finished device support

## 22. What Not To Waste Time On Early

- full Nix-based rearchitecture
- generic ARM portability as a proxy for iOS
- premature optimization of release archive flow
- elegant final cleanup before basic CI proof exists
- trying to port everything in one giant commit

## 23. Recommended Commit Strategy In The Working Branch

Do not make enormous mixed commits.

Prefer commits like:

- observability / workflow scaffolding
- dependency entrypoint script
- host-tools bootstrap
- iOS configure support
- iOS build shim layer
- GHOST bootstrap
- touch event plumbing
- file/document support
- packaging/archive support

And for each commit:

- keep scope narrow
- keep rationale clear
- mention whether it is parity, scaffolding, or cleanup

## 24. Definition Of Done For This Port

True completion means all of these are true:

- [ ] every meaningful iOS branch feature has a parity status
- [ ] no feature from the old iOS branch was silently dropped
- [ ] dependency production no longer depends on pulling `lib/ios_arm64` as the main truth source
- [ ] CI can produce the dependency bundle
- [ ] CI can build Blender for `ios`
- [ ] bundle inspection or launch-evidence runs produce useful results
- [ ] invasive edits to shared files are minimized
- [ ] future version porting is easier than the old branch model

## 25. Resume Checklist For A Future Agent After Context Compaction

If context is lost, do this in order:

- [ ] Read this file fully
- [ ] Read `memory.md`
- [ ] Confirm branch is `blender-v5.1-release-IOSPATCH-round2`
- [ ] Check latest workflow runs on that branch
- [ ] Inspect latest failure logs
- [ ] Inspect last successful artifact bundle if one exists
- [ ] Update `memory.md` with current understanding before changing code
- [ ] Continue from the first unchecked item in the parity checklist or phase checklist

## 26. Immediate Suggested First Session

If starting fresh, do this exact sequence:

- [x] verify working branch in the writable repo
- [x] create/update `memory.md`
- [x] add environment-probe workflow
- [x] run it with `gh workflow run ... --ref blender-v5.1-release-IOSPATCH-round2`
- [x] poll and inspect logs/artifacts
- [x] add host-tools configure workflow
- [x] run it and inspect artifacts
- [x] add thin iOS dependency build script scaffold
- [ ] add iOS deps configure workflow
- [ ] only after that, start touching build-system files

That is the lowest-risk on-ramp.

## 27. Final Strategic Reminder

The old `ios` branch proved that iOS support is possible.

This port should prove that iOS support can be maintained.

That means:

- feature parity with the old branch
- less invasive architecture
- CI as the source of truth
- narrow, observable steps
- no silent feature loss
- constant attention to future `v5.2+` forward-port cost
