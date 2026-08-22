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

## UIKit scene and window ownership

The bundle declares one `UIWindowScene` because Blender currently has one
process-wide GHOST system and one desktop session. `IOSSceneDelegate` starts
Blender from `scene:willConnectToSession:options:`, owns foreground activation
events, and receives scene-routed document URLs. The app delegate retains
process-wide security-scoped document handles and releases them at termination.

Every GHOST window uses `initWithWindowScene:` against that active scene.
Initial geometry comes from the scene coordinate space, and display dimensions,
pixel bounds, input scale, drawable scale, and refresh rate come from the
scene's screen. No production GHOST path reads `UIScreen.mainScreen`. MetalKit
drawable-size callbacks call the normal GHOST window-size handler, which
updates Blender's drawing context before queuing the resize event.

The Metal overlay framebuffer is sized from `MTKView.drawableSize`, which is
already expressed in native pixels for the current window and display. A
temporary zero-sized drawable during scene deactivation or live resize keeps
the last valid backing texture until UIKit publishes a drawable again.
Contexts without a UIKit window use a neutral 1 by 1 view; they never guess a
particular iPhone resolution.

Each `drawInMTKView` delegate callback opens exactly one presentation frame.
Blender may request several swaps while processing that callback, but the
window stores one pending-present bit and submits only the newest overlay at
the callback boundary. The context independently guards against more than one
drawable submission in the same frame. Presentation state belongs to the
context; it never depends on a process-global or unretained drawable pointer.

GHOST keeps its public coordinate contract in native pixels. UIKit conversion
APIs use points, so the iOS window divides by the attached scene screen's scale,
converts through `UIWindowScene.coordinateSpace`, and rounds the result back to
native pixels. UIKit and GHOST both use a top-left origin on iOS, so this path
does not inherit AppKit's Y-axis inversion. Cached pointer locations remain in
client coordinates; cursor polling converts them back to scene screen
coordinates. Programmatic cursor updates perform the inverse conversion before
emitting a client-space event. UIKit cannot warp the physical system pointer.

The UIKit input window uses manual Objective-C reference counting. It owns each
gesture recognizer, Pencil interaction, text field, toolbar item, and saved
cancel string that it allocates. `invalidateInput` detaches targets and
delegates before the C++ GHOST window releases UIKit. It also disables edit-end
callbacks before resigning the text field. Keyboard results live in an owned
`std::string`; a pointer returned by `NSString.UTF8String` is copied before the
field changes or releases its string. Empty edits therefore return a stable
empty C string instead of a dangling pointer or `nullptr`.

## Cycles render boundary

The accepted Cycles fallback is the portable CPU renderer backed by a static
arm64 iOS oneTBB archive. Simulator and device profiles also compile the native
Cycles Metal device from the target SDK. iOS enumeration admits only tier-2
argument-buffer GPUs because the Cycles bindless kernel exceeds tier-1 resource
limits. The iOS Simulator exposes a tier-1 pseudo-GPU capped at 31 buffers, so
it is intentionally hidden and CPU acceptance remains authoritative there.
The unsigned physical-device build contains the tier-2 Metal path, but a signed
real-device render is still required before Metal becomes an accepted runtime
lane. Embree, OSL, path guiding, and the TBB malloc proxy remain off. Blender's
Metal viewport is a separate backend and remains enabled.

iOS arm64 builds do not run host-default x86 feature probes or inject SSE/AVX
flags. Native half conversion includes the arm64 NEON declarations directly,
while the initial CPU kernel remains the portable correctness baseline. An
opt-in post-startup acceptance path waits until the desktop Cycles add-on is
registered, selects either CPU or Metal, renders the startup scene at one
sample, writes and validates an 8 by 8 PNG in the application sandbox, removes
it, and restores the scene and device-preference settings. Current simulator
evidence exercises CPU; `BLENDER_IOS_CYCLES_SMOKE=METAL` is reserved for a
tier-2 physical device.

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
