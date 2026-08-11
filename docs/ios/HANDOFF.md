# Blender 5.2 iOS port handoff

This branch ports the official Blender iOS work onto the immutable Blender
`v5.2.0` release. The first product milestone is an arm64 iOS Simulator build
that reaches a responsive Workbench frame. Physical-device installation and
owner signing are deliberately deferred.

## Ten-minute resume

1. Read `STATUS.json`, the newest entry in `DECISIONS.md`, and
   `overnight/MORNING.md` when it exists.
2. Confirm the worktree is clean and pinned correctly:

   ```sh
   git status --short --branch
   git rev-parse HEAD v5.2.0 origin/ios
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
- Read-only donor: `origin/ios` / `a1de44dd54af75a4c8c4a29a5fed2a1334a87446`
- Donor comparison: `v5.1.2..origin/ios`
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

No packet may inspect signing identities or profiles, sign a device bundle,
merge/rebase/push, rewrite history, or broaden its allowed files. Stop after two
unsuccessful architectural approaches and preserve the evidence.
