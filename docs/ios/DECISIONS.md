# Blender iOS decisions

## ADR-0001: Freeze v5.2.0 and use a release-relative donor delta

- Status: accepted
- Date: 2026-08-10

Production work begins at `v5.2.0` (`fbe6228777e7d9af...`). The official iOS
branch remains read-only at `a1de44dd54af...`. Its reliable donor definition is
the exact `v5.1.2..origin/ios` delta (213 files), because the donor tip contains
a large release tree refresh. The port branch never merges `origin/ios`.

## ADR-0002: Split internal control from external bulk data

- Status: accepted
- Date: 2026-08-10

Git source/worktrees and small control files stay internal. Downloads, dependency
and Blender build trees, installs, temporary compiler data, large logs, and
artifacts live under `/Volumes/BlenderBuild/blender-ios`. The expected APFS
volume UUID is `EC4DA5DD-B2A4-4056-934E-5B703096BEF1`. Missing, read-only, or
changed media stops work.

## ADR-0003: Keep simulator and unsigned-device truth claims separate

- Status: accepted
- Date: 2026-08-10

The simulator artifact may use a local/ad-hoc signature if Xcode requires one.
The device handoff must contain no developer identity, team, provisioning
profile, signer entitlements, or bundle signature.

Packet N040 proved the following Xcode 26.5 build overrides with a minimal UIKit
app for both SDKs:

```text
CODE_SIGNING_ALLOWED=NO
CODE_SIGNING_REQUIRED=NO
CODE_SIGN_STYLE=Manual
```

The arm64 simulator executable is linker-signed ad hoc, with no team identifier,
profile, or `_CodeSignature` directory. The arm64 device bundle is reported by
`codesign` as not signed at all and contains neither an embedded profile nor a
`_CodeSignature` directory. Both executables pass the target-platform ABI audit.
Evidence: `/Volumes/BlenderBuild/blender-ios/artifacts/20260811T044431Z-8f74cae544cd-signing-probe/signing-report.json`.

## ADR-0004: Content-address dependency builds by full cross-compile contract

- Status: accepted
- Date: 2026-08-11

Each simulator or device dependency tree gets a distinct SHA-256 cache key over
the frozen Blender release, dependency versions, iOS framework and patch content,
Xcode/SDK/CMake versions, target triple, deployment target, and feature profile.
Build and install prefixes are immutable per key. Downloads and source packages
are shared on the bulk volume, while host executables remain in a separate native
directory and are never taken from the target prefix.

The generic iOS framework uses an explicit SDK path and target triple, arm64,
`CMAKE_SYSTEM_NAME=iOS`, static-library try-compiles, and target-only library,
include, and package discovery. Program discovery remains host-only. The first
simulator configure is green at cache key
`b4566ec98fb7113e621f79f71f83fb3f49f6c2607886c05c0bcf2c1f5b2bddfd`.
