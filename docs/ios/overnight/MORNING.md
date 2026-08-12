# Overnight handoff — 2026-08-12

Universal iPhone+iPad simulator Workbench is green (P530). The same
`Blender.app` launches on iPhone 17 and an iPad simulator. Next bounded work
is target Python (P117) or an unsigned device handoff. Physical devices remain
unsigned and deferred.

## Green outcomes

- The frozen v5.2.0 baseline and read-only donor refs remain intact.
- Reduced Blender Workbench splash and cube viewport are proven on iPhone 17 /
  iOS 26.5 (P510, P520).
- Packet P530 adds `UIDeviceFamily` 1,2 and iPad orientations to the product
  Info.plist. One bundle id: `org.blenderfoundation.blender.ios`.
- The same installed simulator `.app` runs on iPhone 17 and iPad as a native
  iPad app, not an iPhone compatibility window.
- Target Python, Cycles, USD, and physical-device signing are still out of
  the critical path.

## Evidence

- Interactive iPhone viewport:
  `/Volumes/BlenderBuild/blender-ios/artifacts/p520-first-interactive-viewport-result.json`
- Universal simulator result:
  `/Volumes/BlenderBuild/blender-ios/artifacts/p530-universal-simulator-result.json`
- Screenshots:
  `/Volumes/BlenderBuild/blender-ios/artifacts/p530-iphone-splash.png`
  `/Volumes/BlenderBuild/blender-ios/artifacts/p530-iphone-viewport.png`
  `/Volumes/BlenderBuild/blender-ios/artifacts/p530-ipad-splash.png`
  `/Volumes/BlenderBuild/blender-ios/artifacts/p530-ipad-viewport.png`

## Resume

1. Read `docs/ios/STATUS.json` and the P530 result above.
2. Do not merge `origin/ios`. Do not sign an `iphoneos` bundle.
3. Next safe packets: P117 (target Python) or unsigned device handoff staging.
   Reuse the existing `ios-simulator-minimal-e4b7` Ninja tree; do not rebuild
   dependencies.

Current source milestone: P530 universal iPhone+iPad simulator bundle.
