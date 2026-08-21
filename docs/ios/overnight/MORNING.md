# Morning handoff — 2026-08-21

Portable CPU Cycles remains green, and the production simulator and device
profiles now compile the native Cycles Metal device. The same simulator
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
- All 56 tests under `build_files/ios/tests` pass.

## Evidence

- Simulator build:
  `/Volumes/BlenderBuild/blender-ios/build/ios-simulator-python-e7de/bin/Blender.app`
- Unsigned-device build:
  `/Volumes/BlenderBuild/blender-ios/build/ios-device-python-5353b/bin/Blender.app`
- Unsigned IPA:
  `/Volumes/BlenderBuild/blender-ios/artifacts/20260821-cycles-metal-foundation/Blender-5.2.0-Python-NumPy-Zstandard-Cycles-CPU-Metal-capable-iPhone-iPad-unsigned.ipa`
- IPA SHA-256:
  `acb3bf5bdbf04fa6d399756a69c2e06ef5f8b4c243b53138bdd9efc9a0782851`

## Resume

1. Read `docs/ios/HANDOFF.md`, `docs/ios/LIMITATIONS.md`, ADR-0017, and this
   file before changing a feature profile.
2. Use `blender_ios_sim.cmake` and `blender_ios_device.cmake` as the production
   profiles. Keep their Cycles settings synchronized and rebuild host tools
   whenever the generated-feature manifest changes.
3. Owner-sign the Metal-capable IPA and run
   `BLENDER_IOS_CYCLES_SMOKE=METAL` on tier-2 iPhone and iPad hardware. Preserve
   portable CPU Cycles as the fallback until both physical renders pass.
4. Do not merge the historical `origin/ios` donor branch. Do not ad-hoc sign an
   iPhoneOS handoff; the owner supplies distribution signing and provisioning.
5. Physical-device installation and launch are the next owner-signed release
   gate. Simulator success and an unsigned IPA do not prove that gate.

Current source milestone: portable CPU Cycles runtime plus a tier-2-gated
Cycles Metal build for iPhone and iPad profiles.
