# Morning handoff — 2026-08-22

Portable CPU Cycles remains green, and the production simulator and device
profiles compile the native Cycles Metal device. UIKit now owns the app through
a single window scene with scene-relative geometry and drawable resize events.
Screen/client conversion now maps through that scene while preserving GHOST's
native-pixel coordinate contract.
Metal overlay textures now take their native-pixel size from the current
`MTKView` drawable, including iPad windowed scenes and external-display-ready
geometry, while offscreen contexts use a neutral 1 by 1 backing.
Metal presentation now coalesces Blender's swap requests and submits at most
one drawable per MetalKit delegate frame without global drawable tracking.
Apple Pencil state now starts on contact, follows only its tracked touch, and
keeps force and tilt in valid GHOST ranges.
UIKit keyboard results now use owned UTF-8 storage, and every input target and
delegate detaches before a GHOST window releases its native objects.
Three-finger drag now reaches Blender's standard viewport-pan mapping while
one-finger tools, two-finger orbit, and pinch zoom keep their existing roles.
Generic Metal ownership now follows Objective-C create rules, deletes compute
PSO cache records, and has a reproducible five-minute rendered-viewport soak.
The same simulator
`Blender.app` runs the desktop UI on iPhone and iPad, imports CPython 3.13.13,
NumPy 2.3.4, and zstandard 0.25.0, starts the thread-backed Extensions worker,
and completes a real one-sample CPU Cycles render. The iPhoneOS product builds
and packages as one universal unsigned IPA for device families 1 and 2.

## Green outcomes

- Simulator and device builds enable Cycles CPU, Cycles Metal, and oneTBB with
  identical feature settings. Metal framework discovery stays inside the
  selected target SDK.
- iOS exposes the Cycles Metal device only on tier-2 argument-buffer hardware.
  Xcode 26.5's simulator GPU exposes tier 1 and supports 31 buffers, while the
  Cycles bindless pipeline needs roughly 303 resources. The incompatible
  simulator device stays hidden instead of failing during shader compilation.
- iPhone 17 Pro and iPad Pro 13-inch (M5) simulator launches emit
  `BLENDER_IOS_CYCLES_READY=cpu-render` after producing and validating an 8 by
  8 PNG through Blender's registered Cycles engine.
- The final arm64 iPhoneOS build completes 3,628 actions and a clean incremental
  install. App and oneTBB inputs pass recursive target ABI audits.
- The unsigned IPA contains 74 frameworks and no loose `.so` or `.a` files.
  Bundle policy, private-path, archive-integrity, and packaging checks pass.
- The device and simulator products pass recursive ABI, bundle, and private-path
  audits after compiling the Metal sources.
- `IOSSceneDelegate` owns startup, activation, and document-open delivery.
  GHOST attaches windows to that scene and no longer reads the process main
  screen for window geometry or scale.
- The clean-state iPad Maestro flow connects the scene, enters Quick Setup, and
  reaches the desktop cube viewport. Final iPhone and iPad launches retain all
  Python and CPU Cycles markers after the lifecycle change.
- Scene screen/client conversion and both directions of cached software cursor
  state are protected against regression.
- Input teardown is idempotent, blocks edit-end callbacks, and releases the
  window's manually owned UIKit input objects.
- Metal framebuffer allocation follows the current drawable, preserves the
  last valid texture through zero-size scene transitions, and contains no
  process-main-screen fallback.
- iPhone and iPad complete the full runtime gate without the previous
  duplicate-present diagnostic.
- Pencil pressure/tilt state is safe against zero force ranges and unrelated
  simultaneous finger endings; physical sensor acceptance remains pending.
- The final five-minute EEVEE soak reports zero application-owned leak roots
  and zero leak growth on both simulator form factors. iPhone latter-half RSS
  growth is 1.1 MiB; iPad is 11.1 MiB with visible reclamation cycles.
- All 100 tests under `build_files/ios/tests` pass.

## Evidence

- Simulator build:
  `/Volumes/BlenderBuild/blender-ios/build/ios-simulator-python-e7de/bin/Blender.app`
- Unsigned-device build:
  `/Volumes/BlenderBuild/blender-ios/build/ios-device-python-5353b/bin/Blender.app`
- Unsigned IPA:
  `/Volumes/BlenderBuild/blender-ios/artifacts/20260821-scene-lifecycle/Blender-5.2.0-Python-NumPy-Zstandard-Cycles-CPU-Metal-capable-Scene-lifecycle-iPhone-iPad-unsigned.ipa`
- IPA SHA-256:
  `0e7d4057ed1ac69127d57ce40f9187f4e13454a47024119b2f657a84f0e77c2e`
- Window-coordinate unsigned IPA:
  `/Volumes/BlenderBuild/blender-ios/artifacts/20260821-window-coordinates/Blender-5.2.0-Python-NumPy-Zstandard-Cycles-CPU-Metal-capable-Window-coordinates-iPhone-iPad-unsigned.ipa`
- Window-coordinate IPA SHA-256:
  `cecb1064ccf94be3ecf9e1b66c6c69c3e5bccdbd17cc9ca7d6f6d2a6280be3ce`
- Input-lifetime unsigned IPA:
  `/Volumes/BlenderBuild/blender-ios/artifacts/20260822-input-lifetime/Blender-5.2.0-Python-NumPy-Zstandard-Cycles-CPU-Metal-capable-Input-lifetime-iPhone-iPad-unsigned.ipa`
- Input-lifetime IPA SHA-256:
  `e19deb007d1586de6cbfe10e92e7a00ea4e1f0dc463eab4fc0f227619aefa43a`
- Drawable-size unsigned IPA:
  `/Volumes/BlenderBuild/blender-ios/artifacts/20260822-metal-drawable-size/Blender-5.2.0-Python-NumPy-Zstandard-Cycles-CPU-Metal-capable-Drawable-size-iPhone-iPad-unsigned.ipa`
- Drawable-size IPA SHA-256:
  `2626fe3869adb377ee8174f2c1a26e79bf38a59e91679412a16782f4badb041c`
- Present-scheduling unsigned IPA:
  `/Volumes/BlenderBuild/blender-ios/artifacts/20260822-metal-present-scheduling/Blender-5.2.0-Python-NumPy-Zstandard-Cycles-CPU-Metal-capable-Present-scheduling-iPhone-iPad-unsigned.ipa`
- Present-scheduling IPA SHA-256:
  `1a75df365993c7dabd6512b0ddfab45014f3218daab85db9377c0e692057f7f1`
- Pencil-state unsigned IPA:
  `/Volumes/BlenderBuild/blender-ios/artifacts/20260822-pencil-state/Blender-5.2.0-Python-NumPy-Zstandard-Cycles-CPU-Metal-capable-Pencil-state-iPhone-iPad-unsigned.ipa`
- Pencil-state IPA SHA-256:
  `a31965f9b66d324a3b9c2e9d869628ab2e4773112e0e90275e4935344ba5862a`
- iPad acceptance recording:
  `/Volumes/BlenderBuild/blender-ios/artifacts/20260821-scene-lifecycle/Blender-iPad-scene-lifecycle.mp4`
- Memory-soak unsigned IPA:
  `/Volumes/BlenderBuild/blender-ios/artifacts/20260823-memory-soak/Blender-5.2.0-Python-NumPy-Zstandard-Cycles-CPU-Metal-capable-Memory-soak-iPhone-iPad-unsigned.ipa`
- Memory-soak IPA SHA-256:
  `c99ee373c2cf85865ba8ff01472a2da72d06d1b3dda1de4d80a4ad13b4ce8b72`
- Current iPad release recording:
  `/Volumes/BlenderBuild/blender-ios/artifacts/20260822-touch-memory/Blender-iPad-touch-memory-final.mp4`
- Current recording review permalink:
  `https://planista.shloklab.us/KRHbnyG-JQXGTnpy`
- Current recording SHA-256:
  `1af202110da4fc55c9b5887e909ae3f719e53b5b95dd72f1294958e49a359d96`

## Resume

1. Read `docs/ios/HANDOFF.md`, `docs/ios/LIMITATIONS.md`, ADR-0017, and this
   file before changing a feature profile.
2. Use `blender_ios_sim.cmake` and `blender_ios_device.cmake` as the production
   profiles. Keep their Cycles settings synchronized and rebuild host tools
   whenever the generated-feature manifest changes.
3. Owner-sign the Metal-capable IPA and run
   `BLENDER_IOS_CYCLES_SMOKE=METAL` on tier-2 iPhone and iPad hardware. Preserve
   portable CPU Cycles as the fallback until both physical renders pass.
4. On the same signed devices, rotate, background and foreground, resize the
   iPad scene, verify exact Metal drawable dimensions, test a trackpad in a
   nonzero-origin window, and test external-display and safe-area or scale
   transitions.
5. Exercise software-keyboard empty text, Unicode, Cancel, and repeated
   open/close cycles on both devices. On iPad, validate Pencil contact,
   pressure, tilt, simultaneous finger input, cancellation, hover, and
   double-tap.
6. Do not merge the historical `origin/ios` donor branch. Do not ad-hoc sign an
   iPhoneOS handoff; the owner supplies distribution signing and provisioning.
7. Physical-device installation and launch are the next owner-signed release
   gate. Simulator success and an unsigned IPA do not prove that gate.

Current source milestone: scene-owned UIKit startup, drawable-sized and
single-present Metal frames, resizing, windowed coordinate mapping, owned input
and Metal lifetimes, Pencil state safety, touch orbit/zoom/pan, portable CPU
Cycles runtime, and a tier-2-gated Cycles Metal build.
