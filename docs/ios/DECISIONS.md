# Blender iOS decisions

## ADR-0001: Freeze v5.2.0 and use a release-relative donor delta

- Status: accepted
- Date: 2026-08-10

Production work begins at `v5.2.0` (`fbe6228777e7d9af...`). The official iOS
branch remains read-only at `a1de44dd54af...`. Its reliable donor definition is
the exact `v5.1.2..origin/ios` delta (213 files), because the donor tip contains
a large release tree refresh. The port branch never merges `origin/ios`.

## ADR-0002: Split internal control from external bulk data

- Status: accepted
- Date: 2026-08-10

Git source/worktrees and small control files stay internal. Downloads, dependency
and Blender build trees, installs, temporary compiler data, large logs, and
artifacts live under `/Volumes/BlenderBuild/blender-ios`. The expected APFS
volume UUID is `EC4DA5DD-B2A4-4056-934E-5B703096BEF1`. Missing, read-only, or
changed media stops work.

## ADR-0003: Keep simulator and unsigned-device truth claims separate

- Status: accepted
- Date: 2026-08-10

The simulator artifact may use a local/ad-hoc signature if Xcode requires one.
The device handoff must contain no developer identity, team, provisioning
profile, signer entitlements, or bundle signature.

Packet N040 proved the following Xcode 26.5 build overrides with a minimal UIKit
app for both SDKs:

```text
CODE_SIGNING_ALLOWED=NO
CODE_SIGNING_REQUIRED=NO
CODE_SIGN_STYLE=Manual
```

The arm64 simulator executable is linker-signed ad hoc, with no team identifier,
profile, or `_CodeSignature` directory. The arm64 device bundle is reported by
`codesign` as not signed at all and contains neither an embedded profile nor a
`_CodeSignature` directory. Both executables pass the target-platform ABI audit.
Evidence: `/Volumes/BlenderBuild/blender-ios/artifacts/20260811T044431Z-8f74cae544cd-signing-probe/signing-report.json`.

## ADR-0004: Content-address dependency builds by full cross-compile contract

- Status: accepted
- Date: 2026-08-11

Each simulator or device dependency tree gets a distinct SHA-256 cache key over
the frozen Blender release, dependency versions, iOS framework and patch content,
Xcode/SDK/CMake versions, target triple, deployment target, and feature profile.
Build and install prefixes are immutable per key. Downloads and source packages
are shared on the bulk volume, while host executables remain in a separate native
directory and are never taken from the target prefix.

The generic iOS framework uses an explicit SDK path and target triple, arm64,
`CMAKE_SYSTEM_NAME=iOS`, static-library try-compiles, and target-only library,
include, and package discovery. Program discovery remains host-only. The first
simulator configure is green at cache key
`b4566ec98fb7113e621f79f71f83fb3f49f6c2607886c05c0bcf2c1f5b2bddfd`.

## ADR-0005: Accept dependency families only after archive-member ABI audit

- Status: accepted
- Date: 2026-08-11

An installed header or a successfully linked library is insufficient evidence
for cross-compilation. Each harvested family receives a manifest with file
checksums, architecture information, and the `LC_BUILD_VERSION` platform for
every object in each static archive. A family is green only when all members are
arm64 `IOSSIMULATOR` and all manifests share one cache key.

Packet N111 proves zlib, bzip2, xz/liblzma, SQLite, libxml2, libdeflate, Brotli,
and OpenSSL under cache key
`1ae9905260312a93e8e7174f3abcf94a6b4cc6b380ecc8f9cf329e0989853788`.
The combined evidence is
`/Volumes/BlenderBuild/blender-ios/artifacts/n111-1ae9-bootstrap-summary.json`.

Packet N112 extends the same acceptance rule to FreeType 2.13.3 and replays all
eight prerequisites under cache key
`0edd9316d7de66d11228410643ad30e3bc52970f61a5b0394c010600f227603e`.
Evidence:
`/Volumes/BlenderBuild/blender-ios/artifacts/n112-0edd-font-bootstrap-summary.json`.

## ADR-0006: Split Meson build-machine generators from iOS target code

- Status: accepted
- Date: 2026-08-11

Meson dependencies receive separate native and cross files. Target C/C++
compilers carry the arm64 simulator triple and SDK; native generators use the
host SDK and local ad-hoc linker signing required to execute arm64 tools from
the external volume. No identity or team is involved. Generic `CFLAGS`,
`CXXFLAGS`, `LDFLAGS`, and `IPHONEOS_DEPLOYMENT_TARGET` are cleared at Meson
setup so they cannot contaminate the native compiler.

This removes false iOS dependency edges from HarfBuzz and FriBidi to target
Python and its site packages. The generated graph falls from 301 to 286 edges.
Packet N113 proves HarfBuzz 10.0.1 and FriBidi 1.0.12, including FreeType,
Brotli, and zlib integration, under cache key
`b0340de3aebc1a84777d6b423050aa638e7d9b428282f844f1b7e95e5ca60591`.

## ADR-0007: Keep image-codec builds static and iOS harvesting explicit

- Status: accepted
- Date: 2026-08-11

The iOS lane disables shared libraries, codec tools, and tests where each
upstream project exposes those controls. Compatibility policy overrides for
older codec CMake projects are confined to Apple cross-platform builds. Each
recipe explicitly harvests its installed headers and static libraries because
the desktop harvest helper does not cover this cross-platform configuration.

Packet N114 proves libjpeg-turbo, libpng, libtiff, OpenJPEG, WebP, and zlib
under cache key
`ec24602d8e68ccfaae25ad54e8130ee036d50ea0169fcf7ad71b43b9a45bafcb`.
Every object in every harvested archive is arm64 `IOSSIMULATOR`. Evidence:
`/Volumes/BlenderBuild/blender-ios/artifacts/n114-ec24-image-codecs-summary.json`.

## ADR-0008: Use static geometry libraries and simulator-native ISA flags

- Status: accepted
- Date: 2026-08-11

The iOS lane builds oneTBB, OpenSubdiv, and Embree as static libraries. Embree
uses arm64 NEON and does not inherit macOS-only deployment or x86 SSE flags;
OpenSubdiv disables OpenGL and TBB integration for this reduced lane. Explicit
iOS harvest steps retain headers, CMake metadata, and archives while avoiding
runtime dylib bundling before the application shell exists.

Packet N115 proves all three families under cache key
`9e317f684ffac13636fc5d91f0720b2a33a38569e7895f3c3bfffdb08dd10f9e`.
Every archive member is arm64 `IOSSIMULATOR`. Evidence:
`/Volumes/BlenderBuild/blender-ios/artifacts/n115-9e31-geometry-summary.json`.

## ADR-0009: Keep first-pixel dependencies static and defer embedded Python

- Status: accepted
- Date: 2026-08-11

The first-pixel profile keeps Python, TBB, HarfBuzz, FriBidi, Cycles, USD,
OpenVDB, Embree, OpenSubdiv, OSL, and media integration out of the application
link. Host Python remains available only for source generation. The target
closure includes the mandatory color, image, font, compression, and math
libraries as static arm64 simulator artifacts.

Packet N116 proves 1,181 harvested files under cache key
`e4b775f99fd0d6b27a0ec7bc6425dd9923357c59b1020567af077ec135b09957`.
Every binary is arm64 `IOSSIMULATOR`, OpenColorIO exports no macOS-only
frameworks, and OpenImageIO is built without target Python or tools. Evidence:
`/Volumes/BlenderBuild/blender-ios/artifacts/n116-e4b7-first-pixel-closure-manifest.json`.

## ADR-0010: Prove the UIKit/Metal launch contract before completing GHOST

- Status: accepted
- Date: 2026-08-11

The revision-matched native tools (`makesdna`, `makesrna`, `datatoc`, and
`shader_tool`) are built from the frozen worktree and consumed as host
executables by the simulator build. Blender's reduced graph configures and its
core compiles until the known Cocoa-to-iOS GHOST boundary.

A repository-native UIKit shell independently proves the application lifecycle,
Metal device and command queue, drawable presentation, and visible first frame.
It uses no signing identity or provisioning profile. Packet P500 launched on an
iPhone 17 / iOS 26.5 simulator and emitted `boot`, `metal_ready`, and
`first_frame`; evidence is
`/Volumes/BlenderBuild/blender-ios/artifacts/p500-first-pixel-result.json`.

## ADR-0011: One universal iOS bundle for iPhone and iPad

- Status: accepted
- Date: 2026-08-12

The product is a single bundle id (`org.blenderfoundation.blender.ios`) with
`UIDeviceFamily` 1 and 2. There is no second target, second bundle id, or
iPhone-compatibility wrapper. iPhone keeps the proven landscape-left/right
orientation contract. iPad declares landscape plus portrait and portrait
upside down so it is a native iPad app. `UIRequiresFullScreen` stays true.

Packet P530 proves the same simulator `.app` on iPhone 17 and iPad Pro
13-inch (M5), both iOS 26.5. iPad is `UIUserInterfaceIdiomPad`, not an
iPhone compatibility window. iPadOS 26 windowed-apps chrome may still
surround the scene; that is not a second bundle. The unsigned device
(`iphoneos`) lane remains deferred: no owner signing, no provisioning,
no physical-device claim. Evidence:
`/Volumes/BlenderBuild/blender-ios/artifacts/p530-universal-simulator-result.json`.

## ADR-0012: Ship one audited unsigned IPA for both device families

- Status: accepted
- Date: 2026-08-13

The physical-device handoff uses a distinct arm64 `iphoneos` dependency prefix,
build tree, and minimal feature profile. Its deterministic IPA contains one
`Payload/Blender.app` with bundle id `org.blenderfoundation.blender.ios` and
`UIDeviceFamily` 1 and 2. The packager audits the device ABI and refuses
provisioning artifacts, signing metadata, bundle signatures, and embedded
Mach-O signatures.

The IPA is deliberately unsigned. Repository evidence proves compilation,
linking, bundle resources, archive integrity, and the unsigned contract. Only
the owner can prove physical launch after applying their signing identity and
provisioning profile.

## ADR-0013: Package every Python extension as an iOS framework

- Status: accepted
- Date: 2026-08-21

iOS permits bundled native Python modules only when each executable image is in
a code-signable bundle location. The application therefore embeds CPython as
`Python.framework` and converts every `.so` extension into a module-named
framework under `Blender.app/Frameworks`. Bidirectional marker files preserve
the import path and make repeated CMake installs deterministic. The packager
also removes wheel-provided static development archives because they are not
runtime imports and would leave Mach-O code outside `Frameworks`.

## ADR-0014: Cross-build NumPy from target CPython sysconfig data

- Status: accepted
- Date: 2026-08-21

The dependency build must not execute the target interpreter. A disposable
native virtual environment supplies Meson, Cython, and pip, while a generated
startup module exposes the selected iOS CPython platform, ABI suffix, include
paths, and sysconfig variables. SDK-pinned wrappers and a Meson cross file keep
compiler and linker discovery on the chosen iPhoneOS or Simulator target.

NumPy is initially configured without an external BLAS, with the minimum arm64
CPU baseline and runtime dispatch disabled. This establishes functional ABI and
runtime parity first; Apple Accelerate integration is a separate performance
slice so it cannot obscure Python/import correctness.

## ADR-0015: Replace process-only background services at the transport seam

- Status: accepted
- Date: 2026-08-21

CPython deliberately omits `_multiprocessing` on iOS because applications
cannot fork or spawn child executables. The port does not force-build an API
that the operating system cannot honor. Instead, Blender's Extensions and
remote asset-library downloader selects a thread context on `sys.platform ==
"ios"`. Its connection, event, and worker objects implement the subset of the
existing multiprocessing context used by `BackgroundDownloader`, so queueing,
cancellation, progress reporting, callbacks, and shutdown retain one code path.

Desktop platforms continue to use the existing spawn-based subprocess without
behavioral changes. The iOS runtime smoke starts and stops the worker and the
thread transport has host tests for duplex messages, blocking poll, event, and
worker lifecycle.

## ADR-0016: Share one target-aware Python extension build environment

- Status: accepted
- Date: 2026-08-21

Native Python package frontends must run on macOS while emitting code for the
selected iOS CPython ABI. NumPy, zstandard, and future extension recipes share
one disposable virtual environment with pinned frontend versions, localized
target sysconfig data, and SDK-pinned compiler and linker wrappers. Each device
lane creates its own environment. Build tools never enter the application
through this environment; only audited wheel outputs are harvested into target
site-packages.

zstandard 0.25.0 uses the upstream system-zstd build mode, disables its unused
CFFI backend, and statically links the target zstd archive. Its sole native
module is packaged through the same framework conversion used for CPython and
NumPy. Runtime acceptance requires a real compress/decompress round trip on
both iPhone and iPad simulators, not merely a successful import.

The release path audit continues to reject paths captured from build machines.
Installed wheel `METADATA` and `PKG-INFO` descriptions are deterministic
third-party prose and may contain upstream documentation examples, so those
description files are excluded from build-path findings under a regression
test. Executable, configuration, manifest, and other package content remains
in scope.

## ADR-0017: Establish Cycles with the portable CPU renderer first

- Status: accepted
- Date: 2026-08-21

Cycles enters the iOS product through one shared simulator/device profile: the
portable CPU renderer and static oneTBB, without the TBB malloc proxy. The
Cycles Metal device, Embree, OSL, and path guiding stay off until separate
slices can prove their target dependencies and runtime behavior. This keeps
the first failure boundary at CPU correctness and does not change Blender's
already-enabled Metal viewport backend.

Apple cross-platform configuration discovers oneTBB through its exported CMake
target because the static iOS package exposes a configuration-specific archive
rather than the legacy library variable used by desktop builds. The workaround
is scoped to iOS; desktop link behavior remains unchanged. iOS arm64 also skips
host-default x86 ISA probes and directly includes NEON declarations needed by
the scalar CPU kernel's native half conversion.

oneTBB upstream discourages static distribution, but this lane links exactly
one audited archive into the main executable and does not load another TBB
copy. That is safer for the current unsigned iOS handoff than leaving a raw
dylib in the bundle. A future dynamic TBB experiment must package it as a
signed framework and repeat both ABI and render acceptance before replacing
this boundary.

Acceptance is not an import-only probe. After startup scripts register the
desktop Cycles add-on, the iOS test path requires a CPU device, performs a
one-sample 8 by 8 render, validates a written PNG in the sandbox, removes the
probe output, and restores the scene settings. The same signed simulator app
passes this render on iPhone and iPad.

## ADR-0018: Compile Cycles Metal but require tier-2 hardware

- Status: accepted build boundary; runtime acceptance pending
- Date: 2026-08-21

The production iOS profiles compile the Cycles Metal device while retaining
portable CPU Cycles as the accepted fallback. Cross-build discovery points at
the Metal framework inside `CMAKE_OSX_SYSROOT`; it must not search the macOS
host SDK. macOS-only IOKit GPU-core probing and compiler-tuning selectors are
excluded from iOS, and target availability checks cover both Apple platforms.

Cycles' bindless Metal kernel requires tier-2 argument buffers. Xcode 26.5's
iOS Simulator device advertises tier 1 and rejects the pipeline because it
supports 31 buffers while the kernel declares roughly 303 resources. This is a
simulator capability limit, not a reason to weaken or split the desktop kernel.
iOS device enumeration therefore exposes Metal only when
`argumentBuffersSupport == MTLArgumentBuffersTier2`. Missing simulator working
set telemetry uses the minimum 65,536-state pool rather than reporting false
out-of-memory, which keeps diagnostics accurate without exposing the
incompatible GPU.

Both simulator and unsigned iPhoneOS applications compile and link the target
Metal sources and pass ABI/bundle audits. Simulator CPU render acceptance stays
green. Runtime acceptance for Metal requires an owner-signed launch on real
tier-2 iPhone and iPad hardware using the same real-PNG gate; until then, docs
and artifact names call the build Metal-capable rather than Metal-proven.

## ADR-0019: Give UIKit scene ownership to one Blender session

- Status: accepted
- Date: 2026-08-21

The iOS bundle declares one `UIWindowScene` and starts the Blender callback from
the scene connection instead of the application launch callback. Blender's
GHOST system and window manager remain process-wide, so advertising multiple
UIKit scenes would create two owners for global state. The manifest therefore
sets `UIApplicationSupportsMultipleScenes` to false until Blender has an
explicit multi-session design.

`IOSSceneDelegate` handles foreground activation and scene-routed file URLs.
The app delegate keeps security-scoped document URLs because those handles live
for the process, not one callback. GHOST creates native windows with
`initWithWindowScene:` and reads bounds and scale from the attached scene and
screen. `UIScreen.mainScreen` is forbidden in the iOS GHOST implementation
because it gives the wrong geometry for an iPad windowed scene or an external
display.

MetalKit drawable-size changes enter `GHOST_SystemIOS::handleWindowEvent` so
Blender updates its drawing context before consuming the resize event. The
same source compiles for iPhoneOS and the simulator. iPhone and iPad simulator
launches retain the Python, NumPy, zstandard, threaded HTTP, and real CPU
Cycles-render acceptance markers. A physical owner-signed pass must still
cover rotation, background and foreground, external displays, and safe-area or
scale changes.

## ADR-0020: Preserve native pixels across UIKit scene conversion

- Status: accepted
- Date: 2026-08-21

GHOST's screen/client APIs and event payloads use native pixels, while UIKit
coordinate-space conversion operates in logical points. Passing coordinates
through unchanged only works when a window fills a display and begins at its
origin; it misplaces pointer state in an iPadOS windowed scene or on an external
display.

The iOS window now converts native pixels to points using the attached
`UIWindowScene` screen scale, maps through `UIWindowScene.coordinateSpace`, and
rounds the result back to native pixels. The reverse path is symmetrical.
There is no Y-axis flip because both UIKit and GHOST use top-left coordinates on
iOS. Cached cursor state is client-relative, and polling converts it to scene
screen coordinates. A requested cursor position is converted back to client
space before its software event is queued; UIKit still does not permit an app
to warp the physical pointer.

The contract is protected by source tests and by successful arm64 device and
simulator compilation. Final interaction acceptance still requires an
owner-signed iPad with a trackpad, a nonzero-origin window, and an external
display pass.

## ADR-0021: Own UIKit input state until GHOST consumes it

- Status: accepted
- Date: 2026-08-22

`NSString.UTF8String` returns storage owned by the string. The old keyboard path
saved that pointer and then cleared the `UITextField`, which left GHOST with a
dangling result. The Cancel snapshot had the same lifetime problem because it
kept an autoreleased string between callbacks.

`GHOSTUIWindow` now copies keyboard text into `std::string` and copies the
original `NSString`. Empty text remains a valid result. A failed
`becomeFirstResponder` call returns `GHOST_kFailure` instead of marking the
keyboard active. Teardown first blocks edit-end callbacks, then removes target
actions, gesture recognizers, and the Pencil delegate before releasing every
object owned by the input window. The cleanup method is idempotent because the
C++ destructor calls it before releasing UIKit and Objective-C `dealloc` calls
it again if the scene retained the window.

The port also removes keyboard-frame and GameController connection observers
that only wrote unread state. Hardware-key events still arrive through
`pressesBegan`, `pressesEnded`, and `pressesCancelled`; those observers were not
part of event delivery.

## ADR-0022: Size Metal backing textures from the active drawable

- Status: accepted
- Date: 2026-08-22

An iOS Metal view can occupy only part of an iPad scene, move to an external
display, or change native-pixel size without matching the process main screen.
Using `UIScreen.mainScreen` to allocate Blender's overlay texture therefore
produced the wrong framebuffer outside a full-screen primary-display window.

`GHOST_ContextIOS` now treats `MTKView.drawableSize` as the authoritative pixel
size. If UIKit temporarily reports zero in either dimension while the scene is
inactive or resizing, the context preserves its last valid backing texture and
waits for a later drawable update instead of allocating a fabricated fallback.
An offscreen context has no window scene to consult, so its private Metal view
starts at a deterministic 1 by 1 size rather than a hard-coded device
resolution.

Source contracts forbid process-main-screen reads throughout the iOS GHOST
system, window, and context implementations. Both target lanes compile, the
iPhone and iPad simulators retain their full Python and CPU Cycles runtime
gates, and recursive product audits pass. Exact rotation, Stage Manager resize,
and external-display behavior still requires owner-signed physical-device
acceptance.

## ADR-0023: Present at most once per MetalKit delegate frame

- Status: accepted
- Date: 2026-08-22

Blender can request multiple buffer swaps while processing one UI frame, but a
MetalKit drawable has one presentation lifetime. The inherited iOS path counted
every request and tried to infer duplicate presentation by comparing the raw
address of the current drawable with a process-global, unretained pointer. A
released drawable object can be recreated at the same address, so that state
was neither lifetime-safe nor scoped to a context.

The window now coalesces swap requests into one pending-present bit. Every
`drawInMTKView` callback opens a presentation frame before servicing an older
pending request or running Blender's main-loop body. The context resets its
per-frame guard at that boundary and accepts no second submission until the
next callback. A pending request is consumed before calling the presentation
path so a later request cannot be erased. Continuous MetalKit drawing supplies
the next callback; the old `setNeedsDisplay` call was ineffective because the
view has `enableSetNeedsDisplay` disabled and has been removed.

This makes scheduling explicit rather than suppressing a diagnostic. The old
global drawable pointer and counter are gone, both target lanes compile, and
repeated iPhone and iPad simulator launch/render passes complete without the
previous duplicate-present messages. Physical display timing remains part of
the owner-signed device gate.
