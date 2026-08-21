# Blender iOS port architecture

## Output lanes

The simulator and device products share source and immutable dependency
manifests, but never share build directories.

- **Simulator lane:** arm64 iOS Simulator, locally runnable, toolchain-required
  local/ad-hoc signing permitted. iPhone and iPad share this one product
  (`UIDeviceFamily` 1,2; bundle id `org.blenderfoundation.blender.ios`).
- **Device handoff lane:** arm64 iOS, packaged as one universal iPhone+iPad IPA
  without team, identity, profile, signer entitlements, `_CodeSignature`, or
  embedded Mach-O signature. It is not runnable until the owner signs it later.
  Simulator and device build directories remain split.

## Layer boundaries

| Layer | Responsibility | First proof |
| --- | --- | --- |
| Environment | Pinned refs, SDK, storage, resource limits | Doctor report |
| Dependency builder | Cross-compiled immutable installs and host-tool split | Per-library ABI audit |
| CMake/Xcode | SDK, triple, deployment target, feature and signing modes | Configure contract |
| UIKit lifecycle | Scene/view ownership and lifecycle transitions | Ordered boot markers |
| GHOST | System, window, context, events and coordinates | Compile tests, then event loop |
| GPU/Metal | Drawable, submission, framebuffer and memory behavior | Clear frame, then Workbench cube |
| Input/UI | Pure translation plus WM/keymap integration | Host unit tests, then injected input |
| Resources/Python | Bundle paths, startup data, interpreter/modules | `bpy.app.version` and NumPy runtime markers |
| Files | Sandbox paths and document access | Simulator-container round trip |

## Python native-code packaging

The iOS product embeds `Python.framework` and stores pure Python under
`Assets/5.2/python`. CPython and third-party extension modules cannot remain as
loose `.so` files in that resource tree. The install pass moves each extension
to a uniquely named framework under `Blender.app/Frameworks`, leaves a `.fwork`
import marker at the original module path, and records the reverse mapping in
the framework. This makes every executable image independently signable while
preserving normal Python import names.

Physical-device and simulator extensions are always built separately. A shared,
disposable native virtual environment supplies pinned build frontends while
target CPython sysconfig data and SDK-pinned compiler/linker wrappers expose the
selected iOS ABI. NumPy consumes the generated Meson cross file. zstandard uses
the same environment through setuptools and statically absorbs the target zstd
library. Output wheel tags, Mach-O platforms, deployment targets, and Python
framework dependencies are audited before packages are copied into Blender.

CPython does not expose child-process multiprocessing on iOS. Blender services
that use a subprocess only to stay off the UI thread must provide an iOS worker
transport behind the same queue/report interface. The Extensions and remote
asset-library downloader uses a bidirectional in-process channel and daemon
thread on iOS; desktop platforms retain the spawn-based process context.

## Cycles render boundary

The first production Cycles lane is the portable CPU renderer backed by a
static arm64 iOS oneTBB archive. Simulator and device profiles enable the same
feature set. They deliberately keep the Cycles Metal device, Embree, OSL, path
guiding, and the TBB malloc proxy off until each has an independent build and
runtime proof. Blender's Metal viewport remains enabled; it is a separate
backend from the Cycles Metal render device.

iOS arm64 builds do not run host-default x86 feature probes or inject SSE/AVX
flags. Native half conversion includes the arm64 NEON declarations directly,
while the initial CPU kernel remains the portable correctness baseline. An
opt-in post-startup acceptance path waits until the desktop Cycles add-on is
registered, discovers a CPU device, renders the startup scene at one sample,
writes and validates an 8 by 8 PNG in the application sandbox, removes it, and
restores the scene settings.

## Boot observability

Runtime progress is an ordered stream:

```text
process -> app_delegate -> scene_connected -> ghost_system -> window_created
-> metal_context -> blender_main -> first_frame -> event_loop
```

The runner records the last stage, stage latency, process exit, crash path, and
bounded console tail. Configure, build, bundle, and launch logs remain separate.

## Donor policy

`origin/ios` is a behavioral specification and patch library, not a merge
parent. Dependency-builder changes are transplanted mechanically after the
generic framework exists. GHOST, UIKit lifecycle, Metal, Python, and signing
seams are reimplemented against v5.2 APIs under targeted tests.
