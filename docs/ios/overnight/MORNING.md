# Morning handoff — 2026-08-21

Portable CPU Cycles remains green, and the production simulator and device
profiles compile the native Cycles Metal device. UIKit now owns the app through
a single window scene with scene-relative geometry and drawable resize events.
Screen/client conversion now maps through that scene while preserving GHOST's
native-pixel coordinate contract.
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
- All 63 tests under `build_files/ios/tests` pass.

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
- iPad acceptance recording:
  `/Volumes/BlenderBuild/blender-ios/artifacts/20260821-scene-lifecycle/Blender-iPad-scene-lifecycle.mp4`

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
   iPad scene, test a trackpad in a nonzero-origin window, and test
   external-display and safe-area or scale transitions.
5. Do not merge the historical `origin/ios` donor branch. Do not ad-hoc sign an
   iPhoneOS handoff; the owner supplies distribution signing and provisioning.
6. Physical-device installation and launch are the next owner-signed release
   gate. Simulator success and an unsigned IPA do not prove that gate.

Current source milestone: scene-owned UIKit startup, resizing, and windowed
coordinate mapping plus portable CPU Cycles runtime and a tier-2-gated Cycles
Metal build.
