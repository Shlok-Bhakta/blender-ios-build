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

## ADR-0005: Accept dependency families only after archive-member ABI audit

- Status: accepted
- Date: 2026-08-11

An installed header or a successfully linked library is insufficient evidence
for cross-compilation. Each harvested family receives a manifest with file
checksums, architecture information, and the `LC_BUILD_VERSION` platform for
every object in each static archive. A family is green only when all members are
arm64 `IOSSIMULATOR` and all manifests share one cache key.

Packet N111 proves zlib, bzip2, xz/liblzma, SQLite, libxml2, libdeflate, Brotli,
and OpenSSL under cache key
`1ae9905260312a93e8e7174f3abcf94a6b4cc6b380ecc8f9cf329e0989853788`.
The combined evidence is
`/Volumes/BlenderBuild/blender-ios/artifacts/n111-1ae9-bootstrap-summary.json`.

Packet N112 extends the same acceptance rule to FreeType 2.13.3 and replays all
eight prerequisites under cache key
`0edd9316d7de66d11228410643ad30e3bc52970f61a5b0394c010600f227603e`.
Evidence:
`/Volumes/BlenderBuild/blender-ios/artifacts/n112-0edd-font-bootstrap-summary.json`.

## ADR-0006: Split Meson build-machine generators from iOS target code

- Status: accepted
- Date: 2026-08-11

Meson dependencies receive separate native and cross files. Target C/C++
compilers carry the arm64 simulator triple and SDK; native generators use the
host SDK and local ad-hoc linker signing required to execute arm64 tools from
the external volume. No identity or team is involved. Generic `CFLAGS`,
`CXXFLAGS`, `LDFLAGS`, and `IPHONEOS_DEPLOYMENT_TARGET` are cleared at Meson
setup so they cannot contaminate the native compiler.

This removes false iOS dependency edges from HarfBuzz and FriBidi to target
Python and its site packages. The generated graph falls from 301 to 286 edges.
Packet N113 proves HarfBuzz 10.0.1 and FriBidi 1.0.12, including FreeType,
Brotli, and zlib integration, under cache key
`b0340de3aebc1a84777d6b423050aa638e7d9b428282f844f1b7e95e5ca60591`.
