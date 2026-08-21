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

CPython 3.13.13 and NumPy 2.3.4 are enabled in both application lanes. Their
native extensions are packaged as signable frameworks, and the simulator smoke
test exercises Blender's Python API, common standard-library modules, arrays,
and linear algebra on iPhone and iPad. The standard-library `_multiprocessing`
extension is not yet present, so the Extensions/remote asset-library add-on
reports an import error during registration. Cycles, OSL, USD, OpenVDB, Python
zstandard, and optional media services remain outside the reduced profile and
are being enabled one at a time under named smoke tests.

The current GHOST backend supports UIKit/Metal startup, rendering, touch,
Pencil, mouse/trackpad buttons and motion, hardware-keyboard HID translation,
modifier polling, activation events, sandbox paths, and security-scoped Blender
documents. UIKit still reports that scene-based lifecycle will become mandatory
in a future SDK. Dynamic window resizing, safe-area/scale changes,
memory-pressure handling, and broader document workflows still require device
hardening.

The unsigned device IPA cannot install or run on physical hardware before
owner-controlled signing and provisioning. This lane does not inspect
identities or profiles, and it never signs the `iphoneos` bundle.
