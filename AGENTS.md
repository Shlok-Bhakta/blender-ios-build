# AGENTS.md

## Goal

- establish a repeatable `ios-simulator` runtime validation loop for GHOST/windowing
- get one iOS window + Metal context + first frame/present working
- stop at first reliable windowing smoke; do not chase later touch/IME/document issues yet
- produce an unsigned iOS `.ipa` artifact that the user can sideload with SideStore

## Rules

- use current macOS GHOST + Metal code as the primary source of truth
- use old iOS patches as reference only; do not port them wholesale
- validation first, then implementation
- prefer the smallest working vertical slice
- local simulator smoke first, then CI/runtime automation
- for this user setup, GitHub Actions is the primary executable validation path because the user does not own a Mac
- keep the remote Actions loop running: trigger workflow, poll status, inspect logs, make the next fix, rerun
- do not batch speculative fixes
- defer touch, gestures, Apple Pencil, IME, document browser, sandbox file access, and multi-window work until first frame is stable
- use subagents often
- if user says pause polling, pause polling

## Base Files

Primary implementation base:

- `intern/ghost/intern/GHOST_ISystem.cc`
- `intern/ghost/intern/GHOST_SystemCocoa.hh`
- `intern/ghost/intern/GHOST_SystemCocoa.mm`
- `intern/ghost/intern/GHOST_WindowCocoa.hh`
- `intern/ghost/intern/GHOST_WindowCocoa.mm`
- `intern/ghost/intern/GHOST_WindowViewCocoa.hh`
- `intern/ghost/intern/GHOST_ContextMTL.hh`
- `intern/ghost/intern/GHOST_ContextMTL.mm`

Reference only when needed:

- `port-patches/todo/intern/ghost/intern/GHOST_SystemIOS.mm.patch`
- `port-patches/todo/intern/ghost/intern/GHOST_WindowIOS.mm.patch`
- `port-patches/todo/intern/ghost/intern/GHOST_ContextIOS.mm.patch`
- `port-patches/todo/source/creator/creator.cc.patch`
- `port-patches/todo/source/blender/windowmanager/intern/wm.cc.patch`
- `port-patches/todo/source/blender/gpu/metal/*.patch`

## Reality Check

- old iOS GHOST work was a separate UIKit backend, not a small Cocoa diff
- current Blender still selects Cocoa on Apple in `GHOST_ISystem.cc`
- current Blender main loop still expects normal GHOST event pumping via `wm_window_events_process()`
- Metal backend also has macOS-only assumptions outside GHOST
- first blocker is likely a combination of minimal iOS GHOST backend plus minimal Metal compatibility fixes

## Validation Ladder

1. app compile for `ios-simulator`
2. bundle integrity check
3. simulator install + launch smoke
4. prove process stays alive briefly and logs startup markers
5. prove one window/view/context path and first present
6. app compile for `ios` device
7. package unsigned `.ipa`
8. upload Actions artifact and verify the artifact is usable for SideStore re-signing

Do not move on to input/features before step 5 is green.

## First Slice

1. select an iOS GHOST backend under `WITH_APPLE_CROSSPLATFORM`
2. add minimal `GHOST_SystemIOS`
3. add minimal `GHOST_WindowIOS`
4. add minimal `GHOST_ContextIOS`
5. make only the smallest Metal backend changes needed to accept iOS/simulator
6. only split the app main loop if runtime evidence shows it is required

Scope for first slice:

- one fullscreen window
- one `UIWindow` / view-controller / `MTKView` path
- window activate + size/update events
- Metal drawable acquisition and present

Explicitly out of scope for first slice:

- touch events
- multi-finger taps/gestures
- Apple Pencil
- on-screen keyboard
- security-scoped file access
- drag and drop
- cursor special cases
- multi-window behavior

## Loop

1. inspect current local state and the smallest missing validation step
2. identify the first real runtime blocker
3. make the smallest fix
4. verify with the local simulator smoke loop
5. when local validation is unavailable or insufficient, trigger the GitHub Actions IPA workflow
6. poll the workflow until completion or failure
7. inspect the failing step and logs, then make the smallest fix
8. rerun immediately and repeat until an unsigned IPA artifact exists or a hard external blocker is proven

## Heuristics

- prefer adapting Cocoa code over translating old iOS patch text
- keep the first backend thin and boring
- if a change requires new GHOST event types, stop and ask whether it is really needed for first-frame bring-up
- if a problem can be deferred by stubbing unsupported iOS behavior for now, defer it
- when Metal code assumes macOS-only features, prefer the smallest guarded fallback
- behavior match matters more than patch text match

## Current State

Findings from GHOST analysis:

- best adaptation base is Cocoa window/system/context code
- old iOS patch also changed creator bootstrap and WM main-loop structure
- current runtime validation in GitHub Actions only covers deps/tooling, not simulator app launch
- first meaningful progress requires a simulator smoke loop before deeper GHOST work
- the user can only practically test on a real device via SideStore, so unsigned IPA production in Actions is mandatory
- likely downstream files after initial GHOST backend exist include:
  - `source/blender/gpu/metal/mtl_common.hh`
  - `source/blender/gpu/metal/mtl_context.hh`
  - `source/blender/gpu/metal/mtl_context.mm`
  - `source/blender/gpu/metal/mtl_command_buffer.mm`
  - `source/blender/gpu/metal/mtl_backend.mm`

Current delivery expectation:

- do not stop after adding packaging code locally
- always try to run the relevant GitHub Actions workflow after material iOS packaging/build changes
- actively poll workflow state and continue debugging failures in a loop
- only stop the loop when the user pauses it or an unsigned IPA artifact has been produced

## First Step

1. define the local simulator smoke command loop
2. implement backend selection for iOS under `WITH_APPLE_CROSSPLATFORM`
3. stub the minimal iOS GHOST system/window/context types
4. get compile errors down to the first real runtime path blocker
