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
profile, signer entitlements, or bundle signature. Exact Xcode settings remain
provisional until packet N040 proves them with a minimal generated app.

