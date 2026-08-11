# Overnight handoff — 2026-08-11

First pixel is green. The next bounded packet is N210: integrate the proven
UIKit/Metal shell with Blender's GHOST system, window, and context.

## Green outcomes

- The frozen v5.2.0 baseline and read-only donor refs remain intact.
- The N116 first-pixel dependency closure contains 1,181 harvested files under
  cache key `e4b775f99fd0d6b27a0ec7bc6425dd9923357c59b1020567af077ec135b09957`.
  Every binary is arm64 `IOSSIMULATOR`.
- OpenColorIO and OpenImageIO build statically without target Python, desktop
  monitor frameworks, tools, TBB, or libheif.
- Blender's reduced iOS graph configures against the audited sysroot with Xcode
  26.5 and the iOS 26.5 simulator SDK.
- Revision-matched native `makesdna`, `makesrna`, `datatoc`, and `shader_tool`
  executables generate target sources successfully.
- The reduced Blender compile passes generated shaders, DNA, RNA, and core
  libraries through action 3,906. Its next failure is the expected Cocoa GHOST
  include, not a dependency or target-ABI error.
- The repository-native UIKit/Metal shell installs and launches on the booted
  iPhone 17 simulator. Runtime evidence records `boot`, the Apple iOS simulator
  GPU, and `first_frame` after command-buffer completion.
- The captured 1206×2622 screenshot visibly shows the Metal-cleared frame and
  “BLENDER iOS” overlay.
- All 20 iOS control-plane unit tests pass.

## Evidence

- Dependency audit:
  `/Volumes/BlenderBuild/blender-ios/artifacts/n116-e4b7-first-pixel-closure-manifest.json`
- Reduced configure:
  `/Volumes/BlenderBuild/blender-ios/artifacts/n150-e4b7-blender-configure.log`
- Reduced compile boundary:
  `/Volumes/BlenderBuild/blender-ios/artifacts/n150-e4b7-blender-build.log`
- First-pixel result:
  `/Volumes/BlenderBuild/blender-ios/artifacts/p500-first-pixel-result.json`
- Screenshot:
  `/Volumes/BlenderBuild/blender-ios/artifacts/p500-first-pixel.png`

## Resume

1. Read `docs/ios/STATUS.json` and the P500 result above.
2. Keep the first-pixel shell runnable while adapting only the donor's iOS GHOST
   system/window/context surface to the v5.2.0 interfaces.
3. Reconfigure and resume the existing `ios-simulator-minimal-e4b7` Ninja tree
   at `--parallel 2`; the known boundary is `GHOST_SystemCocoa.mm` including
   unavailable `Cocoa/Cocoa.h`.

Current source milestone: `36f78477019578c8d608229671bb43654caef31c`.
