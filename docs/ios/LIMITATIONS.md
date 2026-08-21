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

CPython 3.13.13, NumPy 2.3.4, zstandard 0.25.0, and portable CPU Cycles are
enabled in both application lanes. Python native extensions are packaged as
signable frameworks. Simulator acceptance exercises Blender's Python API,
common standard-library modules, arrays, linear algebra, zstd
compression/decompression, and the Extensions background worker on iPhone and
iPad. Cycles acceptance discovers a CPU render device and produces a real
one-sample PNG through the registered desktop render engine on both form
factors. iOS does not permit Blender to create child processes, so the standard
Python `multiprocessing.Process` API is unavailable. The Extensions/remote
asset-library downloader preserves its asynchronous queue, cancellation, and
reporting behavior with a worker thread. The Cycles Metal render device now
compiles and links in both profiles and is exposed only on tier-2
argument-buffer GPUs. The iOS Simulator's tier-1 Metal device cannot compile
the roughly 303-resource Cycles bindless pipelines and is intentionally hidden;
the unsigned iPhoneOS app still needs an owner-signed physical-device Metal
render before that backend is accepted for daily work. CPU remains the proven
fallback. Embree, OSL, path guiding, USD, OpenVDB, and optional media services
remain separate hardening slices.

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
