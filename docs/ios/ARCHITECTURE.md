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
| Resources/Python | Bundle paths, startup data, interpreter/modules | `bpy.app.version` marker |
| Files | Sandbox paths and document access | Simulator-container round trip |

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
