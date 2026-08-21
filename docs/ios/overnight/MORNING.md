# Morning handoff — 2026-08-21

Portable CPU Cycles is green in the production simulator and unsigned-device
profiles. The same simulator `Blender.app` runs the desktop UI on iPhone and
iPad, imports CPython 3.13.13, NumPy 2.3.4, and zstandard 0.25.0, starts the
thread-backed Extensions worker, and completes a real one-sample Cycles render.
The iPhoneOS product builds and packages as one universal unsigned IPA for
device families 1 and 2.

## Green outcomes

- Simulator and device builds enable Cycles CPU and oneTBB with identical
  feature settings.
- The optional Cycles Metal device, Embree, OSL, path guiding, and TBB malloc
  proxy remain explicitly disabled pending independent acceptance slices.
- iPhone 17 Pro and iPad Pro 13-inch (M5) simulator launches emit
  `BLENDER_IOS_CYCLES_READY=cpu-render` after producing and validating an 8 by
  8 PNG through Blender's registered Cycles engine.
- The final arm64 iPhoneOS build completes 3,628 actions and a clean incremental
  install. App and oneTBB inputs pass recursive target ABI audits.
- The unsigned IPA contains 74 frameworks and no loose `.so` or `.a` files.
  Bundle policy, private-path, archive-integrity, and packaging checks pass.
- All 55 tests under `build_files/ios/tests` pass.

## Evidence

- Simulator build:
  `/Volumes/BlenderBuild/blender-ios/build/ios-simulator-python-e7de/bin/Blender.app`
- Unsigned-device build:
  `/Volumes/BlenderBuild/blender-ios/build/ios-device-python-5353b/bin/Blender.app`
- Unsigned IPA:
  `/Volumes/BlenderBuild/blender-ios/artifacts/20260821-cycles-cpu/Blender-5.2.0-Python-NumPy-Zstandard-Cycles-CPU-iPhone-iPad-unsigned.ipa`
- IPA SHA-256:
  `13520e6fea4259c196e62e281309a3b6a5136e63422427daebaffbff07eef071`

## Resume

1. Read `docs/ios/HANDOFF.md`, `docs/ios/LIMITATIONS.md`, ADR-0017, and this
   file before changing a feature profile.
2. Use `blender_ios_sim.cmake` and `blender_ios_device.cmake` as the production
   profiles. Keep their Cycles settings synchronized and rebuild host tools
   whenever the generated-feature manifest changes.
3. Take Cycles Metal as a separate feasibility slice with its own build, ABI,
   and real-render proof. Preserve portable CPU Cycles as the fallback.
4. Do not merge the historical `origin/ios` donor branch. Do not ad-hoc sign an
   iPhoneOS handoff; the owner supplies distribution signing and provisioning.
5. Physical-device installation and launch are the next owner-signed release
   gate. Simulator success and an unsigned IPA do not prove that gate.

Current source milestone: portable CPU Cycles on iPhone and iPad profiles.
