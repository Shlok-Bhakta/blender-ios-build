# Blender iOS limitations

Simulator Workbench is proven on both iPhone and iPad. Packet P530 installs the
same `org.blenderfoundation.blender.ios` bundle (`UIDeviceFamily` 1 and 2) on an
iPhone 17 simulator and an iPad Pro 13-inch (M5) simulator, both on iOS 26.5.
Splash and cube viewport screenshots exist for each device. iPad runs as
`UIUserInterfaceIdiomPad` (not an iPhone compatibility window). On iPadOS 26,
`UIRequiresFullScreen` no longer forces a full-screen scene; the iPad capture
is a native iPad windowed scene. Physical iPhone and iPad hardware are not
proven.

The reduced profile still keeps target Python, Cycles, OSL, USD, OpenVDB, and
optional media services out of the critical path. Those features are enabled
one at a time under a named smoke test.

The unsigned device output is a future handoff format. It cannot run on a
physical iPhone or iPad before owner-controlled signing and provisioning. This
lane does not inspect identities, profiles, or sign an `iphoneos` bundle.
