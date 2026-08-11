# Overnight handoff — 2026-08-11

The branch is at packet N113 green. The next bounded packet is N114 (image-codec
dependencies). No Blender application frame or first pixel is claimed yet.

## Green outcomes

- Frozen baseline and read-only donor refs are intact.
- The exact 213-file donor delta remains classified.
- Simulator-local and unsigned-device signing lanes are independently proven.
- The content-addressed iOS dependency framework configured successfully.
- Eight bootstrap families built and passed member-by-member arm64
  `IOSSIMULATOR` audit under one cache key: zlib, bzip2, xz/liblzma, SQLite,
  libxml2, libdeflate, Brotli, and OpenSSL.
- FreeType 2.13.3 built on those roots and passed the same archive-member audit;
  all nine families were replayed under one immutable N112 cache key.
- HarfBuzz 10.0.1 and FriBidi 1.0.12 build through explicit Meson native/cross
  files. Their five-family stack passes the simulator archive audit, and their
  false target-Python dependency edges are gone.
- The environment doctor is green, including AC power, SDK, external volume
  UUID/writeability/free space, host tools, and pinned Git refs.
- All 20 iOS control-plane unit tests and the 213/213 donor-map audit pass.

## Preserved red evidence

- The first zlib attempt tried to link upstream example executables with hidden
  library symbols. The iOS recipe now disables examples. Log:
  `/Volumes/BlenderBuild/blender-ios/artifacts/n111-zlib-build.log`.
- SQLite 3.51 initially could not discover its cross C compiler. The recipe now
  exports the CMake-selected compiler explicitly. Log:
  `/Volumes/BlenderBuild/blender-ios/artifacts/n111-434d-sqlite-build.log`.
- Brotli 1.0.9 has an always-successful Emscripten probe and therefore omits its
  install target during cross-compilation. The iOS lane performs a narrow static
  archive/header install. Failed logs are retained under the `cf72`, `63a7`, and
  `8501` N111 artifact prefixes.
- FriBidi initially exposed native-generator contamination and then the
  Apple-Silicon local-signing requirement. Failed setup logs remain under the
  `3944`, `b1fa`, and `1bff` N113 build prefixes; the successful correction is
  the `b034` generation.

## Resume

1. Read `docs/ios/STATUS.json` and
   `/Volumes/BlenderBuild/blender-ios/artifacts/n111-1ae9-bootstrap-summary.json`.
2. Run `python3 build_files/ios/doctor.py --output /Volumes/BlenderBuild/blender-ios/artifacts/manual-doctor/env.json`.
3. Start N114 with the image-codec roots from `DEPENDENCY_DAG.json`; keep prior
   green prefixes immutable and builds at `--parallel 2`.

Current cache key:
`b0340de3aebc1a84777d6b423050aa638e7d9b428282f844f1b7e95e5ca60591`.
