# Blender 5.2 iOS port handoff

This branch ports the official Blender iOS work onto the immutable Blender
`v5.2.0` release. The simulator product reaches a responsive Workbench frame on
iPhone and iPad, embeds CPython and its accepted native packages, and renders
with portable CPU Cycles. The device product builds as arm64 iPhoneOS and is
handed off as one universal unsigned IPA; owner signing, provisioning, and
physical-device launch remain outside this repository.

## Ten-minute resume

1. Read `STATUS.json`, the newest entry in `DECISIONS.md`, and
   `overnight/MORNING.md` when it exists.
2. Confirm the worktree is clean and pinned correctly:

   ```sh
   git status --short --branch
   git rev-parse HEAD v5.2.0 a1de44dd54af75a4c8c4a29a5fed2a1334a87446
   ```

3. Run the environment doctor before any build:

   ```sh
   python3 build_files/ios/doctor.py --output /Volumes/BlenderBuild/blender-ios/artifacts/manual-doctor/env.json
   ```

4. Inspect the last-green artifact named by `STATUS.json`, then re-run the
   active packet's narrow test before editing.
5. Claim only a packet in `next_safe_packets`. Update the ledger before code if
   recorded state and the checkout disagree.

The generated dependency graph is `DEPENDENCY_DAG.json`. Its bootstrap queue is
dependency-free and ordered for bounded `-j2` packets; do not replace it with the
global `install` target.

## Immutable anchors

- Production baseline: `v5.2.0` / `fbe6228777e7d9afefcd61a413844e790ae75db7`
- Read-only donor: `a1de44dd54af75a4c8c4a29a5fed2a1334a87446`
- Donor comparison: `v5.1.2..a1de44dd54af75a4c8c4a29a5fed2a1334a87446`
- Integration branch: `port/ios-5.2-simulator`

Do not merge the donor branch. Adapt one subsystem at a time and record donor
paths in each packet handoff.

## Storage contract

Source, Git metadata, control scripts, documentation, and small fixtures remain
on the internal SSD. All downloads, dependency builds/installs, Blender build
trees, large logs, artifacts, and task temporary directories belong below
`/Volumes/BlenderBuild/blender-ios`. A missing or changed bulk volume is a hard
stop; never fall back to an internal path.

## Safety boundary

Administrative or host-wide changes require explicit operator authorization;
that authorization was granted for this dedicated build Mac. The N100/N111
bootstrap installed `autoconf`, `automake`, `bison`, `dos2unix`, `flex`,
`libtool`, `meson`, `pkgconf`, and `yasm` with Homebrew, without `sudo`.
Credentials must never be written to source, logs, or artifacts.

No build packet may inspect signing identities or profiles, sign a device
bundle, rewrite history, or broaden its allowed files. Stop after two
unsuccessful architectural approaches and preserve the evidence.

## Unsigned device IPA

The production device lane uses `blender_ios_device.cmake`, an `iphoneos`
sysroot, an arm64-only dependency prefix, and a build directory separate from
the simulator. The `_minimal` profile remains a narrow diagnostic lane and is
not the release handoff. After `ninja install`, create the artifact with:

```sh
python3 build_files/ios/package_unsigned_ipa.py \
  /path/to/bin/Blender.app \
  /path/to/Blender-5.2.0-iPhone-iPad-unsigned.ipa
```

The packager rejects simulator binaries, the wrong bundle id or device-family
metadata, provisioning/signing files, signing plist keys, and embedded Mach-O
signatures. The owner must sign and provision the IPA before installing it.

## Recommended next order

1. Sign the current IPA and run a physical iPhone/iPad smoke test for launch,
   touch, rotation, background/foreground, save/open, and memory pressure.
2. Finish GHOST/UIKit hardening: run physical rotation, resize, safe-area, and
   external-display acceptance against the scene-owned window. Verify the new
   scene-space pointer mapping with a physical trackpad in a nonzero-origin
   iPad window. Exercise software-keyboard empty text, Unicode, Cancel, and
   repeated open/close cycles, then close Pencil, memory-pressure, and
   file-workflow gaps.
3. Owner-sign the P540-capable device IPA and run
   `BLENDER_IOS_CYCLES_SMOKE=METAL` on tier-2 iPhone and iPad hardware. Keep
   portable CPU Cycles as the accepted fallback until both renders pass.
4. Add optional dependency families individually under simulator, device ABI,
   and physical-device smoke tests. Prioritize Apple Accelerate for NumPy,
   then Embree, OSL, USD, OpenVDB, and media integrations.
5. Keep `makesrna.features` synchronized with each target profile when a
   feature changes generated RNA. Rebuild host tools before diagnosing target
   code when the manifest rejects a configure.
