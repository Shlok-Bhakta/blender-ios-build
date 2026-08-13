# Blender iOS limitations

Simulator Workbench is proven on both iPhone and iPad. Packet P530 installs the
same `org.blenderfoundation.blender.ios` bundle (`UIDeviceFamily` 1 and 2) on an
iPhone 17 simulator and an iPad Pro 13-inch (M5) simulator, both on iOS 26.5.
The bundle declares a modern launch screen so current full-screen iPhones use
their complete native viewport instead of a legacy compatibility rectangle.
Splash and cube viewport screenshots exist for each simulator. iPad runs as
`UIUserInterfaceIdiomPad` (not an iPhone compatibility window). On iPadOS 26,
`UIRequiresFullScreen` no longer forces a full-screen scene; the iPad capture
is a native iPad windowed scene. Full-screen versus windowed placement on
iPadOS 26 is controlled by the user and operating system.

The arm64 iPhoneOS build, runtime bundle, and universal unsigned IPA are now
proven. The IPA targets iOS 18.0 or newer, declares iPhone and iPad device
families, and passes bundle, dependency ABI, executable ABI, archive integrity,
and embedded-signature audits. Physical iPhone and iPad launch remain unproven
because the artifact intentionally has no owner signing or provisioning.

The reduced profile still keeps target Python, Cycles, OSL, USD, OpenVDB, and
optional media services out of the critical path. Those features are enabled
one at a time under a named smoke test.

The current GHOST backend is functional but incomplete. UIKit/Metal startup,
rendering, touch, basic text input, sandbox paths, and document open hooks are
present. The next hardening work is scene-based lifecycle, dynamic window
resizing, safe-area/scale changes, pointer and keyboard parity, lifecycle and
memory-pressure handling, and device file workflows.

The unsigned device IPA cannot install or run on physical hardware before
owner-controlled signing and provisioning. This lane does not inspect
identities or profiles, and it never signs the `iphoneos` bundle.
